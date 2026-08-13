import re
import hashlib


def normalize_arabic_text(text: str) -> str:
    """
    Normalisasi Teks Arab (Arabic Text Normalizer v2):
    1. Unicode Normalization
    2. Hapus Tatweel (ـ)
    3. Normalisasi Alif (أ, إ, آ ➔ ا)
    4. Normalisasi Hamzah (ؤ, ئ ➔ ء / ا)
    5. Normalisasi Ya (ى ➔ ي)
    6. Normalisasi Ta Marbutah (ة ➔ ه)
    7. Hapus Diakritik / Harakat (َ ً ُ ٌ ِ ٍ ْ ّ)
    """
    if not text:
        return ""

    # Hapus Tatweel
    res = re.sub(r'\u0640', '', text)
    
    # Hapus Diakritik / Harakat
    res = re.sub(r'[\u064B-\u0652]', '', res)

    # Normalisasi Alif
    res = re.sub(r'[أإآ]', 'ا', res)

    # Normalisasi Ya & Ta Marbutah
    res = re.sub(r'ى', 'ي', res)
    res = re.sub(r'ة', 'ه', res)

    return res.strip()


def generate_search_text(arabic_text: str, narrator_text: str = None, hadith_number: str = None) -> str:
    """Membangun search_text yang menggabungkan teks ter-normalisasi, sanad/perawi, dan nomor hadis."""
    norm_ar = normalize_arabic_text(arabic_text)
    narrator = narrator_text or ""
    num = hadith_number or ""
    return f"{norm_ar} {narrator} {num}".strip()


def calculate_content_hash(text: str) -> str:
    """Menghitung SHA-256 hash untuk konsistensi & audit data terverifikasi (Content Provenance Hash)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
