import re
from typing import Any
from pydantic import BaseModel

from app.services.arabic_normalizer import normalize_arabic

ARABIC_DIGITS = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩",
    "0123456789",
)

EXPLICIT_NUMBER_PATTERNS = [
    (r"حَدِيثُ?\s*(?:رَقْمُ?)?\s*(\d+)", "explicit_number", 0.95),
    (r"الْحَدِيثُ?\s*(?:رَقْمُ?)?\s*(\d+)", "explicit_number", 0.95),
    (r"رَقْمُ?\s*(\d+)", "explicit_number", 0.85),
    (r"ح\s*(\d+)", "short_number", 0.80),
]

MATN_QUOTE_PATTERNS = [
    (r"قَوْلُهُ\s*\((.*?)\)", "quote_parenthesis", 0.92),
    (r"قوله\s*\((.*?)\)", "quote_parenthesis", 0.92),
    (r"قَوْلُهُ\s+([^\.\,\;\:\n]+)", "quote_statement", 0.80),
    (r"قوله\s+([^\.\,\;\:\n]+)", "quote_statement", 0.80),
]

SAHABAH_PATTERNS = [
    (r"عُمَرَ?\s+بْنِ?\s+الْخَطَّابِ?", "عمر بن الخطاب", 1),
    (r"عَائِشَةَ?", "عائشة", 2),
    (r"أَبِي\s+هُرَيْرَةَ?", "أبو هريرة", None),
    (r"ابْنِ?\s+عُمَرَ?", "ابن عمر", None),
    (r"ابْنِ?\s+عَبَّاسٍ?", "ابن عباس", None),
    (r"أَنَسِ?\s+بْنِ?\s+مَالِكٍ?", "أنس بن مالك", None),
    (r"جَابِرِ?\s+بْنِ?\s+عَبْدِ\s+اللَّهِ", "جابر بن عبد الله", None),
]


def normalize_digits(text: str) -> str:
    """Mengonversi digit angka Arab (٠-٩) menjadi angka Latin (0-9)."""
    return text.translate(ARABIC_DIGITS)


class HadithReference(BaseModel):
    hadith_number: int | None = None
    matched_text: str | None = None
    reference_type: str = "unknown"
    confidence: float = 0.0
    evidence: dict[str, Any] = {}


def detect_hadith_references(raw_text: str, normalized_text: str | None = None) -> list[HadithReference]:
    """Mendeteksi referensi hadis eksplisit, kutipan matan, dan perawi sahabat dari teks syarah."""
    norm_text = normalized_text or normalize_arabic(raw_text)
    text_with_latin_digits = normalize_digits(raw_text)
    results: list[HadithReference] = []

    # 1. Deteksi Nomor Hadis Eksplisit
    for pattern, ref_type, conf in EXPLICIT_NUMBER_PATTERNS:
        matches = re.finditer(pattern, text_with_latin_digits)
        for m in matches:
            num = int(m.group(1))
            if 1 <= num <= 7008:
                results.append(
                    HadithReference(
                        hadith_number=num,
                        matched_text=m.group(0),
                        reference_type=ref_type,
                        confidence=conf,
                        evidence={
                            "pattern": pattern,
                            "raw_match": m.group(0),
                            "number": num,
                        },
                    )
                )

    # 2. Deteksi Kutipan Matan (Qawluhu ...)
    for pattern, ref_type, conf in MATN_QUOTE_PATTERNS:
        matches = re.finditer(pattern, raw_text)
        for m in matches:
            quote = m.group(1).strip()
            if len(quote) >= 4:
                results.append(
                    HadithReference(
                        hadith_number=None,
                        matched_text=quote,
                        reference_type=ref_type,
                        confidence=conf,
                        evidence={
                            "quote_raw": quote,
                            "quote_normalized": normalize_arabic(quote),
                            "pattern": pattern,
                        },
                    )
                )

    # 3. Deteksi Sahabat
    for pattern, name, default_num in SAHABAH_PATTERNS:
        if re.search(pattern, raw_text):
            results.append(
                HadithReference(
                    hadith_number=default_num,
                    matched_text=name,
                    reference_type="sahabah_mention",
                    confidence=0.75 if default_num else 0.50,
                    evidence={
                        "sahabah_name": name,
                    },
                )
            )

    return results
