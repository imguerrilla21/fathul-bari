from sqlalchemy.orm import Session
from app.models.workspace import ResearchNote, ResearchBookmark
import uuid

def create_note(db: Session, project_id: str, content: str):
    note = ResearchNote(
        project_id=uuid.UUID(project_id),
        content=content
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

def create_bookmark(db: Session, project_id: str, target_type: str, target_id: str, title: str):
    bookmark = ResearchBookmark(
        project_id=uuid.UUID(project_id),
        target_type=target_type,
        target_id=target_id,
        title=title
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark
