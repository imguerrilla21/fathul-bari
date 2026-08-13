import re
from typing import Dict, Any

# Simple regex-based boundary detection (in real cases, use NLP and ML models)
# We assume that typically "أن رسول الله" or "قال رسول الله" marks the beginning of the matn
MATN_TRIGGERS = [
    r"أن رسول الله.*(?:قال|يقول)",
    r"سمعت رسول الله.*(?:قال|يقول)",
    r"قال رسول الله",
    r"عن النبي.*(?:قال|يقول)"
]

def segment_hadith(text: str) -> Dict[str, Any]:
    """
    Attempts to segment a Hadith into Sanad (chain) and Matn (text).
    Returns boundaries and confidence score.
    """
    for trigger in MATN_TRIGGERS:
        match = re.search(trigger, text)
        if match:
            # The matn begins approximately at the trigger phrase
            matn_start = match.start()
            sanad_text = text[:matn_start].strip()
            matn_text = text[matn_start:].strip()
            
            return {
                "sanad_text": sanad_text,
                "matn_text": matn_text,
                "sanad_start": 0,
                "sanad_end": matn_start,
                "matn_start": matn_start,
                "confidence": 0.85
            }
            
    # Fallback if no clear boundary found
    return {
        "sanad_text": text,
        "matn_text": "",
        "sanad_start": 0,
        "sanad_end": len(text),
        "matn_start": -1,
        "confidence": 0.30,
        "status": "NEEDS_REVIEW"
    }
