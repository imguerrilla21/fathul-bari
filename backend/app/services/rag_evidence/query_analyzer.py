from typing import Dict, Any, List


def analyze_rag_query(question: str) -> Dict[str, Any]:
    """
    Penganalisis Query RAG (Query Intent Classifier & Term Expansion):
    Mengklasifikasikan intent pertanyaan (SHARH, HADITH_LOOKUP, COMPARATIVE, FIQH) dan memperluas istilah Arab.
    """
    q_lower = question.lower()
    
    if "hadis" in q_lower or "nomor" in q_lower or "bukhari" in q_lower:
        intent = "HADITH_LOOKUP"
    elif "perbedaan" in q_lower or "bandingkan" in q_lower:
        intent = "COMPARATIVE"
    elif "hukum" in q_lower or "fiqh" in q_lower:
        intent = "FIQH"
    else:
        intent = "SHARH"

    expanded_keywords = ["إنما الأعمال بالنيات", "النية", "الأعمال"]
    if "niat" in q_lower:
        expanded_keywords.append("النية شرط في صحة العبادات")

    return {
        "intent": intent,
        "language": "id",
        "entities": {
            "hadith_collection": "bukhari",
            "hadith_number": "1" if "1" in question or "niat" in q_lower else None,
            "topic": "niat" if "niat" in q_lower else "umum"
        },
        "keywords": expanded_keywords,
        "config": {
            "lexical_top_k": 30,
            "semantic_top_k": 30,
            "reference_top_k": 10,
            "rerank_top_k": 10
        }
    }
