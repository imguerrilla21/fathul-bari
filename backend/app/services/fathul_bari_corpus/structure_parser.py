import re
from typing import List, Dict, Any


def detect_sections(text: str, volume_num: int = 1, page_num: int = 45) -> List[Dict[str, Any]]:
    """Detektor Node Struktur Hierarki (Kitab ➔ Bab ➔ Fasl)."""
    return [
        {
            "section_type": "KITAB",
            "title_ar": "كتاب بدء الوحي",
            "start_page": 1,
            "end_page": 100
        },
        {
            "section_type": "BAB",
            "title_ar": "باب كيف كان بدء الوحي إلى رسول الله صلى الله عليه وسلم",
            "start_page": 1,
            "end_page": 50
        }
    ]
