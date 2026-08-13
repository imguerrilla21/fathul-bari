import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.ingestion import SourcePage, TextBlock
from app.models.sharh import SharhSection


def detect_sections_and_hierarchy(db: Session, volume: int = 1) -> List[Dict[str, Any]]:
    """
    Mendeteksi pola struktur hirarki (Kitab, Bab, Sharh Section) dari halaman dan blok teks Fathul Bari.
    """
    sections = db.query(SharhSection).filter(SharhSection.volume == volume).all()
    detected_hierarchy = []

    for idx, sec in enumerate(sections, 1):
        raw = sec.arabic_text or ""
        
        # Check layout & lexical signals
        is_kitab = "كتاب" in raw[:100]
        is_bab = "باب" in raw[:100]
        
        sec_type = "KITAB" if is_kitab else ("BAB" if is_bab else "SHARH_SECTION")
        
        detected_hierarchy.append({
            "section_id": str(sec.id),
            "title": sec.title or f"Seksi Syarah #{idx}",
            "section_type": sec_type,
            "volume": sec.volume,
            "printed_page": sec.printed_page or sec.pdf_page or idx,
            "page_start": sec.pdf_page or idx,
            "page_end": (sec.pdf_page or idx) + 1
        })

    return detected_hierarchy
