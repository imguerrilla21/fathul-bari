from sqlalchemy.orm import Session
from app.models.attribution import AttributedClaimEntity
from app.services.attribution.scholar_service import get_scholar_by_alias

def analyze_attribution(db: Session, passage_id: str, text: str):
    # Simulated ML/LLM analysis for speaker extraction
    # E.g. "وقال النووي: ..."
    detected_speaker = "النووي"
    relation = "QUOTES"
    
    if "قال النووي" in text:
        detected_speaker = "النووي"
        relation = "QUOTES"
    elif "قال ابن حجر" in text:
        detected_speaker = "ابن حجر"
        relation = "DIRECT_QUOTE"
        
    scholar = get_scholar_by_alias(db, detected_speaker)
    
    return {
        "speaker": {
            "id": scholar.id if scholar else None,
            "name": scholar.canonical_name if scholar else detected_speaker,
            "confidence": 0.98 if scholar else 0.50
        },
        "relation": relation,
        "passage_id": passage_id
    }

def get_attribution_graph(db: Session, passage_id: str):
    claims = db.query(AttributedClaimEntity).filter(AttributedClaimEntity.passage_id == passage_id).all()
    
    nodes = []
    edges = []
    
    for claim in claims:
        # Avoid duplicate nodes
        if not any(n["id"] == claim.speaker_id for n in nodes):
            nodes.append({"id": claim.speaker_id, "type": "PERSON"})
        if not any(n["id"] == claim.reporter_id for n in nodes):
            nodes.append({"id": claim.reporter_id, "type": "PERSON"})
            
        edges.append({
            "from": claim.reporter_id,
            "to": claim.speaker_id,
            "type": claim.relation
        })
        
    return {"nodes": nodes, "edges": edges}
