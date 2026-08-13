from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.publication.publication_service import create_publication, get_publication_by_id, get_publication_by_slug, create_publication_version
from app.services.publication.block_service import add_block, link_evidence_to_block, get_blocks_for_version, get_evidence_for_block
from app.services.publication.editorial_service import report_issue, get_issues_for_publication
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class CreatePubReq(BaseModel):
    project_id: str
    title: str
    slug: str
    content_type: str
    language: str = "id"

@router.post("/publications")
def create_pub(req: CreatePubReq, db: Session = Depends(get_db)):
    pub = create_publication(db, req.project_id, req.title, req.slug, req.content_type, req.language)
    return pub

class CreateVerReq(BaseModel):
    content: str
    change_summary: str

@router.post("/publications/{pub_id}/versions")
def create_version(pub_id: str, req: CreateVerReq, db: Session = Depends(get_db)):
    ver = create_publication_version(db, pub_id, req.content, req.change_summary)
    return ver

class CreateBlockReq(BaseModel):
    block_type: str
    content: str
    block_order: int

@router.post("/publications/versions/{version_id}/blocks")
def add_pub_block(version_id: str, req: CreateBlockReq, db: Session = Depends(get_db)):
    block = add_block(db, version_id, req.block_type, req.content, req.block_order)
    return block

class LinkEvidenceReq(BaseModel):
    evidence_type: str
    evidence_id: str
    relation: str = "SUPPORTED_BY"

@router.post("/publications/blocks/{block_id}/evidence")
def link_evidence(block_id: str, req: LinkEvidenceReq, db: Session = Depends(get_db)):
    link = link_evidence_to_block(db, block_id, req.evidence_type, req.evidence_id, req.relation)
    return link

class ReportIssueReq(BaseModel):
    block_id: str
    issue_type: str
    severity: str
    description: str

@router.post("/publications/{pub_id}/issues")
def report_editorial_issue(pub_id: str, req: ReportIssueReq, db: Session = Depends(get_db)):
    issue = report_issue(db, pub_id, req.block_id, req.issue_type, req.severity, req.description)
    return issue

@router.get("/publications/{pub_id}/issues")
def list_issues(pub_id: str, db: Session = Depends(get_db)):
    return get_issues_for_publication(db, pub_id)

@router.post("/publications/{pub_id}/publish")
def publish_publication(pub_id: str, db: Session = Depends(get_db)):
    pub = get_publication_by_id(db, pub_id)
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
    pub.status = "PUBLISHED"
    db.commit()
    return pub

@router.get("/public/publications/{slug}")
def public_reader(slug: str, db: Session = Depends(get_db)):
    pub = get_publication_by_slug(db, slug)
    if not pub or pub.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Publication not found or not published")
    
    # Get latest version
    from app.models.publication import PublicationVersionEntity
    ver = db.query(PublicationVersionEntity).filter(PublicationVersionEntity.publication_id == pub.id).order_by(PublicationVersionEntity.version_number.desc()).first()
    
    blocks = []
    if ver:
        raw_blocks = get_blocks_for_version(db, ver.id)
        for rb in raw_blocks:
            evidence = get_evidence_for_block(db, rb.id)
            blocks.append({
                "id": rb.id,
                "type": rb.block_type,
                "content": rb.content,
                "evidence": [{"id": e.id, "evidence_id": e.evidence_id, "type": e.evidence_type} for e in evidence]
            })
            
    return {
        "title": pub.title,
        "status": pub.status,
        "version": ver.version_number if ver else 0,
        "blocks": blocks,
        "updated_at": pub.updated_at
    }
