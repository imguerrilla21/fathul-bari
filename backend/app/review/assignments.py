from sqlalchemy.orm import Session
from app.models.verification import ReviewAssignmentEntity

def assign_review(db: Session, target_type: str, target_id: str, reviewer_id: str, priority: str = "MEDIUM"):
    assignment = ReviewAssignmentEntity(
        target_type=target_type,
        target_id=target_id,
        reviewer_id=reviewer_id,
        priority=priority,
        status="PENDING"
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment
