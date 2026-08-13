import re
from typing import Dict, Any
from app.services.arabic_normalizer import normalize_arabic


def evaluate_text_quality(text: str, ocr_confidence: float = 0.95) -> Dict[str, Any]:
    """
    Evaluasi kualitas teks berdasarkan signal:
    - Arabic character ratio (30%)
    - Text length score (20%)
    - OCR confidence (30%)
    - Noise score (20%)
    """
    if not text:
        return {
            "quality_score": 0.0,
            "arabic_ratio": 0.0,
            "ocr_score": ocr_confidence,
            "noise_score": 0.0,
            "status": "POOR"
        }

    total_chars = len(text)
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    arabic_ratio = arabic_chars / max(1, total_chars)

    length_score = min(1.0, total_chars / 500.0)
    
    # Noise calculation: ratio of non-alphanumeric, non-Arabic, non-space characters
    clean_chars = len(re.findall(r'[\u0600-\u06FFa-zA-Z0-9\s]', text))
    noise_score = clean_chars / max(1, total_chars)

    quality_score = round(
        (arabic_ratio * 0.30) +
        (length_score * 0.20) +
        (ocr_confidence * 0.30) +
        (noise_score * 0.20),
        4
    )

    status = "EXCELLENT" if quality_score >= 0.85 else ("GOOD" if quality_score >= 0.70 else "NEEDS_REVIEW")

    return {
        "quality_score": quality_score,
        "arabic_ratio": round(arabic_ratio, 4),
        "length_score": round(length_score, 4),
        "ocr_score": round(ocr_confidence, 4),
        "noise_score": round(noise_score, 4),
        "status": status
    }


def generate_triple_text_representations(text: str) -> Dict[str, str]:
    """
    Menghasilkan 3 representasi teks:
    1. raw_text: Teks asli sumber (citation/source view)
    2. normalized_text: Teks ternormalisasi Unicode (processing/matching)
    3. search_text: Teks pencarian tanpa harakat & tanda baca (BM25 retrieval)
    """
    raw_text = text or ""
    norm_text = normalize_arabic(raw_text)

    # Search representation: remove remaining punctuation & symbols
    search_text = re.sub(r'[^\w\s\u0600-\u06FF]', '', norm_text)
    search_text = re.sub(r'\s+', ' ', search_text).strip()

    return {
        "raw_text": raw_text,
        "normalized_text": norm_text,
        "search_text": search_text
    }
