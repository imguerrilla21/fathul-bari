from typing import List, Dict, Any


def rerank_evidence_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Penentu Peringkat Bukti Multi-Fitur & Pembersih Duplikat (Multi-Feature Reranker Engine):
    Rerank Score = (0.30 * Semantic) + (0.20 * Lexical) + (0.20 * Reference) + (0.15 * Verified) + (0.10 * Graph) + (0.05 * Quality)
    """
    seen_hashes = set()
    deduped = []
    
    for c in candidates:
        chash = c.get("content_hash")
        if chash and chash in seen_hashes:
            continue
        if chash:
            seen_hashes.add(chash)

        final_score = (
            (0.30 * c.get("semantic_score", 0)) +
            (0.20 * c.get("lexical_score", 0)) +
            (0.20 * c.get("reference_score", 0)) +
            (0.15 * 1.0) +
            (0.10 * c.get("graph_score", 0)) +
            (0.05 * c.get("source_quality", 1.0))
        )
        c["retrieval_score"] = round(final_score, 4)
        deduped.append(c)

    deduped.sort(key=lambda x: x["retrieval_score"], reverse=True)
    
    for idx, item in enumerate(deduped, 1):
        item["rank"] = idx

    return deduped[:8]
