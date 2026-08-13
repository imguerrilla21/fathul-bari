import re
import unicodedata

TATWEEL = "\u0640"

def normalize_arabic(text: str) -> str:
    """
    Normalizes Arabic text:
    - Normalizes Unicode composition
    - Removes Tatweel (Kashida)
    - Normalizes Alef variants (إأٱآ -> ا)
    - Normalizes Ya variants (ى -> ي)
    - Preserves Ta Marbuta (ة) so semantics are not lost.
    """
    text = unicodedata.normalize("NFC", text)

    # Remove tatweel
    text = text.replace(TATWEEL, "")

    # Normalize alef variants
    text = re.sub(r"[إأٱآ]", "ا", text)

    # Normalize ya / alef maqsura
    text = text.replace("ى", "ي")

    # Normalize waw variants (ؤ -> و)
    text = text.replace("ؤ", "و")
    
    # Normalize hamza (ئ -> ء) - simple approach for search normalization
    text = text.replace("ئ", "ء")

    return text
