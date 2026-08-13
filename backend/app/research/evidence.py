from typing import List, Dict, Any
from app.models.research import ResearchEvidenceEntity
from sqlalchemy.orm import Session
import uuid

def pack_evidence(session: Session, research_session_id: str, tool_results: List[Dict[str, Any]]) -> List[ResearchEvidenceEntity]:
    """
    Takes raw tool results, converts them into ResearchEvidenceEntity,
    persists them, and returns them for LLM context.
    """
    evidence_entities = []
    
    for idx, res in enumerate(tool_results):
        evidence_id = f"ev_mock_{research_session_id}_{idx + 1}"
        evidence = ResearchEvidenceEntity(
            id=evidence_id,
            session_id=research_session_id,
            source_id=res.get("id"),
            evidence_text=res.get("text"),
            evidence_type="PRIMARY_HADITH" if "hadith" in res.get("source", "").lower() else "PRIMARY_COMMENTARY",
            relevance_score=0.95,
            confidence=1.0,
            metadata_json={"source": res.get("source")}
        )
        session.add(evidence)
        evidence_entities.append(evidence)
        
    session.commit()
    return evidence_entities

def format_evidence_for_prompt(evidence: List[ResearchEvidenceEntity]) -> str:
    """Formats evidence objects into a string block for the LLM prompt."""
    output = ""
    for ev in evidence:
        output += f"--- EVIDENCE_ID: {ev.id} ---\n"
        output += f"SOURCE: {ev.metadata_json.get('source', 'Unknown')}\n"
        output += f"TEXT: {ev.evidence_text}\n\n"
    return output
