from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.services.workspace.project_service import create_project, get_project
from app.services.workspace.annotation_service import create_annotation, recover_annotation
from app.services.workspace.note_service import create_note, create_bookmark

router = APIRouter(prefix="/api/v1/workspace_engine", tags=["workspace-engine"])

class CreateProjectRequest(BaseModel):
    title: str
    description: Optional[str] = ""

class CreateAnnotationRequest(BaseModel):
    passage_id: str
    selected_text: str
    start_offset: int
    end_offset: int
    anchor_before: str
    anchor_after: str
    comment: str

class CreateNoteRequest(BaseModel):
    content: str

class CreateBookmarkRequest(BaseModel):
    target_type: str
    target_id: str
    title: str

class RecoverAnnotationRequest(BaseModel):
    annotation_id: str
    current_passage_text: str

@router.post("/projects")
def api_create_project(req: CreateProjectRequest, db: Session = Depends(get_db)):
    return create_project(db, title=req.title, description=req.description)

@router.post("/projects/{project_id}/annotations")
def api_create_annotation(project_id: str, req: CreateAnnotationRequest, db: Session = Depends(get_db)):
    return create_annotation(db, project_id, req.selected_text, req.start_offset, req.end_offset, req.anchor_before, req.anchor_after, req.comment)

@router.post("/projects/{project_id}/notes")
def api_create_note(project_id: str, req: CreateNoteRequest, db: Session = Depends(get_db)):
    return create_note(db, project_id, req.content)

@router.post("/projects/{project_id}/bookmarks")
def api_create_bookmark(project_id: str, req: CreateBookmarkRequest, db: Session = Depends(get_db)):
    return create_bookmark(db, project_id, req.target_type, req.target_id, req.title)

@router.post("/annotations/recover")
def api_recover_annotation(req: RecoverAnnotationRequest, db: Session = Depends(get_db)):
    annotation = recover_annotation(db, req.annotation_id, req.current_passage_text)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return {"status": annotation.status, "start_offset": annotation.start_offset, "end_offset": annotation.end_offset}
