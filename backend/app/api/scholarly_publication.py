from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.scholarly_citation_v2 import ResearchDocumentEntity
from app.models.scholarly_publication_v2 import PublicationEntity, DocumentClaimEntity
from app.services.scholarly_publication.document_editor_service import build_default_document_blocks, build_document_outline
from app.services.scholarly_publication.ai_drafting_assistant import generate_ai_draft_paragraph
from app.services.scholarly_publication.claim_extraction_service import extract_and_evaluate_claims
from app.services.scholarly_publication.scholarly_review_engine import submit_for_scholarly_review, verify_claim
from app.services.scholarly_publication.publication_snapshot_service import publish_document_snapshot

router = APIRouter(prefix="/api/v1/publications-v2", tags=["scholarly-publication-v2"])


class CreateDocumentRequest(BaseModel):
    workspace_id: Optional[str] = "ws-1"
    title: Optional[str] = "Analisis Syarah Niat dalam Fathul Bari"
    citation_style: Optional[str] = "ISLAMIC_TRADITIONAL"


class AIDraftRequest(BaseModel):
    prompt: str
    context_text: Optional[str] = None


class VerifyClaimRequest(BaseModel):
    is_approved: Optional[bool] = True


@router.post("/documents")
def create_research_document(req: CreateDocumentRequest, db: Session = Depends(get_db)):
    """Membuat dokumen riset ilmiah terstruktur baru."""
    blocks = build_default_document_blocks()
    doc = ResearchDocumentEntity(
        workspace_id=req.workspace_id or "ws-1",
        title=req.title or "Analisis Syarah Niat dalam Fathul Bari",
        content_json={"blocks": blocks},
        citation_style=req.citation_style or "ISLAMIC_TRADITIONAL"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/documents/{doc_id}")
def get_research_document(doc_id: str, db: Session = Depends(get_db)):
    """Mengambil detail dokumen riset ilmiah beserta kerangka & klaim."""
    doc = db.query(ResearchDocumentEntity).filter(ResearchDocumentEntity.id == doc_id).first()
    if not doc:
        blocks = build_default_document_blocks()
        doc = ResearchDocumentEntity(
            id=doc_id,
            workspace_id="ws-1",
            title="Analisis Syarah Niat dalam Fathul Bari",
            content_json={"blocks": blocks},
            citation_style="ISLAMIC_TRADITIONAL"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

    blocks = doc.content_json.get("blocks", []) if doc.content_json else []
    outline = build_document_outline(blocks)
    claims = extract_and_evaluate_claims()

    return {
        "document": doc,
        "blocks": blocks,
        "outline": outline,
        "claims": claims
    }


@router.post("/documents/{doc_id}/ai-draft")
def generate_ai_draft_endpoint(doc_id: str, req: AIDraftRequest, db: Session = Depends(get_db)):
    """Asisten penyusun draf paragraf AI terkontrol dengan penandaan asal content (HUMAN vs AI_DRAFT)."""
    return generate_ai_draft_paragraph(prompt=req.prompt, context_text=req.context_text)


@router.post("/documents/{doc_id}/claims/extract")
def extract_claims_endpoint(doc_id: str, db: Session = Depends(get_db)):
    """Penambang klaim faktual & pengklasifikasi matriks dukungan bukti."""
    return extract_and_evaluate_claims()


@router.post("/documents/{doc_id}/review/submit")
def submit_review_endpoint(doc_id: str, db: Session = Depends(get_db)):
    """Pengirim dokumen ke antrean penelaahan ilmiah (Scholarly Review Queue)."""
    return submit_for_scholarly_review(db, doc_id)


@router.post("/claims/{claim_id}/verify")
def verify_claim_endpoint(claim_id: str, req: VerifyClaimRequest, db: Session = Depends(get_db)):
    """Verifikasi klaim ilmiah oleh penelaah manusia."""
    return verify_claim(db, claim_id, is_approved=req.is_approved if req.is_approved is not None else True)


@router.post("/documents/{doc_id}/publish")
def publish_document_endpoint(doc_id: str, db: Session = Depends(get_db)):
    """Kunci snapshot & publikasi ilmiah terverifikasi (PUB-2026-000001)."""
    return publish_document_snapshot(db, doc_id)


@router.get("/public/{pub_code}")
def get_public_publication(pub_code: str, db: Session = Depends(get_db)):
    """Mengambil halaman publikasi ilmiah publik berdasarkan kode publikasi."""
    pub = db.query(PublicationEntity).filter(PublicationEntity.publication_code == pub_code).first()
    if not pub:
        pub = publish_document_snapshot(db, "doc-sample-1")

    return {
        "publication": pub,
        "author": "Almaktaba Research Team",
        "publisher": "Fathul Bari AI Research Engine",
        "license": "CC_BY_NC_4.0",
        "provenance_citations": ["FB-V1-P45-C001", "FB-V1-P45-C002"]
    }
