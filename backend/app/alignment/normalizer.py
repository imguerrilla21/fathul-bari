import hashlib
import re

def normalize_arabic(text: str) -> str:
    """
    Normalizes Arabic text by removing tatweel, diacritics, and standardizing alef/teh marbuta.
    """
    if not text:
        return ""
    # Remove diacritics (harakat)
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    # Remove tatweel
    text = re.sub(r'\u0640', '', text)
    # Normalize Alef
    text = re.sub(r'[\u0622\u0623\u0625]', '\u0627', text)
    # Normalize Teh Marbuta
    text = re.sub(r'\u0629', '\u0647', text)
    return text.strip()

def generate_matn_fingerprint(normalized_matn: str) -> str:
    if not normalized_matn:
        return ""
    return hashlib.sha256(normalized_matn.encode('utf-8')).hexdigest()
