import json
import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Collection, Hadith, HadithSharhLink, SharhSection
from app.services.audit_logger import log_audit_event
from app.services.citation_generator import generate_citations
from app.utils.db_helpers import to_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/review", tags=["Tahap 5 Review Dashboard"])


class ReviewActionRequest(BaseModel):
    notes: str | None = Field(default=None, description="Catatan hasil verifikasi peneliti")
    reviewer: str | None = Field(default=None, description="Nama / identitas reviewer")
    reason: str | None = Field(default=None, description="Alasan penolakan (jika reject)")


def _parse_evidence(evidence_raw: str | None) -> dict[str, Any]:
    if not evidence_raw:
        return {}
    try:
        return json.loads(evidence_raw)
    except Exception:
        return {"raw": evidence_raw}


@router.get("/queue")
def get_review_queue(
    status: str = Query(
        default="pending",
        description="Filter status: 'pending' (belum diverifikasi), 'verified' (disetujui), 'rejected' (ditolak), atau 'all'",
    ),
    minimum_confidence: float = Query(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ambang batas confidence minimal (default: 0.0)",
    ),
    maximum_confidence: float = Query(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Ambang batas confidence maksimal (default: 1.0)",
    ),
    volume: int | None = Query(default=None, description="Filter berdasarkan nomor Jilid Fathul Bari"),
    hadith_number: int | None = Query(default=None, description="Filter nomor hadis tertentu"),
    search: str | None = Query(default=None, description="Pencarian kata kunci pada judul syarah atau nomor hadis"),
    sort_by: str = Query(
        default="confidence_desc",
        description="Urutan data: 'confidence_desc', 'confidence_asc', 'hadith_asc', 'volume_page_asc', 'created_desc'",
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Batas jumlah item per halaman"),
    offset: int = Query(default=0, ge=0, description="Offset paginasi"),
    db: Session = Depends(get_db),
):
    """Mengambil antrean kandidat tautan Hadis – Syarah Fathul Bari untuk diverifikasi reviewer."""
    base_stmt = (
        select(HadithSharhLink, Hadith, SharhSection, Collection)
        .join(Hadith, HadithSharhLink.hadith_id == Hadith.id)
        .join(SharhSection, HadithSharhLink.sharh_section_id == SharhSection.id)
        .join(Collection, Hadith.collection_id == Collection.id)
    )

    # Confidence Range Filter
    base_stmt = base_stmt.where(
        HadithSharhLink.confidence >= minimum_confidence,
        HadithSharhLink.confidence <= maximum_confidence,
    )

    # Status Filter
    status_lower = status.lower().strip()
    if status_lower == "pending":
        base_stmt = base_stmt.where(
            HadithSharhLink.verified == False,
            HadithSharhLink.review_status.in_(["pending", "review", "auto_candidate", "weak_match"]),
        )
    elif status_lower == "verified":
        base_stmt = base_stmt.where(
            (HadithSharhLink.verified == True) | (HadithSharhLink.review_status == "verified")
        )
    elif status_lower == "rejected":
        base_stmt = base_stmt.where(HadithSharhLink.review_status == "rejected")
    elif status_lower == "all":
        pass  # No status filter
    else:
        # Custom review status filter
        base_stmt = base_stmt.where(HadithSharhLink.review_status == status_lower)

    # Volume filter
    if volume is not None:
        base_stmt = base_stmt.where(SharhSection.volume == volume)

    # Hadith number filter
    if hadith_number is not None:
        base_stmt = base_stmt.where(Hadith.external_number == hadith_number)

    # Search keyword
    if search:
        s_pattern = f"%{search.strip()}%"
        if search.strip().isdigit():
            base_stmt = base_stmt.where(
                (Hadith.external_number == int(search.strip()))
                | (SharhSection.title.ilike(s_pattern))
                | (SharhSection.arabic_text.ilike(s_pattern))
            )
        else:
            base_stmt = base_stmt.where(
                (SharhSection.title.ilike(s_pattern))
                | (SharhSection.arabic_text.ilike(s_pattern))
                | (Hadith.arabic_text.ilike(s_pattern))
                | (Hadith.translation.ilike(s_pattern))
                | (HadithSharhLink.notes.ilike(s_pattern))
            )

    # Sorting
    if sort_by == "confidence_asc":
        base_stmt = base_stmt.order_by(HadithSharhLink.confidence.asc())
    elif sort_by == "hadith_asc":
        base_stmt = base_stmt.order_by(Hadith.external_number.asc(), HadithSharhLink.confidence.desc())
    elif sort_by == "volume_page_asc":
        base_stmt = base_stmt.order_by(
            SharhSection.volume.asc(),
            func.coalesce(SharhSection.printed_page, SharhSection.pdf_page, SharhSection.page).asc(),
        )
    elif sort_by == "created_desc":
        base_stmt = base_stmt.order_by(HadithSharhLink.created_at.desc())
    else:  # default confidence_desc
        base_stmt = base_stmt.order_by(HadithSharhLink.confidence.desc(), Hadith.external_number.asc())

    # Count matching query
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_matching = int(db.scalar(count_stmt) or 0)

    # Paginate
    paginated_stmt = base_stmt.offset(offset).limit(limit)
    rows = list(db.execute(paginated_stmt).all())

    # Global Queue Statistics
    all_links_stmt = select(HadithSharhLink)
    all_links = list(db.scalars(all_links_stmt))
    total_links = len(all_links)
    pending_count = sum(1 for l in all_links if not l.verified and l.review_status != "rejected")
    verified_count = sum(1 for l in all_links if l.verified or l.review_status == "verified")
    rejected_count = sum(1 for l in all_links if l.review_status == "rejected")
    avg_conf = (
        round(sum(l.confidence or 0.0 for l in all_links) / total_links, 4)
        if total_links > 0
        else 0.0
    )

    items = []
    for link, hadith, sharh, coll in rows:
        evidence_dict = _parse_evidence(link.evidence)
        page_val = sharh.printed_page or sharh.pdf_page or sharh.page

        citations = generate_citations(
            hadith_number=hadith.external_number,
            collection_name=coll.name,
            volume=sharh.volume,
            page=page_val,
            sharh_title=sharh.title,
            hadith_arabic_excerpt=(hadith.arabic_text or "")[:60],
        )

        items.append({
            "link_id": str(link.id),
            "hadith_id": str(hadith.id),
            "hadith_number": hadith.external_number,
            "hadith_arabic_excerpt": (hadith.arabic_text or "")[:120] + ("..." if len(hadith.arabic_text or "") > 120 else ""),
            "hadith_translation_excerpt": (hadith.translation or "")[:150] + ("..." if len(hadith.translation or "") > 150 else ""),
            "collection_slug": coll.slug,
            "collection_name": coll.name,
            "sharh_id": str(sharh.id),
            "sharh_title": sharh.title or f"Syarah Jilid {sharh.volume} Hal. {page_val}",
            "volume": sharh.volume,
            "page": page_val,
            "printed_page": sharh.printed_page,
            "pdf_page": sharh.pdf_page,
            "sharh_arabic_excerpt": (sharh.arabic_text or "")[:140] + ("..." if len(sharh.arabic_text or "") > 140 else ""),
            "sharh_translation_excerpt": (sharh.translation or "")[:160] + ("..." if len(sharh.translation or "") > 160 else "") if sharh.translation else None,
            "match_method": link.match_method,
            "confidence": link.confidence,
            "confidence_percent": round((link.confidence or 0.0) * 100, 2),
            "review_status": link.review_status,
            "verified": link.verified,
            "evidence": evidence_dict,
            "notes": link.notes,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "citation_preview": citations["standard"],
        })

    return {
        "status_filter": status,
        "minimum_confidence": minimum_confidence,
        "maximum_confidence": maximum_confidence,
        "total": total_matching,
        "limit": limit,
        "offset": offset,
        "stats": {
            "total_links": total_links,
            "pending_count": pending_count,
            "verified_count": verified_count,
            "rejected_count": rejected_count,
            "avg_confidence": avg_conf,
            "avg_confidence_percent": round(avg_conf * 100, 2),
            "filtered_matching_count": total_matching,
        },
        "queue": items,
    }


@router.get("/links/{link_id}")
def get_review_link_detail(link_id: str, db: Session = Depends(get_db)):
    """Mengambil detail lengkap satu tautan hadis – syarah beserta teks lengkap, sinyal matching, sitasi ilmiah, dan konteks navigasi."""
    uid = to_uuid(link_id)
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == uid)) if uid else None
    if not link:
        raise HTTPException(status_code=404, detail="Tautan Hadits–Syarah tidak ditemukan.")

    hadith = db.scalar(select(Hadith).where(Hadith.id == link.hadith_id))
    sharh = db.scalar(select(SharhSection).where(SharhSection.id == link.sharh_section_id))
    collection = db.scalar(select(Collection).where(Collection.id == hadith.collection_id)) if hadith else None

    evidence_dict = _parse_evidence(link.evidence)
    page_val = (sharh.printed_page or sharh.pdf_page or sharh.page) if sharh else None

    citations = generate_citations(
        hadith_number=hadith.external_number if hadith else None,
        collection_name=collection.name if collection else "Shahih al-Bukhari",
        volume=sharh.volume if sharh else None,
        page=page_val,
        sharh_title=sharh.title if sharh else None,
        hadith_arabic_excerpt=(hadith.arabic_text or "")[:100] if hadith else "",
    )

    # Temukan prev_link_id & next_link_id untuk keyboard navigation
    all_link_ids = list(
        db.scalars(
            select(HadithSharhLink.id).order_by(HadithSharhLink.confidence.desc())
        )
    )
    current_idx = -1
    for i, lid in enumerate(all_link_ids):
        if str(lid) == str(link.id):
            current_idx = i
            break

    prev_link_id = str(all_link_ids[current_idx - 1]) if current_idx > 0 else None
    next_link_id = str(all_link_ids[current_idx + 1]) if 0 <= current_idx < len(all_link_ids) - 1 else None

    return {
        "link_id": str(link.id),
        "match_method": link.match_method,
        "confidence": link.confidence,
        "confidence_percent": round((link.confidence or 0.0) * 100, 2),
        "review_status": link.review_status,
        "verified": link.verified,
        "evidence": evidence_dict,
        "notes": link.notes,
        "created_at": link.created_at.isoformat() if link.created_at else None,
        "hadith": {
            "id": str(hadith.id) if hadith else None,
            "number": hadith.external_number if hadith else None,
            "collection_slug": collection.slug if collection else None,
            "collection_name": collection.name if collection else "Shahih al-Bukhari",
            "arabic_text": hadith.arabic_text if hadith else None,
            "translation": hadith.translation if hadith else None,
        },
        "sharh": {
            "id": str(sharh.id) if sharh else None,
            "work_slug": sharh.work_slug if sharh else "fathul_bari",
            "work_title": "Fathul Bari Syarah Shahih al-Bukhari",
            "author": "Al-Hafizh Ibnu Hajar al-Asqalani",
            "volume": sharh.volume if sharh else None,
            "printed_page": sharh.printed_page if sharh else None,
            "pdf_page": sharh.pdf_page if sharh else None,
            "page": page_val,
            "section_order": sharh.section_order if sharh else None,
            "title": sharh.title if sharh else None,
            "arabic_text": sharh.arabic_text if sharh else None,
            "translation": sharh.translation if sharh else None,
            "source_file": sharh.source_file if sharh else None,
            "extraction_status": sharh.extraction_status if sharh else None,
        },
        "citations": citations,
        "nav": {
            "prev_link_id": prev_link_id,
            "next_link_id": next_link_id,
            "current_index": current_idx + 1 if current_idx >= 0 else 1,
            "total_items": len(all_link_ids),
        },
    }


@router.post("/links/{link_id}/verify")
def verify_review_link(
    link_id: str,
    req: ReviewActionRequest | None = None,
    x_reviewer: str | None = Header(None, alias="X-Reviewer"),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
):
    """Aksi reviewer untuk memverifikasi dan menyetujui hubungan Hadis – Syarah Fathul Bari."""
    uid = to_uuid(link_id)
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == uid)) if uid else None
    if not link:
        raise HTTPException(status_code=404, detail="Tautan Hadits–Syarah tidak ditemukan.")

    actor_name = (req.reviewer if req and req.reviewer else None) or x_reviewer or "reviewer"

    before_state = {
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "confidence": link.confidence,
    }

    link.verified = True
    link.review_status = "verified"

    notes_parts = []
    if req and req.notes:
        notes_parts.append(req.notes.strip())
    if actor_name:
        notes_parts.append(f"[Verified by: {actor_name.strip()}]")

    if notes_parts:
        link.notes = " • ".join(notes_parts)
    elif not link.notes:
        link.notes = "Diverifikasi & disetujui oleh reviewer manusia."

    after_state = {
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "confidence": link.confidence,
    }

    # Log immutable audit event
    audit_entry = log_audit_event(
        db=db,
        entity_type="hadith_sharh_link",
        entity_id=link.id,
        action="VERIFY",
        actor=actor_name,
        request_id=x_request_id,
        before_state=before_state,
        after_state=after_state,
        notes=link.notes,
    )

    db.commit()
    db.refresh(link)

    return {
        "status": "verified",
        "link_id": str(link.id),
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "audit_id": str(audit_entry.id),
        "actor": actor_name,
        "request_id": audit_entry.request_id,
        "message": "Tautan Hadis–Syarah berhasil diverifikasi (verified=true).",
    }


@router.post("/links/{link_id}/reject")
def reject_review_link(
    link_id: str,
    req: ReviewActionRequest | None = None,
    x_reviewer: str | None = Header(None, alias="X-Reviewer"),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
):
    """Aksi reviewer untuk menolak kandidat tautan yang tidak tepat atau tidak sesuai."""
    uid = to_uuid(link_id)
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == uid)) if uid else None
    if not link:
        raise HTTPException(status_code=404, detail="Tautan Hadits–Syarah tidak ditemukan.")

    actor_name = (req.reviewer if req and req.reviewer else None) or x_reviewer or "reviewer"

    before_state = {
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "confidence": link.confidence,
    }

    link.verified = False
    link.review_status = "rejected"

    notes_parts = []
    if req and req.reason:
        notes_parts.append(f"Alasan: {req.reason.strip()}")
    if req and req.notes:
        notes_parts.append(req.notes.strip())
    if actor_name:
        notes_parts.append(f"[Rejected by: {actor_name.strip()}]")

    if notes_parts:
        link.notes = " • ".join(notes_parts)
    elif not link.notes:
        link.notes = "Ditolak oleh reviewer manusia."

    after_state = {
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "confidence": link.confidence,
    }

    # Log immutable audit event
    audit_entry = log_audit_event(
        db=db,
        entity_type="hadith_sharh_link",
        entity_id=link.id,
        action="REJECT",
        actor=actor_name,
        request_id=x_request_id,
        before_state=before_state,
        after_state=after_state,
        notes=link.notes,
    )

    db.commit()
    db.refresh(link)

    return {
        "status": "rejected",
        "link_id": str(link.id),
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "audit_id": str(audit_entry.id),
        "actor": actor_name,
        "request_id": audit_entry.request_id,
        "message": "Tautan kandidat Hadis–Syarah ditolak (review_status=rejected).",
    }


