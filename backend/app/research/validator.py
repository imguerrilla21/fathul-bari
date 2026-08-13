from typing import List
from app.llm.structured import ResearchAnswerPayload
from app.models.research import ResearchEvidenceEntity

def validate_claims(answer: ResearchAnswerPayload, evidence: List[ResearchEvidenceEntity]) -> bool:
    """
    The Hallucination Firewall.
    Checks if all claims made in the answer refer to valid evidence IDs.
    """
    valid_evidence_ids = {ev.id for ev in evidence}
    
    for section in answer.sections:
        for claim_dict in section.claims:
            # We used dicts in the ResearchAnswerSection to simplify the generic LLM parsing.
            evidence_ids = claim_dict.get("evidence_ids", [])
            if not evidence_ids:
                return False # Unsupported claim
                
            for ev_id in evidence_ids:
                if ev_id not in valid_evidence_ids:
                    return False # Invented evidence ID
                    
    return True
