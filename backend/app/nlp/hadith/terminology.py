import re
from typing import List, Dict, Any

HADITH_TERMINOLOGY = [
    "صحيح",
    "حسن",
    "ضعيف",
    "موضوع",
    "مرفوع",
    "موقوف",
    "مقطوع",
    "مرسل",
    "منقطع",
    "معضل",
    "معلق",
    "متواتر",
    "غريب",
    "عزيز",
    "مشهور"
]

def extract_hadith_terminology(text: str) -> List[Dict[str, Any]]:
    """
    Extracts occurrences of recognized Hadith grading/terminology.
    Note: detecting the term does NOT mean it's the grading of the specific Hadith.
    It simply logs that the term was mentioned in this context.
    """
    mentions = []
    
    for term in HADITH_TERMINOLOGY:
        # Match exact term in text
        for match in re.finditer(rf"\b{term}\b", text):
            mentions.append({
                "surface": match.group(),
                "start_char": match.start(),
                "end_char": match.end(),
                "entity_type": "TERM_MENTION"
            })
            
    return mentions
