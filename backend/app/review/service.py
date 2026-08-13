from sqlalchemy.orm import Session
from app.models.research import ResearchClaimEntity
from app.models.verification import VerificationRecordEntity, ClaimVersionEntity
from app.audit.events import log_audit_event
from app.review.permissions import require_permission

class ReviewService:
    def verify_claim(self, db: Session, claim_id: str, reviewer_id: str, reviewer_role: str, notes: str = ""):
        require_permission(reviewer_role, "verify_claim")
        
        claim = db.query(ResearchClaimEntity).filter(ResearchClaimEntity.id == claim_id).first()
        if not claim:
            raise ValueError("Claim not found")
            
        old_status = claim.validation_status
        new_status = "VERIFIED"
        
        claim.validation_status = new_status
        
        # Record the verification
        record = VerificationRecordEntity(
            target_type="CLAIM",
            target_id=claim_id,
            reviewer_id=reviewer_id,
            decision="VERIFY",
            reason="Source supports the claim",
            notes=notes,
            previous_status=old_status,
            new_status=new_status
        )
        db.add(record)
        
        # Immutable audit log
        log_audit_event(
            db=db,
            actor_id=reviewer_id,
            action="VERIFY_CLAIM",
            entity_type="ResearchClaimEntity",
            entity_id=claim_id,
            before_state={"validation_status": old_status},
            after_state={"validation_status": new_status},
            reason="Reviewer verified the claim"
        )
        
        db.commit()
        return claim
        
    def reject_claim(self, db: Session, claim_id: str, reviewer_id: str, reviewer_role: str, reason: str):
        require_permission(reviewer_role, "verify_claim")
        
        claim = db.query(ResearchClaimEntity).filter(ResearchClaimEntity.id == claim_id).first()
        if not claim:
            raise ValueError("Claim not found")
            
        old_status = claim.validation_status
        new_status = "REJECTED"
        
        claim.validation_status = new_status
        
        # Record the verification
        record = VerificationRecordEntity(
            target_type="CLAIM",
            target_id=claim_id,
            reviewer_id=reviewer_id,
            decision="REJECT",
            reason=reason,
            previous_status=old_status,
            new_status=new_status
        )
        db.add(record)
        
        log_audit_event(
            db=db,
            actor_id=reviewer_id,
            action="REJECT_CLAIM",
            entity_type="ResearchClaimEntity",
            entity_id=claim_id,
            before_state={"validation_status": old_status},
            after_state={"validation_status": new_status},
            reason=reason
        )
        
        db.commit()
        return claim

    def correct_claim(self, db: Session, claim_id: str, reviewer_id: str, reviewer_role: str, corrected_text: str, reason: str):
        require_permission(reviewer_role, "verify_claim")
        
        claim = db.query(ResearchClaimEntity).filter(ResearchClaimEntity.id == claim_id).first()
        if not claim:
            raise ValueError("Claim not found")
            
        old_text = claim.claim_text
        old_status = claim.validation_status
        
        # Save old version
        # Assuming version 1 for simplicity in starter
        version_record = ClaimVersionEntity(
            claim_id=claim_id,
            version=1,
            claim_text=old_text,
            author_id=reviewer_id,
            change_reason=reason
        )
        db.add(version_record)
        
        claim.claim_text = corrected_text
        claim.validation_status = "CORRECTED"
        
        record = VerificationRecordEntity(
            target_type="CLAIM",
            target_id=claim_id,
            reviewer_id=reviewer_id,
            decision="CORRECT",
            reason=reason,
            previous_status=old_status,
            new_status="CORRECTED"
        )
        db.add(record)
        
        log_audit_event(
            db=db,
            actor_id=reviewer_id,
            action="CORRECT_CLAIM",
            entity_type="ResearchClaimEntity",
            entity_id=claim_id,
            before_state={"validation_status": old_status, "claim_text": old_text},
            after_state={"validation_status": "CORRECTED", "claim_text": corrected_text},
            reason=reason
        )
        
        db.commit()
        return claim
