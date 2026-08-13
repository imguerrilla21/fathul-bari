from sqlalchemy.orm import Session
from app.models.verification import ReviewDiscussionEntity

def add_discussion_message(db: Session, target_type: str, target_id: str, author_id: str, message: str):
    discussion = ReviewDiscussionEntity(
        target_type=target_type,
        target_id=target_id,
        author_id=author_id,
        message=message
    )
    db.add(discussion)
    db.commit()
    db.refresh(discussion)
    return discussion
