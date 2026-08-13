from sqlalchemy.orm import Session
from app.models.attribution import AttributionAuditEntity

def validate_attribution(db: Session, claim_id: str, detected_speaker_id: str, expected_speaker_id: str):
    status = "VERIFIED"
    if detected_speaker_id != expected_speaker_id:
        status = "FALSE_ATTRIBUTION"
        
    audit = AttributionAuditEntity(
        claim_id=claim_id,
        detected_speaker_id=detected_speaker_id,
        expected_speaker_id=expected_speaker_id,
        status=status,
        confidence=0.95
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    
    return audit