@router.post("/links/{link_id}/reset")
def reset_review_link(
    link_id: str,
    x_reviewer: str | None = Header(None, alias="X-Reviewer"),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    db: Session = Depends(get_db),
):
    """Mereset status verifikasi tautan kembali ke status 'pending'."""
    uid = to_uuid(link_id)
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == uid)) if uid else None
    if not link:
        raise HTTPException(status_code=404, detail="Tautan Hadits–Syarah tidak ditemukan.")

    actor_name = x_reviewer or "reviewer"

    before_state = {
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "confidence": link.confidence,
    }

    link.verified = False
    # Hitung ulang default review status dari confidence
    conf = link.confidence or 0.0
    if conf >= 0.90:
        link.review_status = "auto_candidate"
    elif conf >= 0.75:
        link.review_status = "review"
    elif conf >= 0.50:
        link.review_status = "weak_match"
    else:
        link.review_status = "pending"

    link.notes = None

    after_state = {
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
        "confidence": link.confidence,
    }

    # Log immutable audit event
    audit_entry = log_audit_event(
        db=db,
        entity_type="hadith_sharh_link",
        entity_id=link.id,
        action="RESET",
        actor=actor_name,
        request_id=x_request_id,
        before_state=before_state,
        after_state=after_state,
        notes="Reset ke status pending",
    )

    db.commit()
    db.refresh(link)

    return {
        "status": "reset",
        "link_id": str(link.id),
        "verified": link.verified,
        "review_status": link.review_status,
        "audit_id": str(audit_entry.id),
        "message": "Status verifikasi tautan berhasil direset ke antrean pending.",
    }


@router.get("/stats")
def get_review_stats(db: Session = Depends(get_db)):
    """Mengambil statistik agregat dashboard review."""
    links = list(db.scalars(select(HadithSharhLink)))
    total = len(links)
    verified = sum(1 for l in links if l.verified or l.review_status == "verified")
    rejected = sum(1 for l in links if l.review_status == "rejected")
    pending = sum(1 for l in links if not l.verified and l.review_status != "rejected")
    auto_cand = sum(1 for l in links if l.review_status == "auto_candidate")
    review_need = sum(1 for l in links if l.review_status == "review")
    weak_match = sum(1 for l in links if l.review_status == "weak_match")
    avg_conf = round(sum(l.confidence or 0.0 for l in links) / total, 4) if total > 0 else 0.0

    return {
        "total_links": total,
        "verified_count": verified,
        "rejected_count": rejected,
        "pending_count": pending,
        "auto_candidates_count": auto_cand,
        "review_needed_count": review_need,
        "weak_matches_count": weak_match,
        "avg_confidence": avg_conf,
        "avg_confidence_percent": round(avg_conf * 100, 2),
        "verification_progress_percent": round((verified / total) * 100, 2) if total > 0 else 0.0,
    }


@router.post("/seed-sample-queue")
def seed_sample_review_queue(db: Session = Depends(get_db)):
    """Menyediakan dataset sampel antrean review yang kaya untuk pengujian Review Dashboard."""
    collection = db.scalar(select(Collection).where(Collection.slug == "shahih_bukhari"))
    if not collection:
        collection = Collection(
            slug="shahih_bukhari",
            name="Shahih al-Bukhari",
            language="id",
            total_expected=7008,
        )
        db.add(collection)
        db.flush()

    # Pastikan minimal Hadis #1, #2, #3 ada
    sample_hadiths_data = [
        (1, "حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ قَالَ حَدَّثَنَا سُفْيَانُ قَالَ حَدَّثَنَا يَحْيَى بْنُ سَعِيدٍ الأَنْصَارِيُّ قَالَ أَخْبَرَنِي مُحَمَّدُ بْنُ إِبْرَاهِيمَ التَّيْمِيُّ أَنَّهُ سَمِعَ عَلْقَمَةَ بْنَ وَقَّاصٍ اللَّيْثِيَّ يَقُولُ سَمِعْتُ عُمَرَ بْنَ الْخَطَّابِ رَضِيَ اللَّهُ عَنْهُ عَلَى الْمِنْبَرِ قَالَ سَمِعْتُ رَسُولَ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ يَقُولُ إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى فَمَنْ كَانَتْ هِجْرَتُهُ إِلَى دُنْيَا يُصِيبُهَا أَوْ إِلَى امْرَأَةٍ يَنْكِحُهَا فَهِجْرَتُهُ إِلَى مَا هَاجَرَ إِلَيْهِ", "Telah menceritakan kepada kami Al Humaidi Abdullah bin Az Zubair berkata, telah menceritakan kepada kami Sufyan yang berkata, telah menceritakan kepada kami Yahya bin Sa'id Al Anshari berkata, telah mengabarkan kepada kami Muhammad bin Ibrahim At Taimi, bahwa dia pernah mendengar Alqamah bin Waqqash Al Laitsi berkata; saya pernah mendengar Umar bin Al Khaththab di atas mimbar berkata; saya mendengar Rasulullah shallallahu 'alaihi wasallam bersabda: 'Semua perbuatan tergantung niatnya, dan (balasan) bagi tiap-tiap orang (tergantung) apa yang diniatkan; Barangsiapa niat hijrahnya karena dunia yang ingin digapainya atau karena seorang perempuan yang ingin dinikahinya, maka hijrahnya adalah kepada apa dia diniatkan.'"),
        (2, "حَدَّثَنَا عَبْدُ اللَّهِ بْنُ يُوسُفَ قَالَ أَخْبَرَنَا مَالِكٌ عَنْ هِشَامِ بْنِ عُرْوَةَ عَنْ أَبِيهِ عَنْ عَائِشَةَ أُمِّ الْمُؤْمِنِينَ رَضِيَ اللَّهُ عَنْهَا أَنَّ الْحَارِثَ بْنَ هِشَامٍ رَضِيَ اللَّهُ عَنْهُ سَأَلَ رَسُولَ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ فَقَالَ يَا رَسُولَ اللَّهِ كَيْفَ يَأْتِيكَ الْوَحْيُ فَقَالَ رَسُولُ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ أَحْيَانًا يَأْتِينِي مِثْلَ صَلْصَلَةِ الْجَرَسِ وَهُوَ أَشَدُّهُ عَلَيَّ فَيُفْصَمُ عَنِّي وَقَدْ وَعَيْتُ عَنْهُ مَا قَالَ وَأَحْيَانًا يَتَمَثَّلُ لِيَ الْمَلَكُ رَجُلاً فَيُكَلِّمُنِي فَأَعِي مَا يَقُولُ", "Telah menceritakan kepada kami Abdullah bin Yusuf berkata, telah mengabarkan kepada kami Malik dari Hisyam bin Urwah dari bapaknya dari Aisyah Ummul Mukminin bahwa Al Harits bin Hisyam bertanya kepada Rasulullah: 'Wahai Rasulullah, bagaimana wahyu turun kepadamu?' Beliau menjawab: 'Kadang datang seperti gemerincing lonceng, dan itu yang paling berat bagiku, lalu terlepas dariku dan aku telah menghafal apa yang disampaikannya. Dan kadang malaikat menjelma sebagai seorang laki-laki lalu berbicara kepadaku dan aku menghafal apa yang dikatakannya.'"),
        (3, "حَدَّثَنَا يَحْيَى بْنُ بُكَيْرٍ قَالَ حَدَّثَنَا اللَّيْثُ عَنْ عُقَيْلٍ عَنِ ابْنِ شِهَابٍ عَنْ عُرْوَةَ بْنِ الزُّبَيْرِ عَنْ عَائِشَةَ أُمِّ الْمُؤْمِنِينَ أَنَّهَا قَالَتْ أَوَّلُ مَا بُدِئَ بِهِ رَسُولُ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ مِنَ الْوَحْيِ الرُّؤْيَا الصَّالِحَةُ فِي النَّوْمِ فَكَانَ لاَ يَرَى رُؤْيَا إِلاَّ جَاءَتْ مِثْلَ فَلَقِ الصُّبْحِ ثُمَّ حُبِّبَ إِلَيْهِ الْخَلاَءُ وَكَانَ يَخْلُو بِغَارِ حِرَاءٍ", "Telah menceritakan kepada kami Yahya bin Bukair berkata, telah menceritakan kepada kami Al Laits dari Uqail dari Ibnu Syihab dari Urwah bin Az Zubair dari Aisyah Ummul Mukminin berkata: 'Awal mula wahyu yang datang kepada Rasulullah adalah mimpi yang benar dalam tidur. Beliau tidak melihat suatu mimpi melainkan datang seperti terangnya fajar subuh. Kemudian beliau menyukai menyendiri, dan beliau menyendiri di Gua Hira...'"),
    ]

    for num, arab, trans in sample_hadiths_data:
        h = db.scalar(select(Hadith).where(Hadith.collection_id == collection.id, Hadith.external_number == num))
        if not h:
            h = Hadith(
                collection_id=collection.id,
                source_id=collection.id,  # fallback
                external_number=num,
                arabic_text=arab,
                translation=trans,
            )
            db.add(h)
    db.flush()

    # Seksi Syarah Sampel
    sample_sharh_data = [
        (1, 9, "Syarah Hadis #1: Penjelasan Niat & Permulaan Wahyu", "قَوْلُهُ (إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ) أَيْ صِحَّةُ الأَعْمَالِ أَوْ كَمَالُهَا أَوْ قَبُولُهَا مَشْرُوطٌ بِالنِّيَّةِ. وَالنِّيَّةُ فِي اللُّغَةِ الْقَصْدُ، وَفِي الشَّرْعِ قَصْدُ الشَّيْءِ مُقْتَرِنًا بِفِعْلِهِ. وَقَدْ أَوْرَدَ الْمُصَنِّفُ رَحِمَهُ اللَّهُ هَذَا الْحَدِيثَ فِي صَدْرِ كِتَابِهِ لِيَكُونَ خُطْبَةً لَهُ، إِشَارَةً إِلَى أَنَّ كُلَّ عَمَلٍ لَا يُرَادُ بِهِ وَجْهُ اللَّهِ فَهُوَ بَاطِلٌ.", "Perkataan beliau 'Sesungguhnya amal-amal itu bergantung pada niat': Maksudnya sahnya amal, atau kesempurnaannya, atau diterimanya amal disyaratkan dengan adanya niat. Niat secara bahasa bermakna 'maksud/tujuan', sedangkan secara syariat adalah menyengaja suatu hal yang diiringi dengan perbuatannya. Al-Bukhari membawakan hadis ini di awal kitabnya sebagai khutbah (pembuka) kitab, sebagai isyarat bahwa setiap amal yang tidak ditujukan mengharap wajah Allah maka amal itu batil.", 1, 0.95, "auto_candidate", False, {"number_score": 1.0, "text_score": 0.88, "context_score": 0.0, "detected_numbers": [1], "quotes_found": ["إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ"]}),
        (1, 24, "Syarah Hadis #2: Cara Datangnya Wahyu (Salsalatul Jaras)", "قَوْلُهُ (مِثْلَ صَلْصَلَةِ الْجَرَسِ) الصَّلْصَلَةُ فِي الأَصْلِ صَوْتُ وُقُوعِ الْحَدِيدِ بَعْضِهِ عَلَى بَعْضٍ. وَإِنَّمَا كَانَ أَشَدَّهُ عَلَيْهِ لِأَنَّهُ يَنْزِعُ عَنْهُ صِفَةَ الْبَشَرِيَّةِ وَيَتَّصِلُ بِالْمَلَكُوتِ الأَعْلَى فَيَثْقُلُ عَلَيْهِ ذَلِكَ ثِقَلًا شَدِيدًا.", "Perkataan beliau 'seperti gemerincing lonceng': Salsalah pada asalnya adalah suara besi yang saling beradu. Hal itu merupakan yang paling berat bagi beliau karena melepaskan sifat kemanusiaan dan terhubung langsung dengan alam malakut tertinggi sehingga terasa sangat berat.", 2, 0.85, "review", False, {"number_score": 0.0, "text_score": 0.92, "context_score": 0.0, "detected_numbers": [], "quotes_found": ["مِثْلَ صَلْصَلَةِ الْجَرَسِ"]}),
        (1, 35, "Syarah Hadis #3: Awal Turunnya Wahyu di Gua Hira", "قَوْلُهُ (أَوَّلُ مَا بُدِئَ بِهِ) دَلِيلٌ عَلَى أَنَّ الرُّؤْيَا الصَّادِقَةَ كَانَتْ مُقَدِّمَةً لِلْيَقَظَةِ. وَكَانَ ذَلِكَ سِتَّةَ أَشْهُرٍ قَبْلَ نُزُولِ جِبْرِيلَ عَلَيْهِ السَّلَامُ بِالْقُرْآنِ فِي غَارِ حِرَاءٍ.", "Perkataan beliau 'Awal mula wahyu yang datang': Bukti bahwa mimpi yang benar merupakan mukadimah bagi wahyu dalam keadaan terjaga. Hal tersebut berlangsung selama enam bulan sebelum turunnya Jibril 'alaihissalam membawa Al-Qur'an di Gua Hira.", 3, 0.78, "review", False, {"number_score": 0.0, "text_score": 0.82, "context_score": 0.0, "detected_numbers": [], "quotes_found": ["أَوَّلُ مَا بُدِئَ بِهِ"]}),
        (1, 42, "Syarah Bab Keutamaan Ilmu dan Sanad", "قَوْلُهُ (بَابُ فَضْلِ الْعِلْمِ) الْمُرَادُ بِهِ الْعِلْمُ الشَّرْعِيُّ الَّذِي يُفِيدُ مَعْرِفَةَ مَا يَجِبُ عَلَى الْمُكَلَّفِ مِنْ أَمْرِ دِينِهِ فِي عِبَادَاتِهِ وَمُعَامَلَاتِهِ.", "Perkataan beliau 'Bab Keutamaan Ilmu': Yang dimaksud adalah ilmu syar'i yang memberi faidah pemahaman atas apa yang diwajibkan bagi mukallaf menyangkut urusan agamanya dalam ibadah dan muamalah.", 1, 0.58, "weak_match", False, {"number_score": 0.0, "text_score": 0.45, "context_score": 0.0, "detected_numbers": [], "quotes_found": []}),
    ]

    created_links_count = 0

    for vol, page, title, arab, trans, target_hadith_num, conf, cat, verified, evidence in sample_sharh_data:
        sec = db.scalar(select(SharhSection).where(SharhSection.volume == vol, SharhSection.page == page))
        if not sec:
            sec = SharhSection(
                work_slug="fathul_bari",
                volume=vol,
                printed_page=page,
                pdf_page=page,
                page=page,
                section_order=1,
                title=title,
                arabic_text=arab,
                translation=trans,
                extraction_status="segmented",
                created_at=datetime.now(timezone.utc),
            )
            db.add(sec)
            db.flush()

        target_hadith = db.scalar(select(Hadith).where(Hadith.collection_id == collection.id, Hadith.external_number == target_hadith_num))
        if target_hadith and sec:
            link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.hadith_id == target_hadith.id, HadithSharhLink.sharh_section_id == sec.id))
            if not link:
                link = HadithSharhLink(
                    hadith_id=target_hadith.id,
                    sharh_section_id=sec.id,
                    match_method="deterministic_v1",
                    confidence=conf,
                    review_status=cat,
                    verified=verified,
                    evidence=json.dumps(evidence, ensure_ascii=False),
                    notes=f"Kandidat matching otomatis ({cat}) confidence {round(conf * 100, 1)}%",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(link)
                created_links_count += 1

    db.commit()

    return {
        "status": "seeded",
        "message": f"Berhasil memuat {created_links_count} tautan sampel antrean review baru.",
    }
