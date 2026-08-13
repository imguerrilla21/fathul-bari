from sqlalchemy.orm import Session
from app.models.research import ResearchAnswerEntity, ResearchClaimEntity

def can_publish_answer(db: Session, answer_id: str) -> bool:
    """
    Publication Gate logic.
    An answer can only be published if all its critical claims have been VERIFIED.
    For this starter logic, we will assume all extracted claims are critical.
    """
    answer = db.query(ResearchAnswerEntity).filter(ResearchAnswerEntity.id == answer_id).first()
    if not answer:
        return False
        
    claims = db.query(ResearchClaimEntity).filter(ResearchClaimEntity.session_id == answer.session_id).all()
    
    for claim in claims:
        # If any claim is not VERIFIED, block publication
        if claim.validation_status != "VERIFIED":
            return False
            
    return True
