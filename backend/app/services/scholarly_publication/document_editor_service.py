from typing import Dict, Any, List


def build_default_document_blocks() -> List[Dict[str, Any]]:
    """Membuat struktur blok awal dokumen riset ilmiah terstruktur."""
    return [
        {
            "id": "b-heading-1",
            "type": "HEADING",
            "level": 1,
            "text": "Analisis Syarah Niat dalam Fathul Bari",
            "origin": "HUMAN"
        },
        {
            "id": "b-abstract",
            "type": "PARAGRAPH",
            "text": "Abstrak: Kajian ini menganalisis kedudukan hukum niat dalam ibadah berdasarkan penjelasan Al-Hafizh Ibnu Hajar al-Asqalani dalam Fathul Bari.",
            "origin": "HUMAN"
        },
        {
            "id": "b-hadith-text",
            "type": "HADITH",
            "text": "عن عمر بن الخطاب رضي الله عنه قال: سمعت رسول الله صلى الله عليه وسلم يقول: \"إنما الأعمال بالنيات...\"",
            "origin": "HUMAN"
        },
        {
            "id": "b-sharh-analysis",
            "type": "PARAGRAPH",
            "text": "Ibnu Hajar menegaskan bahwa niat merupakan rukun utama dan syarat sahnya seluruh ibadah. Sitasi: [FB-V1-P45-C001].",
            "origin": "AI_DRAFT"
        }
    ]


def build_document_outline(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Membangun navigasi kerangka (Outline Navigator) dari blok dokumen."""
    outline = []
    for b in blocks:
        if b.get("type") in ["HEADING", "HADITH"]:
            outline.append({
                "id": b["id"],
                "title": b.get("text", "")[:40],
                "type": b.get("type")
            })
    return outline
