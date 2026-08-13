from typing import List, Dict, Any, Optional

def perform_hybrid_arabic_search(query: str, source_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Simulates a hybrid Arabic search that combines:
    - Exact phrase match (Weight: 0.30)
    - Lexical (BM25) match (Weight: 0.20)
    - Lemma match (Weight: 0.15)
    - Semantic match (Weight: 0.20)
    - Entity / Root match (Weight: 0.10)
    - Source Priority (Weight: 0.05)
    
    In a real implementation, this would query Elasticsearch/Postgres FTS + Vector DB and rerank.
    """
    
    # Mocking a hybrid search response for the starter
    return {
        "query": query,
        "mode": "hybrid",
        "results": [
            {
                "chunk_id": "FB-V1-P45-C003",
                "match_type": "EXACT + SEMANTIC",
                "score": 0.94,
                "snippet": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"
            },
            {
                "chunk_id": "FB-V1-P46-C010",
                "match_type": "LEMMA",
                "score": 0.72,
                "snippet": "النية محلها القلب"
            },
            {
                "chunk_id": "SB-B01-H001",
                "match_type": "LEXICAL",
                "score": 0.65,
                "snippet": "يقول سمعت عمر بن الخطاب رضي الله عنه على المنبر قال سمعت رسول الله صلى الله عليه وسلم يقول إنما الأعمال بالنيات"
            }
        ],
        "metadata": {
            "exact_score_weight": 0.30,
            "lexical_score_weight": 0.20,
            "lemma_score_weight": 0.15,
            "semantic_score_weight": 0.20,
            "entity_score_weight": 0.10,
            "source_priority_weight": 0.05
        }
    }
