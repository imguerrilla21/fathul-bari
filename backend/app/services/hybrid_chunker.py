import hashlib
import json
import math
import re
import unicodedata
from typing import Any

from app.services.arabic_normalizer import normalize_arabic

# Kamus pemetaan konsep semantik lintas-bahasa (Indonesian <-> Arabic canonical concepts)
MULTILINGUAL_CONCEPT_MAP: dict[str, list[str]] = {
    "niat": ["نية", "نيات", "قصد", "ارادة", "اخلاص", "عمل", "اعمال"],
    "amal": ["عمل", "اعمال", "فعل", "افعال", "سعي", "طاعة"],
    "wahyu": ["وحي", "تنزيل", "رؤيا", "جبريل", "ملك", "نبue", "نبوة", "بدء"],
    "ilmu": ["علم", "معرفة", "فقه", "رواية", "دراية", "علماء", "باب"],
    "shalat": ["صلاة", "ركوع", "سجود", "طهارة", "وضوء", "مسجد", "قبلة"],
    "puasa": ["صوم", "صيام", "رمضان", "افطار", "سحور", "امساك"],
    "zakat": ["زكاة", "صدقة", "مال", "فقراء", "مساكين", "انفاق"],
    "haji": ["حج", "عمرة", "طواف", "سعي", "عرفات", "احرام", "مكة", "اسود"],
    "thawaf": ["طواف", "بيت", "كعبة", "حجر", "اسود", "مسجد", "حرام"],
    "iman": ["ايمان", "توحيد", "عقيدة", "اسلام", "يقين", "تصديق"],
    "adab": ["ادب", "اخلاق", "بر", "صلة", "رحم", "معاملة", "احسان"],
    "lonceng": ["صلصلة", "جرس", "صوت", "حديد", "شديد"],
    "mimpi": ["رؤيا", "منام", "صادقة", "صالحة", "نوم"],
    "hira": ["حراء", "غار", "تعبد", "تحنث", "جبل"],
    "jibril": ["جبريل", "ملك", "روح", "قدس", "اقرا"],
    "wasiat": ["وصية", "عهد", "ميراث", "حق"],
    "taubat": ["توبة", "استغفار", "ندم", "رجوع", "مغفرة"],
    "hijrah": ["هجرة", "مهاجر", "مدينة", "حبشة", "ترك"],
    "itikaf": ["اعتكاف", "مسجد", "عشر", "اواخر", "رمضان"],
}


def detect_language(text: str) -> str:
    """Mendeteksi apakah teks berbahasa Arab, Indonesia, atau campuran."""
    if not text:
        return "id"
    
    arabic_chars = len(re.findall(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", text))
    latin_chars = len(re.findall(r"[a-zA-Z]", text))

    total = arabic_chars + latin_chars
    if total == 0:
        return "id"
    
    ar_ratio = arabic_chars / total
    if ar_ratio >= 0.70:
        return "ar"
    elif ar_ratio <= 0.20:
        return "id"
    return "mixed"


def generate_multilingual_embedding(text: str, dim: int = 256) -> list[float]:
    """
    Menghasilkan representasi vektor semantik multilingual (256-dimensi).
    Menggabungkan fitur n-gram leksikal dengan pemetaan konsep semantik Arab ↔ Indonesia,
    lalu dinormalisasi L2 agar cosine similarity = dot product.
    """
    clean_text = text.lower().strip()
    norm_ar = normalize_arabic(clean_text)
    
    vec = [0.0] * dim
    
    # 1. Ekstraksi token kata & karakter tri-gram
    words = re.findall(r"[\w\u0600-\u06FF]+", clean_text)
    for w in words:
        # Hashing fitur kata ke ruang vektor
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        vec[idx] += sign * 1.5

        # Cross-lingual expansion jika kata ada di konsep map
        w_norm = normalize_arabic(w)
        for id_concept, ar_concepts in MULTILINGUAL_CONCEPT_MAP.items():
            if id_concept in w or any(ac in w_norm for ac in ar_concepts):
                concept_hash = int(hashlib.sha256(id_concept.encode("utf-8")).hexdigest(), 16)
                c_idx = concept_hash % dim
                c_sign = 1.0 if ((concept_hash >> 8) & 1) == 0 else -1.0
                vec[c_idx] += c_sign * 2.5

    # 2. Karakter tri-gram untuk menangkap morfologi Arab & kata berimbuhan Indonesia
    for i in range(len(norm_ar) - 2):
        tri = norm_ar[i : i + 3]
        h_tri = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
        idx_tri = h_tri % dim
        sign_tri = 1.0 if ((h_tri >> 8) & 1) == 0 else -1.0
        vec[idx_tri] += sign_tri * 0.8

    # 3. L2 Normalization
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0.0:
        vec = [round(v / norm, 6) for v in vec]
    return vec


def split_text_into_chunks(text: str, max_chars: int = 900, overlap: int = 150) -> list[str]:
    """Membagi teks panjang menjadi beberapa potongan chunk bertumpang tindih (sliding window)."""
    clean = text.strip()
    if len(clean) <= max_chars:
        return [clean]

    chunks = []
    start = 0
    while start < len(clean):
        end = min(start + max_chars, len(clean))
        if end < len(clean):
            # Potong pada akhir kalimat atau spasi terdekat
            split_pos = clean.rfind("\n", start + overlap, end)
            if split_pos == -1:
                split_pos = clean.rfind(" ", start + overlap, end)
            if split_pos != -1 and split_pos > start:
                end = split_pos

        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(clean):
            break
        start = max(start + 1, end - overlap)

    return chunks
