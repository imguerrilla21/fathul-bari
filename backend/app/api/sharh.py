import json
import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Collection, Hadith, HadithSharhLink, SharhSection
from app.services.arabic_normalizer import normalize_arabic
from app.services.hadith_linker import evaluate_against_gold, link_sharh_section_to_hadiths
from app.services.pdf_extractor import extract_pdf
from app.services.sharh_segmenter import segment_page_to_sections

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sharh", tags=["Syarah Fathul Bari Pipeline"])


class ReviewActionRequest(BaseModel):
    action: str = Field(enum=["verify", "reject", "reset"], description="Aksi human review")
    notes: str | None = Field(default=None, description="Catatan hasil verifikasi peneliti")


class ExtractPDFRequest(BaseModel):
    pdf_path: str = Field(default="data/fathul_bari/raw/fathul_bari_volume_01.pdf")
    volume: int = Field(default=1, ge=1)
    save_to_db: bool = Field(default=True)


def background_extract_and_segment(pdf_path: str, volume: int, save_to_db: bool):
    db: Session = SessionLocal()
    try:
        pages = extract_pdf(pdf_path, output_dir="data/fathul_bari/extracted")
        for p in pages:
            sections = segment_page_to_sections(p, volume=volume)
            if save_to_db:
                for sec in sections:
                    db_sec = SharhSection(
                        work_slug=sec["work_slug"],
                        volume=sec["volume"],
                        pdf_page=sec["pdf_page"],
                        printed_page=sec["printed_page"],
                        page=sec["page"],
                        section_order=sec["section_order"],
                        title=sec["title"],
                        arabic_text=sec["arabic_text"],
                        normalized_text=sec["normalized_text"],
                        source_file=sec["source_file"],
                        source_hash=sec["source_hash"],
                        extraction_status="segmented",
                    )
                    db.add(db_sec)
                db.commit()
    except Exception as exc:
        logger.error("Background extraction failed: %s", exc)
    finally:
        db.close()


@router.get("/hadith/{kitab}/{nomor}")
def get_sharh_by_hadith(kitab: str, nomor: int, db: Session = Depends(get_db)):
    """Mengambil penjelasan Syarah Fathul Bari yang tertaut dengan hadis beserta confidence & status review."""
    collection = db.scalar(select(Collection).where(Collection.slug == kitab))
    if not collection:
        raise HTTPException(status_code=404, detail=f"Koleksi {kitab} tidak ditemukan.")

    hadith = db.scalar(
        select(Hadith).where(
            Hadith.collection_id == collection.id,
            Hadith.external_number == nomor,
        )
    )
    if not hadith:
        return {
            "kitab": kitab,
            "nomor": nomor,
            "has_hadith": False,
            "sharh_sections": [],
            "message": "Hadis belum diunduh ke database lokal.",
        }

    links = list(
        db.scalars(
            select(HadithSharhLink)
            .where(HadithSharhLink.hadith_id == hadith.id)
            .order_by(HadithSharhLink.confidence.desc())
        )
    )

    results = []
    for link in links:
        sec = db.scalar(select(SharhSection).where(SharhSection.id == link.sharh_section_id))
        if sec:
            evidence_obj = None
            if link.evidence:
                try:
                    evidence_obj = json.loads(link.evidence)
                except Exception:
                    evidence_obj = {"raw": link.evidence}

            results.append({
                "link_id": str(link.id),
                "section_id": str(sec.id),
                "work_slug": sec.work_slug,
                "volume": sec.volume,
                "pdf_page": sec.pdf_page,
                "printed_page": sec.printed_page or sec.page,
                "page": sec.printed_page or sec.page,
                "section_order": sec.section_order,
                "title": sec.title,
                "arabic_text": sec.arabic_text,
                "normalized_text": sec.normalized_text,
                "translation": sec.translation,
                "source_file": sec.source_file,
                "match_method": link.match_method,
                "confidence": link.confidence,
                "confidence_percent": round((link.confidence or 0.0) * 100, 1),
                "review_status": link.review_status,
                "verified": link.verified,
                "evidence": evidence_obj,
                "notes": link.notes,
            })

    return {
        "kitab": kitab,
        "nomor": nomor,
        "hadith_id": str(hadith.id),
        "total_sharh_sections": len(results),
        "sharh_sections": results,
    }


