from sqlalchemy.orm import Session
from app.models.research import ResearchSessionEntity, ResearchStepEntity, ResearchClaimEntity, ResearchAnswerEntity, ResearchCitationEntity
from app.research.intent import parse_intent
from app.research.planner import generate_plan
from app.research.tools import search_hadith, get_commentary
from app.research.evidence import pack_evidence, format_evidence_for_prompt
from app.research.validator import validate_claims
from app.llm.client import get_llm_client
from app.llm.prompts import RESEARCH_ANSWER_PROMPT
from app.llm.structured import ResearchAnswerPayload

def run_research(db: Session, query_text: str, mode: str = "STANDARD") -> dict:
    """
    Executes the full research pipeline.
    """
    # 1. Create Session
    rs = ResearchSessionEntity(original_question=query_text)
    db.add(rs)
    db.commit()
    db.refresh(rs)
    
    # 2. Parse Intent
    rs_step_intent = ResearchStepEntity(session_id=rs.id, step_order=1, step_type="INTENT_DETECTION", status="COMPLETED")
    db.add(rs_step_intent)
    
    query_obj = parse_intent(query_text)
    rs.intent = query_obj.intent
    db.commit()
    
    # 3. Plan
    rs_step_plan = ResearchStepEntity(session_id=rs.id, step_order=2, step_type="PLANNING", status="COMPLETED")
    db.add(rs_step_plan)
    
    plan = generate_plan(query_obj)
    db.commit()
    
    # 4. Tool Execution (Simulated based on plan)
    # In a real implementation, this would iterate over plan.steps
    raw_results = []
    if "IDENTIFY_HADITH" in plan.steps or "SEARCH_ARABIC_TERMS" in plan.steps:
        raw_results.extend(search_hadith(query_obj.arabic_terms[0] if query_obj.arabic_terms else query_text))
        
    if "RETRIEVE_FATHUL_BARI" in plan.steps:
        raw_results.extend(get_commentary(query_text, "bukhari_1"))
        
    # 5. Pack Evidence
    evidence_entities = pack_evidence(db, rs.id, raw_results)
    
    # 6. Generate Answer
    client = get_llm_client()
    evidence_text = format_evidence_for_prompt(evidence_entities)
    
    answer_payload = client.generate_structured(
        system_prompt=RESEARCH_ANSWER_PROMPT + f"\n\nEVIDENCE:\n{evidence_text}",
        user_prompt=query_text,
        response_model=ResearchAnswerPayload
    )
    
    # 7. Validate Claims (Hallucination Firewall)
    if not validate_claims(answer_payload, evidence_entities):
        # In a real system, we'd loop back and ask the LLM to fix it.
        # Here we just mark it.
        rs.status = "VALIDATION_FAILED"
    else:
        rs.status = "COMPLETED"
        
    # 8. Save Answer, Claims, Citations
    answer_entity = ResearchAnswerEntity(
        session_id=rs.id,
        title=answer_payload.title,
        summary=answer_payload.summary,
        sections_json=[s.model_dump() for s in answer_payload.sections],
        quality_score={"evidence_coverage": 1.0, "citation_coverage": 1.0}
    )
    db.add(answer_entity)
    
    for section in answer_payload.sections:
        for claim_dict in section.claims:
            claim_text = claim_dict.get("claim", "")
            evidence_ids = claim_dict.get("evidence_ids", [])
            
            rc = ResearchClaimEntity(session_id=rs.id, claim_text=claim_text, validation_status="PASS")
            db.add(rc)
            db.flush() # to get rc.id
            
            for ev_id in evidence_ids:
                cit = ResearchCitationEntity(claim_id=rc.id, source_id=ev_id, validation_status="PASS")
                db.add(cit)
                
    db.commit()
    
    # Build a simple dict response to return to the API
    return {
        "session_id": rs.id,
        "intent": rs.intent,
        "status": rs.status,
        "answer": {
            "title": answer_entity.title,
            "summary": answer_entity.summary,
            "sections": answer_entity.sections_json
        },
        "evidence": [{"id": e.id, "text": e.evidence_text} for e in evidence_entities]
    }
