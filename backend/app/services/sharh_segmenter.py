import re
from typing import Any

from app.services.arabic_normalizer import normalize_arabic

SHARH_MARKERS = [
    r"قَوْلُهُ\s*\(.*?\)",
    r"قَوْلُهُ",
    r"قوله",
    r"قَوْلُهُ تَعَالَى",
    r"قوله تعالى",
    r"قَوْلُهُ بَابُ",
    r"قوله باب",
    r"حَدِيثُ",
    r"حديث",
    r"الْحَدِيثُ",
    r"الحديث",
    r"أَخْرَجَهُ",
    r"أخرجه",
    r"رَوَاهُ",
    r"رواه",
    r"بَابُ",
    r"باب",
]

MARKER_REGEX = re.compile("|".join(SHARH_MARKERS))


def detect_markers(text: str) -> list[str]:
    """Mendeteksi marker-marker ulasan syarah klasik dalam teks."""
    found = []
    for pattern in SHARH_MARKERS:
        clean_pat = pattern.replace(r"\s*", " ").replace(r"\(.*?\)", "")
        if re.search(pattern, text):
            found.append(clean_pat)
    return list(set(found))


def segment_page_to_sections(
    page_record: dict[str, Any],
    volume: int = 1,
    min_paragraph_len: int = 40,
) -> list[dict[str, Any]]:
    """Memecah teks halaman PDF menjadi seksi-seksi ulasan syarah terstruktur."""
    raw_text = page_record.get("text", "") or ""
    pdf_page = page_record.get("pdf_page", 1)
    printed_page = page_record.get("printed_page", pdf_page)
    source_file = page_record.get("source_file")
    source_hash = page_record.get("source_hash")

    if not raw_text.strip():
        return []

    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [raw_text.strip()]

    sections: list[dict[str, Any]] = []
    section_order = 1

    for idx, para in enumerate(paragraphs, start=1):
        if len(para) < min_paragraph_len and len(paragraphs) > 1:
            # Lewatkan header/footer yang terlalu pendek atau gabungkan
            continue

        markers = detect_markers(para)
        normalized = normalize_arabic(para)

        # Buat judul seksi berdasarkan baris pertama atau marker yang ditemukan
        first_line = para.split("\n")[0][:80]
        title = f"Fathul Bari Jilid {volume} Hal. {printed_page} (§{section_order})"
        if markers:
            title = f"{title} [{', '.join(markers[:2])}] - {first_line}..."

        sections.append({
            "work_slug": "fathul_bari",
            "volume": volume,
            "pdf_page": pdf_page,
            "printed_page": printed_page,
            "page": printed_page,
            "section_order": section_order,
            "title": title,
            "arabic_text": para,
            "normalized_text": normalized,
            "source_file": source_file,
            "source_hash": source_hash,
            "markers_found": markers,
            "extraction_status": "segmented",
        })
        section_order += 1

    return sections
