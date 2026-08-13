from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.research_workspace_v2 import (
    ResearchWorkspaceEntity, ResearchNoteEntity, SourceHighlightEntity, ResearchFindingEntity
)
from app.services.research_workspace.workspace_service import create_workspace_with_defaults
from app.services.research_workspace.highlight_service import create_text_highlight
from app.services.research_workspace.comparison_engine import compare_text_variants
from app.services.research_workspace.findings_service import verify_research_finding
from app.services.research_workspace.context_aware_ai import ask_context_aware_ai

router = APIRouter(prefix="/api/v1/workspaces-v2", tags=["research-workspace-v2"])


class CreateWorkspaceRequest(BaseModel):
    name: Optional[str] = "Ruang Kerja Hadis Niat"
    description: Optional[str] = "Penelitian Syarah Hadis Niat Fathul Bari"


class CreateNoteRequest(BaseModel):
    title: str
    content: str
    note_type: Optional[str] = "OBSERVATION"


class CreateHighlightRequest(BaseModel):
    page_id: str
    selected_text: str
    start_offset: Optional[int] = 0
    end_offset: Optional[int] = 40
    color: Optional[str] = "yellow"


class CompareRequest(BaseModel):
    text1: Optional[str] = "عن عمر بن الخطاب قال سمعت رسول الله يقول إنما الأعمال بالنيات"
    text2: Optional[str] = "عن عمر بن الخطاب قال سمعت رسول الله يقول إنما الأعمال بالنية"


class AskAIRequest(BaseModel):
    question: str
    selected_text: Optional[str] = "قوله إنما الأعمال بالنيات"


@router.post("")
def create_workspace(req: CreateWorkspaceRequest, db: Session = Depends(get_db)):
    """Membuat ruang kerja riset baru."""
    ws = create_workspace_with_defaults(db, name=req.name or "Ruang Kerja Hadis Niat", description=req.description or "")
    return ws


@router.get("")
def list_workspaces(db: Session = Depends(get_db)):
    """Mengambil daftar ruang kerja riset."""
    ws = create_workspace_with_defaults(db)
    workspaces = db.query(ResearchWorkspaceEntity).filter(ResearchWorkspaceEntity.status == "ACTIVE").all()
    return workspaces


@router.get("/{workspace_id}")
def get_workspace_detail(workspace_id: str, db: Session = Depends(get_db)):
    """Mengambil detail ruang kerja riset beserta catatan & temuan."""
    ws = db.query(ResearchWorkspaceEntity).filter(ResearchWorkspaceEntity.id == workspace_id).first()
    if not ws:
        ws = create_workspace_with_defaults(db)

    notes = db.query(ResearchNoteEntity).filter(ResearchNoteEntity.workspace_id == ws.id).all()
    findings = db.query(ResearchFindingEntity).filter(ResearchFindingEntity.workspace_id == ws.id).all()
    highlights = db.query(SourceHighlightEntity).filter(SourceHighlightEntity.workspace_id == ws.id).all()

    return {
        "workspace": ws,
        "notes": notes,
        "findings": findings,
        "highlights": highlights
    }


@router.post("/{workspace_id}/notes")
def add_workspace_note(workspace_id: str, req: CreateNoteRequest, db: Session = Depends(get_db)):
    """Menambahkan catatan riset Markdown baru ke ruang kerja."""
    note = ResearchNoteEntity(
        workspace_id=workspace_id,
        title=req.title,
        content=req.content,
        note_type=req.note_type or "OBSERVATION"
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.post("/{workspace_id}/highlights")
def add_workspace_highlight(workspace_id: str, req: CreateHighlightRequest, db: Session = Depends(get_db)):
    """Menambahkan highlight penandaan teks ke ruang kerja."""
    hl = create_text_highlight(
        db,
        workspace_id=workspace_id,
        page_id=req.page_id,
        selected_text=req.selected_text,
        start_offset=req.start_offset or 0,
        end_offset=req.end_offset or 40,
        color=req.color or "yellow"
    )
    return hl


@router.post("/{workspace_id}/compare")
def compare_workspace_variants(workspace_id: str, req: CompareRequest, db: Session = Depends(get_db)):
    """Komparasi perbedaan urutan kata varian hadis (Arabic Text Sequence Diff)."""
    return compare_text_variants(
        text1=req.text1 or "عن عمر بن الخطاب قال سمعت رسول الله يقول إنما الأعمال بالنيات",
        text2=req.text2 or "عن عمر بن الخطاب قال سمعت رسول الله يقول إنما الأعمال بالنية"
    )


@router.post("/{workspace_id}/ask")
def ask_ai_workspace(workspace_id: str, req: AskAIRequest, db: Session = Depends(get_db)):
    """Asisten AI Kontekstual Workspace ("Ask AI From Selection")."""
    return ask_context_aware_ai(
        db,
        workspace_id=workspace_id,
        question=req.question,
        selected_text=req.selected_text
    )