@router.get("/sections")
def list_sharh_sections(
    work_slug: str = Query(default="fathul_bari"),
    volume: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Mendaftar seluruh seksi syarah terstruktur yang tersimpan."""
    stmt = select(SharhSection).where(SharhSection.work_slug == work_slug)
    if volume is not None:
        stmt = stmt.where(SharhSection.volume == volume)

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = list(
        db.scalars(
            stmt.order_by(SharhSection.volume, SharhSection.printed_page, SharhSection.section_order)
            .offset(offset)
            .limit(limit)
        )
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "sections": [
            {
                "id": str(x.id),
                "work_slug": x.work_slug,
                "volume": x.volume,
                "pdf_page": x.pdf_page,
                "printed_page": x.printed_page or x.page,
                "page": x.printed_page or x.page,
                "section_order": x.section_order,
                "title": x.title,
                "arabic_text": x.arabic_text,
                "translation": x.translation,
                "extraction_status": x.extraction_status,
                "created_at": x.created_at.isoformat() if x.created_at else None,
            }
            for x in rows
        ],
    }


@router.post("/extract")
def trigger_extraction(
    req: ExtractPDFRequest,
    background_tasks: BackgroundTasks,
    sync_mode: str = Query(default="sync", enum=["sync", "async"]),
    db: Session = Depends(get_db),
):
    """Memicu pipeline ekstraksi PDF & segmentasi seksi ulasan."""
    if sync_mode == "async":
        background_tasks.add_task(background_extract_and_segment, req.pdf_path, req.volume, req.save_to_db)
        return {"status": "started", "message": f"Ekstraksi {req.pdf_path} dimulai di background."}

    # Synchronous extraction
    try:
        pages = extract_pdf(req.pdf_path, output_dir="data/fathul_bari/extracted")
        saved_count = 0
        for p in pages:
            sections = segment_page_to_sections(p, volume=req.volume)
            if req.save_to_db:
                for sec in sections:
                    db_sec = SharhSection(
                        work_slug=sec["work_slug"],
                        volume=sec["volume"],
                        pdf_page=sec["pdf_page"],
                        printed_page=sec["printed_page"],
                        page=sec["page"],
                        section_order=sec["section_order"],
                        title=sec["title"],
                        arabic_text=sec["arabic_text"],
                        normalized_text=sec["normalized_text"],
                        source_file=sec["source_file"],
                        source_hash=sec["source_hash"],
                        extraction_status="segmented",
                    )
                    db.add(db_sec)
                    saved_count += 1
                db.commit()

        return {
            "status": "completed",
            "extracted_pages": len(pages),
            "sections_saved": saved_count,
            "volume": req.volume,
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ekstraksi gagal: {exc}")


@router.post("/link")
def trigger_linking_engine(
    volume: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Memicu Hadith-Sharh Linking Engine untuk seluruh seksi syarah."""
    stmt = select(SharhSection).where(SharhSection.work_slug == "fathul_bari")
    if volume is not None:
        stmt = stmt.where(SharhSection.volume == volume)

    sections = list(db.scalars(stmt))
    total_links = 0
    for sec in sections:
        links = link_sharh_section_to_hadiths(db, sec)
        total_links += len(links)

    return {
        "status": "completed",
        "sections_processed": len(sections),
        "total_links_generated": total_links,
    }


@router.post("/review/{link_id}")
def human_review_link(
    link_id: str,
    req: ReviewActionRequest,
    db: Session = Depends(get_db),
):
    """Aksi human verification oleh peneliti untuk memverifikasi atau menolak kandidat tautan."""
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == link_id))
    if not link:
        raise HTTPException(status_code=404, detail="Tautan hadits-syarah tidak ditemukan.")

    if req.action == "verify":
        link.verified = True
        link.review_status = "verified"
    elif req.action == "reject":
        link.verified = False
        link.review_status = "rejected"
    elif req.action == "reset":
        link.verified = False
        link.review_status = "pending"

    if req.notes:
        link.notes = req.notes

    db.commit()
    db.refresh(link)

    return {
        "status": "ok",
        "link_id": str(link.id),
        "review_status": link.review_status,
        "verified": link.verified,
        "notes": link.notes,
    }


@router.get("/metrics")
def get_pipeline_metrics(db: Session = Depends(get_db)):
    """Mengambil metrik komprehensif pipeline ekstraksi, segmentasi, status review, dan evaluasi Precision/Recall."""
    total_sections = int(db.scalar(select(func.count()).select_from(SharhSection)) or 0)
    total_links = int(db.scalar(select(func.count()).select_from(HadithSharhLink)) or 0)
    verified_links = int(db.scalar(select(func.count()).select_from(HadithSharhLink).where(HadithSharhLink.verified.is_(True))) or 0)
    auto_candidates = int(db.scalar(select(func.count()).select_from(HadithSharhLink).where(HadithSharhLink.review_status == "auto_candidate")) or 0)
    pending_reviews = int(db.scalar(select(func.count()).select_from(HadithSharhLink).where(HadithSharhLink.review_status == "pending")) or 0)

    gold_eval = evaluate_against_gold(db)

    return {
        "work_slug": "fathul_bari",
        "total_sharh_sections": total_sections,
        "total_hadith_links": total_links,
        "verified_links": verified_links,
        "auto_candidates": auto_candidates,
        "pending_reviews": pending_reviews,
        "verification_rate_percent": round((verified_links / max(total_links, 1)) * 100, 2),
        "gold_evaluation": gold_eval,
    }


