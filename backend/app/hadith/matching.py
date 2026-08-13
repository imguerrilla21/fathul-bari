from typing import Dict, Any

def calculate_variant_similarity(variant_a: str, variant_b: str) -> Dict[str, Any]:
    """
    Calculates the similarity between two Hadith variants to determine if they are related.
    Uses basic lexical overlap for demonstration. A real system uses embeddings, lemma overlap, etc.
    """
    # Simple tokenization by whitespace
    tokens_a = set(variant_a.split())
    tokens_b = set(variant_b.split())
    
    if not tokens_a or not tokens_b:
        return {"relation": "UNRELATED", "score": 0.0}
        
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    
    jaccard_score = len(intersection) / len(union)
    
    # Matching heuristics
    if jaccard_score > 0.90:
        relation = "MATCH"
    elif jaccard_score > 0.70:
        relation = "POSSIBLE_VARIANT"
    elif jaccard_score > 0.40:
        relation = "RELATED"
    else:
        relation = "UNRELATED"
        
    return {
        "relation": relation,
        "score": round(jaccard_score, 4),
        "metrics": {
            "matn_exact": jaccard_score, # Mocking actual exact match
            "lexical_similarity": jaccard_score,
            "semantic_similarity": jaccard_score + 0.05 # Mocked semantic boost
        }
    }
