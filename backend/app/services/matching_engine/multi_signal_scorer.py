from typing import Dict, Any


def calculate_hybrid_match_score(
    lexical: float,
    semantic: float,
    reference: float,
    context: float
) -> Dict[str, Any]:
    """
    Kalkulator Skor Hibrida Multi-Sinyal (Multi-Signal Hybrid Scorer):
    Hybrid Score = (0.30 * Lexical) + (0.35 * Semantic) + (0.20 * Reference) + (0.15 * Context)
    """
    confidence_score = (0.30 * lexical) + (0.35 * semantic) + (0.20 * reference) + (0.15 * context)
    confidence_score = round(confidence_score, 4)

    # Confidence Bands Calibration
    if confidence_score >= 0.90:
        band = "HIGH"
    elif confidence_score >= 0.75:
        band = "MEDIUM"
    elif confidence_score >= 0.50:
        band = "LOW"
    else:
        band = "VERY_LOW"

    return {
        "confidence_score": confidence_score,
        "confidence_band": band,
        "lexical_score": lexical,
        "semantic_score": semantic,
        "reference_score": reference,
        "context_score": context
    }


def generate_match_explanation(
    hadith_num: str,
    opening_phrase: str,
    scores: Dict[str, Any]
) -> Dict[str, Any]:
    """Pembuat Penjelasan Bukti Rasional ("Why This Match?" Rationale Explanation Breakdown)."""
    signals = [
        {
            "type": "EXACT_PHRASE",
            "description": f"Ditemukan kecocokan frasa pembuka hadis '{opening_phrase[:40]}...'",
            "score": scores["lexical_score"],
            "matched": bool(scores["lexical_score"] > 0.8)
        },
        {
            "type": "HADITH_REFERENCE",
            "description": f"Ditemukan jangkar referensi nomor hadis #{hadith_num} dalam teks syarah",
            "score": scores["reference_score"],
            "matched": bool(scores["reference_score"] > 0.8)
        },
        {
            "type": "SEMANTIC_VECTOR",
            "description": "Keserupaan makna vektor embedding HNSW",
            "score": scores["semantic_score"],
            "matched": bool(scores["semantic_score"] > 0.8)
        },
        {
            "type": "SECTION_CONTEXT",
            "description": "Kesesuaian konteks bab syarah Fathul Bari",
            "score": scores["context_score"],
            "matched": bool(scores["context_score"] > 0.8)
        }
    ]

    return {
        "matcher_version": "20.1.0",
        "overall_confidence": scores["confidence_score"],
        "confidence_band": scores["confidence_band"],
        "signals": signals,
        "summary": f"Kandidat cocok dengan skor hibrida {scores['confidence_score']} ({scores['confidence_band']})"
    }
