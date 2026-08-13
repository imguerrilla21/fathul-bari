import re

ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

PUNCTUATION_REGEX = re.compile(
    r"[،؛؟«»\"'“”‘’\(\)\[\]\{\}\.,:;\-—_/\\]"
)


def normalize_arabic(text: str) -> str:
    """Menormalisasi teks Arab: menghapus harakat, menyamakan alif, ya, kaf, dan spasi."""
    if not text:
        return ""

    # 1. Hapus harakat / tashkeel
    text = ARABIC_DIACRITICS.sub("", text)

    # 2. Samakan bentuk Alif (إ, أ, آ, ٱ -> ا)
    text = re.sub(r"[إأآٱ]", "ا", text)

    # 3. Samakan Alif Maqshurah & Yeh (ى -> ي)
    text = text.replace("ى", "ي")

    # 4. Samakan variasi huruf Persia / Urdu ke Arab standar
    text = text.replace("ک", "ك").replace("ی", "ي").replace("گ", "ك").replace("پ", "ب").replace("چ", "ج")

    # 5. Samakan Ta Marbutah di akhir kata ke Ha jika diperlukan untuk pencarian longgar (opsional: tetap jaga ة atau h)
    # text = text.replace("ة", "ه")

    # 6. Bersihkan tanda baca
    text = PUNCTUATION_REGEX.sub(" ", text)

    # 7. Normalkan spasi
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_arabic_words(text: str) -> list[str]:
    """Mengekstrak daftar kata Arab yang telah dinormalisasi."""
    norm = normalize_arabic(text)
    words = [w for w in norm.split() if len(w) > 1]
    return words


def compute_char_ngrams(text: str, n: int = 3) -> set[str]:
    """Menghasilkan set character n-grams untuk matching fuzzy."""
    norm = normalize_arabic(text).replace(" ", "")
    if len(norm) < n:
        return {norm} if norm else set()
    return {norm[i : i + n] for i in range(len(norm) - n + 1)}


def compute_matn_similarity(query_text: str, target_text: str) -> float:
    """Menghitung skor kesamaan teks Arab antara kutipan syarah dan hadis (0.0 s/d 1.0)."""
    norm_q = normalize_arabic(query_text)
    norm_t = normalize_arabic(target_text)

    if not norm_q or not norm_t:
        return 0.0

    # 1. Exact Substring Match (Kutipan syarah ada persis di dalam matan hadis)
    if norm_q in norm_t:
        # Semakin panjang kutipan relatif terhadap query, semakin tinggi skornya (min 0.92)
        ratio = len(norm_q) / max(len(norm_t), 1)
        return round(min(1.0, 0.90 + (0.10 * min(ratio * 2, 1.0))), 4)

    if norm_t in norm_q:
        return 0.95

    # 2. Token Jaccard Overlap
    words_q = set(extract_arabic_words(norm_q))
    words_t = set(extract_arabic_words(norm_t))

    if not words_q or not words_t:
        return 0.0

    intersection = words_q.intersection(words_t)
    # Jika sebagian besar kata dalam kutipan syarah ditemukan di matan hadis
    recall_q = len(intersection) / len(words_q)
    jaccard = len(intersection) / len(words_q.union(words_t))

    # 3. N-gram Character Similarity
    ngrams_q = compute_char_ngrams(norm_q, 3)
    ngrams_t = compute_char_ngrams(norm_t, 3)
    ngram_jaccard = len(ngrams_q.intersection(ngrams_t)) / max(len(ngrams_q.union(ngrams_t)), 1)

    # Gabungkan metrik (bobot tinggi pada recall_q: kata-kata syarah yang ada di hadis)
    final_score = (recall_q * 0.60) + (jaccard * 0.20) + (ngram_jaccard * 0.20)
    return round(min(1.0, final_score), 4)
