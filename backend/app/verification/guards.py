from typing import Any

def validate_attribution(claim: Any) -> bool:
    """
    Ensure that an attribution claim is backed by the appropriate evidence type.
    """
    if getattr(claim, 'attribution', None) == "IBN_HAJAR":
        # Requires Fathul Bari evidence
        has_fb = any("Fathul Bari" in ev.get("source", "") for ev in getattr(claim, 'evidence', []))
        if not has_fb:
            return False
    return True

def validate_hadith_grading(claim_text: str, evidence_list: list) -> bool:
    """
    If AI asserts grading (e.g. Sahih), ensure evidence explicitly mentions it.
    """
    grading_keywords = ["sahih", "hasan", "daif", "dhaif", "mawdu"]
    claim_lower = claim_text.lower()
    
    found_gradings = [g for g in grading_keywords if g in claim_lower]
    if not found_gradings:
        return True # Not a grading claim
        
    for g in found_gradings:
        evidence_supports = any(g in str(ev).lower() for ev in evidence_list)
        if not evidence_supports:
            return False
            
    return True

def validate_isnad_chain(chain_nodes: list, graph_service: Any) -> bool:
    """
    Ensure the claimed chain exists in the verified graph.
    """
    if hasattr(graph_service, 'contains_path'):
        return graph_service.contains_path(*chain_nodes)
    return True
