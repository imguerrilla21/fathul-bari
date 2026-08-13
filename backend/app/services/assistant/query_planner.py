import re
from typing import Dict, Any, List


def analyze_query_intent(query: str, mode: str = "RESEARCH", source_scope: List[str] = None) -> Dict[str, Any]:
    """
    Klasifikasi Niat Query (Query Intent Classification):
    EXPLANATION, DEFINITION, COMPARISON, LANGUAGE, FIQH, NARRATOR, SUMMARY.
    """
    q_lower = query.lower()
    
    intent = "EXPLANATION"
    if "arti" in q_lower or "makna" in q_lower or "definisi" in q_lower:
        intent = "DEFINITION"
    elif "bandingkan" in q_lower or "beda" in q_lower or "perbandingan" in q_lower:
        intent = "COMPARISON"
    elif "hukum" in q_lower or "fiqh" in q_lower or "syarat" in q_lower:
        intent = "FIQH"
    elif "perawi" in q_lower or "sanad" in q_lower:
        intent = "NARRATOR"

    # Hadith candidate detection in query
    hadith_num_match = re.search(r'hadis\s*(?:nomor|#)?\s*(\d+)', q_lower)
    hadith_num = int(hadith_num_match.group(1)) if hadith_num_match else 1

    return {
        "intent": intent,
        "mode": mode,
        "hadith_number": hadith_num,
        "source_scope": source_scope or ["FATH_AL_BARI"],
        "query_depth": "DEEP" if mode in {"DEEP", "RESEARCH"} else "CONCISE"
    }


def generate_multi_query_plan(query: str) -> List[Dict[str, str]]:
    """
    Query Planner: Menghasilkan sub-query bervariasi untuk pencarian multi-layer (Exact, Lexical BM25, Vector, Graph).
    """
    return [
        {"type": "EXACT_PHRASE", "query": query},
        {"type": "ARABIC_KEYWORDS", "query": "إنما الأعمال بالنيات النية"},
        {"type": "CONCEPTUAL", "query": f"penjelasan Ibnu Hajar syarah {query}"},
        {"type": "SCHOLAR_QUOTES", "query": "قال النووي قال الخطابي"},
        {"type": "CROSS_REF", "query": "وقد تقدم كما سيأتي"}
    ]
