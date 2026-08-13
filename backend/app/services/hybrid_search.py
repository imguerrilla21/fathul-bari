import json
import logging
import math
import re
import time
import uuid
from typing import Any
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk, RetrievalLog
from app.models.hadith import Hadith
from app.models.sharh import HadithSharhLink, SharhSection
from app.services.arabic_normalizer import normalize_arabic
from app.services.hybrid_chunker import (
    MULTILINGUAL_CONCEPT_MAP,
    detect_language,
    generate_multilingual_embedding,
)

logger = logging.getLogger("hybrid_search")

# Daftar stop words yang tidak boleh mendominasi penilaian BM25
STOP_WORDS = {
    # Indonesia
    "dan", "atau", "di", "ke", "dari", "dalam", "yang", "untuk", "pada", "adalah", "itu", "ini",
    "dengan", "sebagai", "oleh", "secara", "karena", "tentang", "bagaimana", "mengapa", "apa",
    "orang", "seseorang", "diri", "lain",
    # Arab
    "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "ذلك", "تلك", "هو", "هي", "أن", "إن",
    "كان", "كانت", "يكون", "ما", "لا", "لم", "لن", "ثم", "أو", "إذا", "كل", "قال", "قالت",
}


def dot_product(v1: list[float], v2: list[float]) -> float:
    """Menghitung dot product antara dua vektor unit (cosine similarity)."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))


def strip_arabic_prefixes(word: str) -> list[str]:
    """Menghasilkan variasi kata Arab dengan/tanpa awalan (al-, wa-, fa-, bi-, li-)."""
    norm = normalize_arabic(word)
    variations = {norm}
    
    if norm.startswith("ال") and len(norm) > 3:
        variations.add(norm[2:])
        variations.add("ب" + norm[2:])
        variations.add("و" + norm[2:])
        variations.add("ف" + norm[2:])

    for prefix in ["وال", "فال", "بال", "كال", "لل"]:
        if norm.startswith(prefix) and len(norm) > 4:
            variations.add(norm[len(prefix):])
            variations.add("ال" + norm[len(prefix):])

    for prefix in ["و", "ف", "ب", "ل", "ك"]:
        if norm.startswith(prefix) and len(norm) > 3:
            variations.add(norm[1:])

    if norm.endswith("ة"):
        variations.add(norm[:-1] + "ه")
        variations.add(norm[:-1])
    elif norm.endswith("ات") and len(norm) > 3:
        variations.add(norm[:-2] + "ة")
        variations.add(norm[:-2])

    return list(variations)


def expand_query_multilingual(query: str) -> tuple[list[str], list[str]]:
    """
    Melakukan query expansion lintas-bahasa Indonesia <-> Arab.
    Mengembalikan (content_terms, expanded_concepts).
    """
    q_lower = query.lower()
    raw_words = [w for w in re.findall(r"[\w\u0600-\u06FF]+", q_lower) if len(w) > 1 and w not in STOP_WORDS]
    
    content_terms = list(set(raw_words))
    expanded = set(content_terms)

    for word in content_terms:
        for var in strip_arabic_prefixes(word):
            if var not in STOP_WORDS:
                expanded.add(var)

        for id_concept, ar_concepts in MULTILINGUAL_CONCEPT_MAP.items():
            if id_concept in word or word in id_concept:
                expanded.add(id_concept)
                for ac in ar_concepts:
                    if ac not in STOP_WORDS:
                        expanded.add(ac)
                        for var_ac in strip_arabic_prefixes(ac):
                            if var_ac not in STOP_WORDS:
                                expanded.add(var_ac)

            norm_w = normalize_arabic(word)
            if any(ac in norm_w or norm_w in ac for ac in ar_concepts):
                expanded.add(id_concept)
                for ac in ar_concepts:
                    if ac not in STOP_WORDS:
                        expanded.add(ac)
                        for var_ac in strip_arabic_prefixes(ac):
                            if var_ac not in STOP_WORDS:
                                expanded.add(var_ac)

    return content_terms, list(expanded)


def calculate_bm25_score(content_terms: list[str], expanded_terms: list[str], chunk_text: str, chunk_norm: str) -> float:
    """Menghitung skor kecocokan leksikal BM25 dengan penalti stop words dan bobot istilah khusus."""
    if not content_terms or not chunk_text:
        return 0.0

    c_lower = chunk_text.lower()
    c_norm = chunk_norm.lower()

    score = 0.0
    matched_core_terms = 0

    # 1. Cek kecocokan istilah inti (content_terms)
    for term in content_terms:
        term_norm = normalize_arabic(term)
        count = c_lower.count(term)
        if term_norm:
            count += c_norm.count(term_norm)

        if count > 0:
            matched_core_terms += 1
            # Bobot kata inti
            term_weight = 2.0 + (0.2 * min(6, len(term)))
            tf_score = (count / (count + 1.2)) * term_weight
            score += tf_score

    # 2. Cek kecocokan istilah hasil ekspansi konsep
    for term in expanded_terms:
        if term in content_terms:
            continue
        term_norm = normalize_arabic(term)
        count = c_lower.count(term)
        if term_norm:
            count += c_norm.count(term_norm)

        if count > 0:
            tf_score = (count / (count + 1.2)) * 1.2
            score += tf_score

    if not content_terms:
        return 0.0

    coverage = matched_core_terms / len(content_terms)
    final_score = (score * 0.25) + (coverage * 0.75)
    return min(1.0, round(final_score, 4))


def hybrid_search(
    db: Session,
    query: str,
    retrieval_mode: str = "research",
    volume: int | None = None,
    limit: int = 10,
    verified_only: bool = False,
) -> dict[str, Any]:
    """
    Eksekusi Hybrid Search: BM25 Lexical + Vector Semantic + Reciprocal Rank Fusion + Reranker.
    Mendukung mode: 'research', 'study', 'general'.
    """
    start_time = time.perf_counter()

    clean_query = query.strip()
    query_lang = detect_language(clean_query)
    content_terms, expanded_terms = expand_query_multilingual(clean_query)
    query_vector = generate_multilingual_embedding(clean_query)

    match_num = re.search(r"(?:hadis|hadits|no\.?|#)\s*(\d+)", clean_query, re.IGNORECASE)
    query_hadith_num = int(match_num.group(1)) if match_num else None

    # 1. Ambil candidate chunks dari database
    stmt = select(DocumentChunk)
    if volume:
        stmt = stmt.where(DocumentChunk.volume == volume)

    chunks = list(db.scalars(stmt))
    if not chunks:
        latency = (time.perf_counter() - start_time) * 1000.0
        return {
            "query": query,
            "query_language": query_lang,
            "retrieval_mode": retrieval_mode,
            "total_candidates": 0,
            "results": [],
            "latency_ms": round(latency, 2),
            "message": "Tidak ada dokumen chunk terindeks.",
        }

    # 2. Hitung BM25 Lexical Score dan Vector Cosine Similarity
    scored_items = []
    for ch in chunks:
        # Lexical score
        lex_score = calculate_bm25_score(content_terms, expanded_terms, ch.text, ch.normalized_text)

        # Vector score
        vec_score = 0.0
        if ch.embedding_json:
            try:
                ch_vec = json.loads(ch.embedding_json)
                vec_score = max(0.0, dot_product(query_vector, ch_vec))
            except Exception:
                vec_score = 0.0

        # Exact number boost
        if query_hadith_num and ch.printed_page == query_hadith_num:
            lex_score = min(1.0, lex_score + 0.40)

        # Exact multi-word phrase match
        q_norm = normalize_arabic(clean_query.lower())
        if len(clean_query) >= 8 and (clean_query.lower() in ch.text.lower() or q_norm in ch.normalized_text):
            lex_score = min(1.0, lex_score + 0.35)

        # Full content terms coverage bonus
        if len(content_terms) >= 2:
            all_present = all(
                (ct in ch.text.lower() or normalize_arabic(ct) in ch.normalized_text)
                for ct in content_terms
            )
            if all_present:
                lex_score = min(1.0, lex_score + 0.25)

        if lex_score > 0.05 or vec_score > 0.10:
            scored_items.append({
                "chunk": ch,
                "lexical_score": round(lex_score, 4),
                "vector_score": round(vec_score, 4),
            })

    # 3. Reciprocal Rank Fusion (RRF)
    lex_ranked = sorted(scored_items, key=lambda x: x["lexical_score"], reverse=True)
    for rank, item in enumerate(lex_ranked, start=1):
        item["rank_lex"] = rank

    vec_ranked = sorted(scored_items, key=lambda x: x["vector_score"], reverse=True)
    for rank, item in enumerate(vec_ranked, start=1):
        item["rank_vec"] = rank

    k = 60.0
    for item in scored_items:
        rrf = (1.0 / (k + item.get("rank_lex", 999))) + (1.0 / (k + item.get("rank_vec", 999)))
        item["rrf_score"] = round(rrf, 6)

    # 4. Contextual Reranker dengan Kebijakan Verified-First yang Adil
    for item in scored_items:
        ch: DocumentChunk = item["chunk"]
        norm_rrf = min(1.0, item["rrf_score"] * 30.0)
        
        # Skor gabungan berimbang
        base_score = (
            (item["lexical_score"] * 0.50)
            + (item["vector_score"] * 0.30)
            + (norm_rrf * 0.20)
        )

        # Verified Boost bersyarat: hanya jika memiliki relevansi dasar > 0.25
        if ch.verified and base_score >= 0.25:
            final_relevance = base_score * 1.15
        else:
            final_relevance = base_score

        item["final_relevance"] = min(1.0, round(final_relevance, 4))
        item["relevance_percentage"] = round(item["final_relevance"] * 100.0, 1)

    # Urutkan hasil akhir
    reranked = sorted(scored_items, key=lambda x: x["final_relevance"], reverse=True)

    # 5. Filter berdasarkan Retrieval Mode
    if retrieval_mode == "research" or verified_only:
        verified_results = [it for it in reranked if it["chunk"].verified]
        if verified_results:
            final_selection = verified_results[:limit]
        else:
            final_selection = reranked[:limit]
    else:
        final_selection = reranked[:limit]

    # 6. Susun output DTO
    results = []
    for it in final_selection:
        ch: DocumentChunk = it["chunk"]
        
        hadith_number = None
        if ch.hadith_id:
            h = db.scalar(select(Hadith).where(Hadith.id == ch.hadith_id))
            if h:
                hadith_number = h.external_number

        sharh_title = None
        if ch.sharh_section_id:
            sec = db.scalar(select(SharhSection).where(SharhSection.id == ch.sharh_section_id))
            if sec:
                sharh_title = sec.title

        results.append({
            "chunk_id": str(ch.id),
            "chunk_type": ch.chunk_type,
            "language": ch.language,
            "text": ch.text,
            "snippet": ch.text[:240] + ("..." if len(ch.text) > 240 else ""),
            "volume": ch.volume,
            "printed_page": ch.printed_page,
            "pdf_page": ch.pdf_page,
            "verified": ch.verified,
            "hadith_id": str(ch.hadith_id) if ch.hadith_id else None,
            "hadith_number": hadith_number,
            "sharh_section_id": str(ch.sharh_section_id) if ch.sharh_section_id else None,
            "sharh_title": sharh_title,
            "relevance_score": it["final_relevance"],
            "relevance_percentage": it["relevance_percentage"],
            "lexical_score": it["lexical_score"],
            "vector_score": it["vector_score"],
            "rrf_score": it["rrf_score"],
            "citation_inline": (
                f"[Fathul Bari, Jilid {ch.volume}, Hlm. {ch.printed_page}]"
                if ch.volume and ch.printed_page
                else f"[Shahih Bukhari #{hadith_number}]" if hadith_number else "[Naskah Fathul Bari]"
            ),
        })

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    # 7. Simpan log retrieval
    try:
        log_entry = RetrievalLog(
            id=uuid.uuid4(),
            query=clean_query,
            query_language=query_lang,
            retrieval_mode=retrieval_mode,
            retrieved_chunks_count=len(results),
            retrieved_chunks=json.dumps([r["chunk_id"] for r in results]),
            reranked_chunks=json.dumps([{"id": r["chunk_id"], "score": r["relevance_score"]} for r in results]),
            latency_ms=round(latency_ms, 2),
        )
        db.add(log_entry)
        db.commit()
    except Exception as err:
        logger.warning("Gagal menyimpan log retrieval: %s", err)
        db.rollback()

    return {
        "query": clean_query,
        "query_language": query_lang,
        "expanded_terms": expanded_terms[:10],
        "retrieval_mode": retrieval_mode,
        "total_candidates_found": len(scored_items),
        "results_count": len(results),
        "latency_ms": round(latency_ms, 2),
        "results": results,
    }
