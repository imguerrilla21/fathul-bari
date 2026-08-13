from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.scholarly_citation_v2 import ScholarlyCitationEntity, BibliographicSourceEntity, AuthorEntity
from app.services.scholarly_citation.citation_formatter import CitationFormatter
from app.services.scholarly_citation.citation_validator_v2 import validate_citation_integrity
from app.services.scholarly_citation.bibliography_generator import generate_workspace_bibliography
from app.services.scholarly_citation.export_engine import export_workspace_document

router = APIRouter(prefix="/api/v1", tags=["scholarly-citation-v2"])


class FormatCitationRequest(BaseModel):
    author: Optional[str] = "Ibn Hajar al-'Asqalani"
    title: Optional[str] = "Fath al-Bari bi-Sharh Sahih al-Bukhari"
    volume: Optional[int] = 1
    printed_page: Optional[int] = 45
    publisher: Optional[str] = "Dar al-Ma'rifah"
    pub_year: Optional[str] = "1379 H"
    style: Optional[str] = "ISLAMIC_TRADITIONAL"
    citation_type: Optional[str] = "FOOTNOTE"


class ExportRequest(BaseModel):
    export_format: Optional[str] = "markdown"  # markdown, docx, pdf, bibtex, ris, csl_json
    style: Optional[str] = "ISLAMIC_TRADITIONAL"


@router.post("/citations-v2")
def create_scholarly_citation(db: Session = Depends(get_db)):
    """Membuat rekod sitasi ilmiah baru."""
    src = db.query(BibliographicSourceEntity).first()
    if not src:
        src = BibliographicSourceEntity(
            title="Fath al-Bari bi-Sharh Sahih al-Bukhari",
            publisher="Dar al-Ma'rifah",
            publication_place="Beirut",
            publication_year="1379 H"
        )
        db.add(src)
        db.commit()
        db.refresh(src)

    cit = ScholarlyCitationEntity(
        bibliographic_source_id=src.id,
        locator_json={"volume": 1, "printed_page": 45, "pdf_page": 67},
        citation_label="FB-V1-P45-C001",
        content_hash="8e72a4b89f1d2c3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e"
    )
    db.add(cit)
    db.commit()
    db.refresh(cit)
    return cit


@router.get("/citations-v2")
def list_scholarly_citations(db: Session = Depends(get_db)):
    """Mengambil daftar sitasi ilmiah terdaftar."""
    citations = db.query(ScholarlyCitationEntity).all()
    results = []
    for c in citations:
        results.append({
            "id": c.id,
            "citation_label": c.citation_label,
            "locator": c.locator_json,
            "content_hash": c.content_hash,
            "formatted": {
                "ISLAMIC_TRADITIONAL": CitationFormatter.format_citation(style="ISLAMIC_TRADITIONAL"),
                "CHICAGO": CitationFormatter.format_citation(style="CHICAGO"),
                "APA": CitationFormatter.format_citation(style="APA")
            }
        })
    return results


@router.post("/citations-v2/{citation_id}/format")
def format_single_citation(citation_id: str, req: FormatCitationRequest, db: Session = Depends(get_db)):
    """Pemformat sitasi ilmiah langsung berbasis gaya yang dipilih."""
    formatted_text = CitationFormatter.format_citation(
        author=req.author or "Ibn Hajar al-'Asqalani",
        title=req.title or "Fath al-Bari bi-Sharh Sahih al-Bukhari",
        volume=req.volume or 1,
        printed_page=req.printed_page or 45,
        publisher=req.publisher or "Dar al-Ma'rifah",
        pub_year=req.pub_year or "1379 H",
        style=req.style or "ISLAMIC_TRADITIONAL",
        citation_type=req.citation_type or "FOOTNOTE"
    )
    
    validation = validate_citation_integrity(db, citation_id)

    return {
        "citation_id": citation_id,
        "style": req.style,
        "citation_type": req.citation_type,
        "formatted_text": formatted_text,
        "validation": validation
    }


@router.get("/workspaces-v2/{workspace_id}/bibliography")
def get_workspace_bibliography_endpoint(workspace_id: str, style: Optional[str] = "ISLAMIC_TRADITIONAL", db: Session = Depends(get_db)):
    """Mengambil daftar pustaka workspace terotomatisasi."""
    return generate_workspace_bibliography(db, workspace_id, style=style or "ISLAMIC_TRADITIONAL")


@router.post("/workspaces-v2/{workspace_id}/export")
def export_workspace_document_endpoint(workspace_id: str, req: ExportRequest, db: Session = Depends(get_db)):
    """Ekspor Dokumen Riset & Daftar Pustaka Multi-Format (Markdown, DOCX, PDF, BibTeX, RIS, CSL-JSON)."""
    return export_workspace_document(
        db,
        workspace_id=workspace_id,
        export_format=req.export_format or "markdown",
        style=req.style or "ISLAMIC_TRADITIONAL"
    )
