import re
from typing import Dict, Any, List, Optional
from app.services.arabic_normalizer import normalize_arabic

STOPWORDS_AR = {"في", "من", "عن", "إلى", "على", "حتى", "أن", "إن", "كان", "قال", "ثم", "أو", "مع"}


def normalize_arabic_v2(text: str) -> str:
    """
    Normalisasi Bahasa Arab v2:
    Diacritics removal, Unicode normalization, Alef/Ya/Ta Marbuta handling, Tatweel removal, Punctuation & Whitespace cleanup.
    """
    if not text:
        return ""
    
    res = normalize_arabic(text)
    res = re.sub(r'[\u0640\u064B-\u065F\u0670]', '', res)  # Tatweel & Harakat
    res = re.sub(r'[إأآا]', 'ا', res)
    res = re.sub(r'ى', 'ي', res)
    res = re.sub(r'ة', 'ه', res)
    res = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', res)
    res = re.sub(r'\s+', ' ', res).strip()

    return res


def tokenize_and_lemmatize(text: str) -> Dict[str, Any]:
    """
    Tokenisasi dan lematisasi teks Arab tanpa mengubah teks asli.
    """
    norm = normalize_arabic_v2(text)
    raw_tokens = norm.split()
    
    # Filter stopwords for search tokens
    search_tokens = [t for t in raw_tokens if t not in STOPWORDS_AR]
    
    # Primitive stemmer/lemma mapping
    lemmas = [re.sub(r'^(ال|بال|لل|فبال)', '', t) for t in search_tokens]

    return {
        "raw_tokens": raw_tokens,
        "search_tokens": search_tokens,
        "lemmas": list(set(lemmas))
    }


def extract_arabic_entities(text: str) -> List[Dict[str, Any]]:
    """
    Pengenal Entitas Teks (NER) khusus teks hadis dan syarah:
    NARRATOR, PROPHET, COMPANION, BOOK_REF, HADITH_REF.
    """
    entities = []
    if not text:
        return entities

    # Narrator pattern: "عن أبي هريرة" / "حدثنا مالك"
    narrator_matches = re.findall(r'(?:عن|حدثنا|أخبرنا)\s+([\u0600-\u06FF\s]+?)(?:رضي|قال|أنه|أن|\.|\b)', text)
    for nm in narrator_matches:
        clean_name = nm.strip()
        if len(clean_name) > 3 and clean_name not in STOPWORDS_AR:
            entities.append({
                "entity_text": clean_name,
                "entity_type": "NARRATOR",
                "confidence": 0.95
            })

    # Prophet pattern
    if "رسول الله" in text or "النبي" in text:
        entities.append({
            "entity_text": "رسول الله صلى الله عليه وسلم",
            "entity_type": "PROPHET",
            "confidence": 0.99
        })

    # Book / Chapter pattern: "كتاب البيوع" / "كتاب بدء الوحي"
    book_matches = re.findall(r'(كتاب\s+[\u0600-\u06FF]+)', text)
    for bm in book_matches:
        entities.append({
            "entity_text": bm.strip(),
            "entity_type": "BOOK_REF",
            "confidence": 0.92
        })

    return entities


def parse_sanad_transmission(text: str) -> List[Dict[str, Any]]:
    """
    Parser mata rantai transmisi sanad (narrator_a -> TRANSMITS_TO -> narrator_b).
    """
    chain = []
    tokens = re.split(r'(حدثنا|أخبرنا|عن|قال)', text)
    
    current_term = "عن"
    current_narrator = ""

    for tok in tokens:
        tok_s = tok.strip()
        if tok_s in {"حدثنا", "أخبرنا", "عن", "قال"}:
            current_term = tok_s
        elif tok_s:
            clean_name = re.sub(r'(رضي الله عنه|رحمه الله)', '', tok_s).strip()
            if len(clean_name) > 3 and clean_name not in STOPWORDS_AR:
                if current_narrator:
                    chain.append({
                        "source": current_narrator,
                        "target": clean_name,
                        "term": current_term
                    })
                current_narrator = clean_name

    return chain


def extract_matn_fingerprint(text: str) -> List[str]:
    """
    Ekstraksi n-gram matn fingerprint untuk substring partial matn matching.
    """
    norm = normalize_arabic_v2(text)
    words = norm.split()
    if len(words) < 3:
        return [norm]
    
    ngrams = []
    for i in range(len(words) - 2):
        ngrams.append(" ".join(words[i:i+3]))
    return ngrams


def resolve_relative_reference(text: str) -> Dict[str, Any]:
    """
    Resolver Rujukan Relatif (cross-reference resolver) untuk pola:
    - "وقد تقدم" ➔ PREVIOUS_REFERENCE
    - "كما سيأتي في كتاب البيوع" ➔ FUTURE_REFERENCE
    - "وفي رواية لمسلم" ➔ HADITH_VARIANT
    """
    if "تقدم" in text or "سبق" in text:
        return {
            "ref_type": "PREVIOUS_REFERENCE",
            "target": "Hadis / Seksi Sebelumnya",
            "confidence": 0.90
        }
    elif "سيأتي" in text:
        book_match = re.search(r'في\s+(كتاب\s+[\u0600-\u06FF]+)', text)
        return {
            "ref_type": "FUTURE_REFERENCE",
            "target": book_match.group(1) if book_match else "Seksi Akan Datang",
            "confidence": 0.88
        }
    elif "رواية" in text:
        return {
            "ref_type": "HADITH_VARIANT",
            "target": "Variasi Riwayat Hadis",
            "confidence": 0.94
        }
    
    return {
        "ref_type": "DIRECT_REFERENCE",
        "target": "Rujukan Langsung",
        "confidence": 0.95
    }
