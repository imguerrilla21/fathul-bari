import json
import logging
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hadith import Hadith
from app.models.sharh import SharhSection
from app.models.workspace import (
    ResearchAnnotation,
    ResearchCitation,
    ResearchNote,
    ResearchProject,
)
from app.services.graph_rag import expand_query_via_knowledge_graph
from app.services.rag_synthesizer import synthesize_rag_response
from app.services.workspace_exporter import (
    export_project_to_bibtex,
    export_project_to_json,
    export_project_to_markdown,
    export_project_to_ris,
)
from app.utils.db_helpers import to_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workspace", tags=["Tahap 10 Research Workspace"])


# DTO Schemas
class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    created_by: str = Field(default="Peneliti Hadis")


class UpdateProjectRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class CreateNoteRequest(BaseModel):
    content: str = Field(..., min_length=1)
    hadith_id: str | None = None
    sharh_section_id: str | None = None
    source_page_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class CreateAnnotationRequest(BaseModel):
    selected_text: str = Field(..., min_length=1)
    annotation_type: str = Field(default="NOTE", description="NOTE, QUESTION, IMPORTANT, CROSS_REFERENCE, QUOTE, TODO")
    comment: str = Field(..., min_length=1)
    hadith_id: str | None = None
    sharh_section_id: str | None = None


class CreateCitationRequest(BaseModel):
    hadith_id: str | None = None
    sharh_section_id: str | None = None
    citation_text: str
    work_title: str = "Fathul Bari Syarah Shahih al-Bukhari"
    author: str = "Al-Hafizh Ibnu Hajar al-Asqalani"
    edition: str | None = "Dar al-Ma'rifah, Beirut"
    volume: int | None = None
    printed_page: int | None = None
    pdf_page: int | None = None
    source_file: str | None = None


class WorkspaceAIRequest(BaseModel):
    query: str = Field(..., min_length=2)
    mode: str = Field(default="research", description="Mode riset workspace")


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """Mengambil daftar seluruh proyek penelitian riset aktif."""
    projects = list(
        db.scalars(
            select(ResearchProject).order_by(desc(ResearchProject.created_at))
        )
    )

    items = []
    for p in projects:
        notes_count = len(p.notes)
        annotations_count = len(p.annotations)
        citations_count = len(p.citations)

        items.append({
            "id": str(p.id),
            "title": p.title,
            "description": p.description,
            "created_by": p.created_by,
            "status": p.status,
            "notes_count": notes_count,
            "annotations_count": annotations_count,
            "citations_count": citations_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    return {
        "total": len(items),
        "projects": items,
    }


@router.post("/projects")
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db)):
    """Membuat proyek penelitian baru di Research Workspace."""
    project = ResearchProject(
        id=uuid.uuid4(),
        title=req.title,
        description=req.description,
        created_by=req.created_by,
        status="active",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "status": "success",
        "message": f"Proyek riset '{project.title}' berhasil dibuat.",
        "project": {
            "id": str(project.id),
            "title": project.title,
            "description": project.description,
            "created_by": project.created_by,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
        },
    }


@router.get("/projects/{project_id}")
def get_project_details(project_id: str, db: Session = Depends(get_db)):
    """Mengambil rincian proyek riset lengkap beserta catatan, anotasi, dan sitasi."""
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    notes_data = []
    for n in project.notes:
        tags = []
        if n.tags_json:
            try:
                tags = json.loads(n.tags_json)
            except Exception:
                tags = []
        notes_data.append({
            "id": str(n.id),
            "content": n.content,
            "hadith_id": str(n.hadith_id) if n.hadith_id else None,
            "sharh_section_id": str(n.sharh_section_id) if n.sharh_section_id else None,
            "source_page_id": n.source_page_id,
            "tags": tags,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })

    annotations_data = [
        {
            "id": str(a.id),
            "selected_text": a.selected_text,
            "annotation_type": a.annotation_type,
            "comment": a.comment,
            "hadith_id": str(a.hadith_id) if a.hadith_id else None,
            "sharh_section_id": str(a.sharh_section_id) if a.sharh_section_id else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in project.annotations
    ]

    citations_data = [
        {
            "id": str(c.id),
            "citation_text": c.citation_text,
            "work_title": c.work_title,
            "author": c.author,
            "edition": c.edition,
            "volume": c.volume,
            "printed_page": c.printed_page,
            "pdf_page": c.pdf_page,
            "source_file": c.source_file,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in project.citations
    ]

    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            "description": project.description,
            "created_by": project.created_by,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        },
        "notes": notes_data,
        "annotations": annotations_data,
        "citations": citations_data,
    }


@router.put("/projects/{project_id}")
def update_project(project_id: str, req: UpdateProjectRequest, db: Session = Depends(get_db)):
    """Memperbarui informasi proyek riset."""
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    if req.title is not None:
        project.title = req.title
    if req.description is not None:
        project.description = req.description
    if req.status is not None:
        project.status = req.status

    db.commit()
    return {"status": "success", "message": "Proyek riset berhasil diperbarui."}


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Menghapus proyek riset beserta seluruh catatan dan anotasinya."""
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    db.delete(project)
    db.commit()
    return {"status": "success", "message": "Proyek riset berhasil dihapus."}


@router.post("/projects/{project_id}/notes")
def add_note(project_id: str, req: CreateNoteRequest, db: Session = Depends(get_db)):
    """Menambahkan catatan analisis ilmiah ke proyek riset."""
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    note = ResearchNote(
        id=uuid.uuid4(),
        project_id=project.id,
        content=req.content,
        hadith_id=to_uuid(req.hadith_id) if req.hadith_id else None,
        sharh_section_id=to_uuid(req.sharh_section_id) if req.sharh_section_id else None,
        source_page_id=req.source_page_id,
        tags_json=json.dumps(req.tags, ensure_ascii=False) if req.tags else None,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "status": "success",
        "message": "Catatan penelitian berhasil ditambahkan.",
        "note_id": str(note.id),
    }


@router.delete("/notes/{note_id}")
def delete_note(note_id: str, db: Session = Depends(get_db)):
    """Menghapus catatan riset."""
    uid = to_uuid(note_id)
    note = db.scalar(select(ResearchNote).where(ResearchNote.id == uid)) if uid else None
    if not note:
        raise HTTPException(status_code=404, detail="Catatan tidak ditemukan.")

    db.delete(note)
    db.commit()
    return {"status": "success", "message": "Catatan berhasil dihapus."}


@router.post("/projects/{project_id}/annotations")
def add_annotation(project_id: str, req: CreateAnnotationRequest, db: Session = Depends(get_db)):
    """Menambahkan anotasi teks highlight pada naskah/matan."""
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    ann = ResearchAnnotation(
        id=uuid.uuid4(),
        project_id=project.id,
        selected_text=req.selected_text,
        annotation_type=req.annotation_type,
        comment=req.comment,
        hadith_id=to_uuid(req.hadith_id) if req.hadith_id else None,
        sharh_section_id=to_uuid(req.sharh_section_id) if req.sharh_section_id else None,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)

    return {
        "status": "success",
        "message": "Anotasi teks berhasil disimpan.",
        "annotation_id": str(ann.id),
    }


@router.delete("/annotations/{annotation_id}")
def delete_annotation(annotation_id: str, db: Session = Depends(get_db)):
    """Menghapus anotasi teks."""
    uid = to_uuid(annotation_id)
    ann = db.scalar(select(ResearchAnnotation).where(ResearchAnnotation.id == uid)) if uid else None
    if not ann:
        raise HTTPException(status_code=404, detail="Anotasi tidak ditemukan.")

    db.delete(ann)
    db.commit()
    return {"status": "success", "message": "Anotasi berhasil dihapus."}


@router.post("/projects/{project_id}/citations")
def add_citation(project_id: str, req: CreateCitationRequest, db: Session = Depends(get_db)):
    """Menyematkan sitasi dokumen primer ke proyek riset."""
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    cit = ResearchCitation(
        id=uuid.uuid4(),
        project_id=project.id,
        hadith_id=to_uuid(req.hadith_id) if req.hadith_id else None,
        sharh_section_id=to_uuid(req.sharh_section_id) if req.sharh_section_id else None,
        citation_text=req.citation_text,
        work_title=req.work_title,
        author=req.author,
        edition=req.edition,
        volume=req.volume,
        printed_page=req.printed_page,
        pdf_page=req.pdf_page,
        source_file=req.source_file,
    )
    db.add(cit)
    db.commit()
    db.refresh(cit)

    return {
        "status": "success",
        "message": "Sitasi berhasil disematkan ke proyek.",
        "citation_id": str(cit.id),
    }


@router.delete("/citations/{citation_id}")
def delete_citation(citation_id: str, db: Session = Depends(get_db)):
    """Menghapus sitasi dari proyek."""
    uid = to_uuid(citation_id)
    cit = db.scalar(select(ResearchCitation).where(ResearchCitation.id == uid)) if uid else None
    if not cit:
        raise HTTPException(status_code=404, detail="Sitasi tidak ditemukan.")

    db.delete(cit)
    db.commit()
    return {"status": "success", "message": "Sitasi berhasil dihapus."}


@router.post("/projects/{project_id}/ai-ask")
async def ask_workspace_ai(project_id: str, req: WorkspaceAIRequest, db: Session = Depends(get_db)):
    """
    Eksekusi Scoped GraphRAG AI Assistant khusus dalam korpus dan bukti proyek penelitian ini.
    """
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    # 1. Expand Knowledge Graph
    graph_rag_info = expand_query_via_knowledge_graph(
        db=db,
        query=req.query,
        retrieval_mode=req.mode,
        limit=4,
    )

    # 2. Sintesis respon dengan konteks proyek
    context_text = f"PROYEK RISET: {project.title}\n"
    if project.description:
        context_text += f"DESKRIPSI: {project.description}\n"

    # Tambahkan catatan dan anotasi proyek ke dalam konteks
    if project.notes:
        context_text += "\nCATATAN PENELITIAN:\n"
        for n in project.notes[:3]:
            context_text += f"- {n.content}\n"

    if project.annotations:
        context_text += "\nANOTASI TEKS PENELITI:\n"
        for a in project.annotations[:3]:
            context_text += f"- [{a.annotation_type}] \"{a.selected_text}\" -> {a.comment}\n"

    rag_retrieval_result = {
        "hadith": None,
        "sharh_sections": [
            {
                "id": str(uuid.uuid4()),
                "title": it.get("sharh_title") or f"Fathul Bari Jilid {it.get('volume')}",
                "arabic_text": it.get("snippet", ""),
                "volume": it.get("volume"),
                "page": it.get("page"),
                "confidence": 0.95,
                "verified": it.get("verified", True),
            }
            for it in graph_rag_info.get("evidence_chain", [])
        ],
        "query_expansion": [f"Project: {project.title}"],
    }

    synthesis_res = await synthesize_rag_response(
        query=req.query,
        rag_retrieval_result=rag_retrieval_result,
        mode="syarah_focus",
    )

    return {
        "status": "success",
        "project_id": str(project.id),
        "query": req.query,
        "answer": synthesis_res.get("answer"),
        "citations": synthesis_res.get("citations", []),
        "evidence_chain": graph_rag_info.get("evidence_chain", []),
    }


@router.get("/projects/{project_id}/export")
def export_project(
    project_id: str,
    format: str = Query(default="markdown", description="Format: markdown, bibtex, ris, json"),
    db: Session = Depends(get_db),
):
    """
    Mengekspor seluruh monograf proyek riset ke format Markdown, BibTeX, RIS, atau JSON.
    """
    uid = to_uuid(project_id)
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == uid)) if uid else None
    if not project:
        raise HTTPException(status_code=404, detail="Proyek riset tidak ditemukan.")

    notes = list(project.notes)
    annotations = list(project.annotations)
    citations = list(project.citations)

    clean_filename = project.title.lower().replace(" ", "_")[:40]

    if format.lower() == "bibtex":
        content = export_project_to_bibtex(project, citations)
        return Response(
            content=content,
            media_type="application/x-bibtex",
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}.bib"'},
        )
    elif format.lower() == "ris":
        content = export_project_to_ris(project, citations)
        return Response(
            content=content,
            media_type="application/x-research-info-systems",
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}.ris"'},
        )
    elif format.lower() == "json":
        data = export_project_to_json(project, notes, annotations, citations)
        return Response(
            content=json.dumps(data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}.json"'},
        )
    else:  # default markdown
        content = export_project_to_markdown(project, notes, annotations, citations)
        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}.md"'},
        )
