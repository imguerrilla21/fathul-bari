from sqlalchemy.orm import Session
from app.models.workspace import ResearchAnnotation
import hashlib
import uuid

def generate_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def create_annotation(db: Session, project_id: str, selected_text: str, start_offset: int, end_offset: int, anchor_before: str, anchor_after: str, comment: str):
    annotation = ResearchAnnotation(
        project_id=uuid.UUID(project_id),
        selected_text=selected_text,
        start_offset=start_offset,
        end_offset=end_offset,
        text_hash=generate_text_hash(selected_text),
        anchor_before=anchor_before,
        anchor_after=anchor_after,
        comment=comment,
        annotation_type="IMPORTANT",
        status="ACTIVE"
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return annotation

def recover_annotation(db: Session, annotation_id: str, current_passage_text: str):
    # This simulates Annotation Recovery when OCR text offsets change
    annotation = db.query(ResearchAnnotation).filter(ResearchAnnotation.id == uuid.UUID(annotation_id)).first()
    if not annotation:
        return None
        
    # Example heuristic recovery:
    # We look for the selected_text near the anchor_before
    search_context = annotation.anchor_before + annotation.selected_text + annotation.anchor_after
    
    # Simple simulated recovery
    idx = current_passage_text.find(annotation.selected_text)
    if idx != -1 and idx != annotation.start_offset:
        annotation.start_offset = idx
        annotation.end_offset = idx + len(annotation.selected_text)
        annotation.status = "RESTORED"
        db.commit()
        db.refresh(annotation)
    
    return annotation