@router.post("/seed-sample")
def seed_sample_sharh(db: Session = Depends(get_db)):
    """Memasukkan sampel Syarah Fathul Bari awal untuk Hadis #1, #2, & #3 untuk menguji linking engine."""
    collection = db.scalar(select(Collection).where(Collection.slug == "shahih_bukhari"))
    if not collection:
        raise HTTPException(status_code=400, detail="Collection shahih_bukhari belum ada. Jalankan seed.py.")

    # Section 1 - Hadis #1
    sec1 = db.scalar(select(SharhSection).where(SharhSection.work_slug == "fathul_bari", SharhSection.volume == 1, SharhSection.printed_page == 9))
    if not sec1:
        sec1 = SharhSection(
            work_slug="fathul_bari",
            volume=1,
            pdf_page=9,
            printed_page=9,
            page=9,
            section_order=1,
            title="Syarah Hadis Pertama: Innamal A'malu bin-Niyyat (Permulaan Wahyu & Niat)",
            arabic_text="قَوْلُهُ (إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ) أَيْ صِحَّةُ الأَعْمَالِ أَوْ كَمَالُهَا أَوْ قَبُولُهَا مَشْرُوطٌ بِالنِّيَّةِ. وَالنِّيَّةُ فِي اللُّغَةِ الْقَصْدُ، وَفِي الشَّرْعِ قَصْدُ الشَّيْءِ مُقْتَرِنًا بِفِعْلِهِ. وَقَدْ أَوْرَدَ الْمُصَنِّفُ رَحِمَهُ اللَّهُ هَذَا الْحَدِيثَ فِي صَدْرِ كِتَابِهِ لِيَكُونَ خُطْبَةً لَهُ، إِشَارَةً إِلَى أَنَّ كُلَّ عَمَلٍ لَا يُرَادُ بِهِ وَجْهُ اللَّهِ فَهُوَ بَاطِلٌ.",
            normalized_text=normalize_arabic("قوله إنما الأعمال بالنيات أي صحة الأعمال أو كمالها أو قبولها مشروط بالنية."),
            translation="Perkataan beliau 'Sesungguhnya amal-amal itu bergantung pada niat': Maksudnya sahnya amal, atau kesempurnaannya, atau diterimanya amal disyaratkan dengan adanya niat. Niat secara bahasa bermakna 'maksud/tujuan', sedangkan secara syariat adalah menyengaja suatu hal yang diiringi dengan perbuatannya. Al-Bukhari membawakan hadis ini di awal kitabnya sebagai khutbah (pembuka) kitab, sebagai isyarat bahwa setiap amal yang tidak ditujukan mengharap wajah Allah maka amal itu batil.",
            extraction_status="verified",
            source_file="fathul_bari_volume_01.pdf",
            created_at=datetime.now(timezone.utc),
        )
        db.add(sec1)
        db.flush()

    # Section 2 - Hadis #2
    sec2 = db.scalar(select(SharhSection).where(SharhSection.work_slug == "fathul_bari", SharhSection.volume == 1, SharhSection.printed_page == 24))
    if not sec2:
        sec2 = SharhSection(
            work_slug="fathul_bari",
            volume=1,
            pdf_page=24,
            printed_page=24,
            page=24,
            section_order=1,
            title="Syarah Hadis Kedua: Kaifa Kana Bad'ul Wahyi (Cara Datangnya Wahyu)",
            arabic_text="قَوْلُهُ (كَيْفَ كَانَ بَدْءُ الْوَحْيِ إِلَى رَسُولِ اللَّهِ) وَالْوَحْيُ فِي اللُّغَةِ الْإِعْلَامُ فِي خَفَاءٍ. وَفِي حَدِيثِ عَائِشَةَ رَضِيَ اللَّهُ عَنْهَا سُؤَالُ الْحَارِثِ بْنِ هِشَامٍ: كَيْفَ يَأْتِيكَ الْوَحْيُ؟ فَقَالَ: أَحْيَانًا يَأْتِينِي مِثْلَ صَلْصَلَةِ الْجَرَسِ وَهُوَ أَشَدُّهُ عَلَيَّ.",
            normalized_text=normalize_arabic("قوله كيف كان بدء الوحي إلى رسول الله والوحي في اللغة الإعلام في خفاء."),
            translation="Perkataan beliau 'Bagaimana permulaan wahyu kepada Rasulullah': Wahyu secara bahasa adalah pemberitahuan secara rahasia/samar. Dalam hadis Aisyah terdapat pertanyaan Harits bin Hisyam: Bagaimana wahyu datang kepadamu? Beliau bersabda: Kadang datang kepadaku seperti gemerincing lonceng dan itulah yang paling berat bagiku.",
            extraction_status="verified",
            source_file="fathul_bari_volume_01.pdf",
            created_at=datetime.now(timezone.utc),
        )
        db.add(sec2)
        db.flush()

    db.commit()

    # Link both sections to Hadith #1 and #2
    link_sharh_section_to_hadiths(db, sec1)
    link_sharh_section_to_hadiths(db, sec2)

    return {
        "status": "ok",
        "message": "Sampel Fathul Bari Tahap 3 (Hadis #1 & #2) berhasil dimuat dan di-link dengan multi-signal engine.",
        "sections": [str(sec1.id), str(sec2.id)],
    }
