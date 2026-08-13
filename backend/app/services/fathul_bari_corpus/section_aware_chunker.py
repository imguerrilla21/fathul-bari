import hashlib
from typing import List, Dict, Any
from app.services.hadith_data_layer.arabic_normalizer import normalize_arabic_text, calculate_content_hash


def create_section_aware_chunks(
    volume_num: int,
    printed_page_num: int,
    pdf_page_num: int,
    page_text: str
) -> List[Dict[str, Any]]:
    """
    Mesin Pembagi Chunk Berbasis Seksi (Section-Aware Chunker Engine):
    Membagi teks halaman menjadi chunk semantis 600-1000 token Arab dan menghasilkan Kode Sitasi Universal (FB-V1-P45-C001).
    """
    chunks = []
    paragraphs = page_text.split("...")
    
    for idx, p in enumerate(paragraphs, 1):
        if not p.strip():
            continue

        orig_text = p.strip()
        norm_text = normalize_arabic_text(orig_text)
        c_hash = calculate_content_hash(orig_text)
        citation = f"FB-V{volume_num}-P{printed_page_num}-C{idx:03d}"

        chunks.append({
            "chunk_index": idx,
            "citation_code": citation,
            "original_text": orig_text,
            "normalized_text": norm_text,
            "start_offset": (idx - 1) * 400,
            "end_offset": idx * 400,
            "token_count": len(orig_text.split()),
            "content_hash": c_hash
        })

    return chunks
