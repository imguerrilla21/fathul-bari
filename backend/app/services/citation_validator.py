"""Citation Validator & Anti-Hallucination Guardrail Service.

Memastikan sitasi AI memenuhi aturan Blueprint Bagian 30 & 31:
1. Tidak mengarang nomor hadis, jilid, halaman, atau kutipan.
2. Memverifikasi keberadaan data pada database lokal (Ahmad Sanusi API provenance & Fathul Bari turats).
3. Menyediakan format sitasi akademik standar (Turats Indonesia, Chicago, BibTeX, Markdown).
"""

import re
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Collection, Hadith, HadithSharhLink, SharhSection
from app.services.citation_generator import generate_citations


def validate_citation_record(
    db: Session,
    collection_slug: str = "shahih_bukhari",
    hadith_number: int | None = None,
    volume: int | None = None,
    page: int | None = None,
    sharh_id: str | None = None,
) -> dict[str, Any]:
    """Memvalidasi integritas catatan sitasi terhadap database lokal."""
    hadith_valid = False
    sharh_valid = False
    verified_by_reviewer = False
    evidence_notes = []

    hadith_obj: Hadith | None = None
    sharh_obj: SharhSection | None = None

    # 1. Validasi Hadis
    if hadith_number is not None:
        collection = db.scalar(select(Collection).where(Collection.slug == collection_slug))
        if collection:
            hadith_obj = db.scalar(
                select(Hadith).where(
                    Hadith.collection_id == collection.id,
                    Hadith.external_number == hadith_number,
                )
            )
            if hadith_obj:
                hadith_valid = True
                evidence_notes.append(f"Hadis #{hadith_number} terdaftar di database lokal ({collection.name}).")
            else:
                evidence_notes.append(f"Hadis #{hadith_number} belum ada di DB lokal (dapat disinkronkan on-demand).")

    # 2. Validasi Syarah Section
    if sharh_id:
        sharh_obj = db.scalar(select(SharhSection).where(SharhSection.id == sharh_id))
    elif volume is not None and page is not None:
        sharh_obj = db.scalar(
            select(SharhSection).where(
                SharhSection.work_slug == "fathul_bari",
                SharhSection.volume == volume,
                SharhSection.page == page,
            )
        )

    if sharh_obj:
        sharh_valid = True
        evidence_notes.append(f"Syarah Fathul Bari Jilid {sharh_obj.volume} Hal. {sharh_obj.page} terverifikasi pada database teks.")

        # Periksa apakah ada tautan verifikasi manusia
        if hadith_obj:
            link = db.scalar(
                select(HadithSharhLink).where(
                    HadithSharhLink.hadith_id == hadith_obj.id,
                    HadithSharhLink.sharh_section_id == sharh_obj.id,
                )
            )
            if link and link.verified:
                verified_by_reviewer = True
                evidence_notes.append("Hubungan Hadis ↔ Syarah telah diverifikasi oleh peneliti (Human Verified).")
            elif link:
                evidence_notes.append(f"Hubungan Hadis ↔ Syarah berstatus '{link.review_status}' dengan confidence {link.confidence or 0:.2f}.")

    # Format sitasi akademik
    citations = generate_citations(
        hadith_number=hadith_number,
        collection_name="Shahih al-Bukhari" if collection_slug == "shahih_bukhari" else collection_slug,
        volume=sharh_obj.volume if sharh_obj else volume,
        page=sharh_obj.page if sharh_obj else page,
        sharh_title=sharh_obj.title if sharh_obj else None,
        hadith_arabic_excerpt=hadith_obj.arabic_text[:60] if hadith_obj and hadith_obj.arabic_text else None,
    )

    return {
        "is_valid": hadith_valid or sharh_valid,
        "hadith_valid": hadith_valid,
        "sharh_valid": sharh_valid,
        "human_verified": verified_by_reviewer,
        "collection_slug": collection_slug,
        "hadith_number": hadith_number,
        "volume": sharh_obj.volume if sharh_obj else volume,
        "page": sharh_obj.page if sharh_obj else page,
        "sharh_title": sharh_obj.title if sharh_obj else None,
        "citations": citations,
        "evidence_notes": evidence_notes,
    }


def audit_ai_response_citations(
    response_text: str,
    retrieved_hadiths: list[dict[str, Any]],
    retrieved_sharh: list[dict[str, Any]],
) -> dict[str, Any]:
    """Memeriksa teks jawaban AI untuk memastikan tidak ada nomor hadis / halaman fantasi (anti-hallucination)."""
    valid_hadith_nums = {h.get("number") for h in retrieved_hadiths if h.get("number") is not None}
    valid_pages = {s.get("page") for s in retrieved_sharh if s.get("page") is not None}

    # Cari pola nomor hadis dalam teks
    detected_hadith_nums = set()
    for m in re.finditer(r'(?:hadis|hadits|no\.?|nomor)\s*(?:bukhari\s*)?#?\s*(\d+)', response_text, re.IGNORECASE):
        try:
            detected_hadith_nums.add(int(m.group(1)))
        except ValueError:
            pass

    # Cari pola halaman dalam teks
    detected_pages = set()
    for m in re.finditer(r'(?:hal(?:aman)?\.?|hlm\.?)\s*(\d+)', response_text, re.IGNORECASE):
        try:
            detected_pages.add(int(m.group(1)))
        except ValueError:
            pass

    unverified_hadiths = detected_hadith_nums - valid_hadith_nums if valid_hadith_nums else set()
    unverified_pages = detected_pages - valid_pages if valid_pages else set()

    is_clean = len(unverified_hadiths) == 0 and len(unverified_pages) == 0

    return {
        "passed": is_clean,
        "detected_hadiths": sorted(list(detected_hadith_nums)),
        "valid_retrieved_hadiths": sorted(list(valid_hadith_nums)),
        "unverified_hadiths": sorted(list(unverified_hadiths)),
        "detected_pages": sorted(list(detected_pages)),
        "valid_retrieved_pages": sorted(list(valid_pages)),
        "unverified_pages": sorted(list(unverified_pages)),
        "audit_summary": "Passed anti-hallucination check." if is_clean else "Warning: Response contains citations not found in retrieved DB context.",
    }
