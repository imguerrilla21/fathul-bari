import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hadith, HadithSharhLink, SharhSection
from app.services.hadith_linker import get_matching_candidates, persist_matching_candidates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/matching", tags=["Tahap 4 Matching Engine"])


class VerificationRequest(BaseModel):
    notes: str | None = Field(default=None, description="Catatan hasil verifikasi peneliti")


class PersistRequest(BaseModel):
    top_k: int = Field(default=10, ge=1, le=50, description="Jumlah kandidat teratas yang dievaluasi")
    min_confidence: float = Field(default=0.50, ge=0.0, le=1.0, description="Batas confidence minimal untuk disimpan")


@router.get("/sharh/{sharh_id}/candidates")
def get_candidates_for_sharh(
    sharh_id: str,
    top_k: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Menghitung skor kandidat hadis untuk seksi syarah tertentu menggunakan Matching Engine v1."""
    section = db.scalar(select(SharhSection).where(SharhSection.id == sharh_id))
    if not section:
        raise HTTPException(status_code=404, detail="Seksi syarah tidak ditemukan.")

    candidates = get_matching_candidates(db, section, top_k=top_k)

    return {
        "sharh_id": str(section.id),
        "volume": section.volume,
        "page": section.printed_page or section.pdf_page or section.page,
        "title": section.title,
        "formula": "final = number_score*0.50 + text_score*0.35 + context_score*0.15",
        "total_candidates": len(candidates),
        "candidates": candidates,
    }


@router.post("/sharh/{sharh_id}/persist")
def persist_candidates_for_sharh(
    sharh_id: str,
    req: PersistRequest,
    db: Session = Depends(get_db),
):
    """Menghitung dan menyimpan kandidat hadis yang memenuhi batas min_confidence ke database."""
    section = db.scalar(select(SharhSection).where(SharhSection.id == sharh_id))
    if not section:
        raise HTTPException(status_code=404, detail="Seksi syarah tidak ditemukan.")

    candidates = get_matching_candidates(db, section, top_k=req.top_k)
    persisted_links = persist_matching_candidates(db, section, candidates=candidates, min_confidence=req.min_confidence)

    return {
        "status": "persisted",
        "sharh_id": str(section.id),
        "persisted_count": len(persisted_links),
        "min_confidence_applied": req.min_confidence,
        "links": [
            {
                "link_id": str(l.id),
                "hadith_id": str(l.hadith_id),
                "confidence": l.confidence,
                "review_status": l.review_status,
                "verified": l.verified,
            }
            for l in persisted_links
        ],
    }


@router.get("/links")
def list_matching_links(
    minimum_confidence: float = Query(default=0.75, ge=0.0, le=1.0, description="Filter confidence minimum (default: 0.75)"),
    review_status: str | None = Query(default=None, description="Filter kategori status (auto_candidate, review, weak_match, verified, rejected)"),
    verified: bool | None = Query(default=None, description="Filter status verifikasi peneliti"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Mendaftar hasil tautan hadits–syarah yang telah dihasilkan dengan filter confidence dan review status."""
    stmt = select(HadithSharhLink).where(HadithSharhLink.confidence >= minimum_confidence)

    if review_status:
        stmt = stmt.where(HadithSharhLink.review_status == review_status)
    if verified is not None:
        stmt = stmt.where(HadithSharhLink.verified == verified)

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    links = list(
        db.scalars(
            stmt.order_by(HadithSharhLink.confidence.desc())
            .offset(offset)
            .limit(limit)
        )
    )

    results = []
    for l in links:
        sec = db.scalar(select(SharhSection).where(SharhSection.id == l.sharh_section_id))
        h = db.scalar(select(Hadith).where(Hadith.id == l.hadith_id))

        evidence_obj = {}
        if l.evidence:
            try:
                evidence_obj = json.loads(l.evidence)
            except Exception:
                evidence_obj = {"raw": l.evidence}

        results.append({
            "link_id": str(l.id),
            "hadith_id": str(l.hadith_id),
            "hadith_number": h.external_number if h else None,
            "hadith_arab": (h.arabic_text or "")[:100] + "..." if h else None,
            "sharh_id": str(l.sharh_section_id),
            "sharh_volume": sec.volume if sec else None,
            "sharh_page": (sec.printed_page or sec.pdf_page or sec.page) if sec else None,
            "sharh_title": sec.title if sec else None,
            "match_method": l.match_method,
            "confidence": l.confidence,
            "confidence_percent": round((l.confidence or 0.0) * 100, 2),
            "review_status": l.review_status,
            "verified": l.verified,
            "evidence": evidence_obj,
            "notes": l.notes,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        })

    return {
        "minimum_confidence": minimum_confidence,
        "total": total,
        "limit": limit,
        "offset": offset,
        "links": results,
    }


@router.post("/links/{link_id}/verify")
def verify_matching_link(
    link_id: str,
    req: VerificationRequest | None = None,
    db: Session = Depends(get_db),
):
    """Aksi verifikasi manusia oleh peneliti untuk menyetujui tautan hadits–syarah."""
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == link_id))
    if not link:
        raise HTTPException(status_code=404, detail="Tautan hadits–syarah tidak ditemukan.")

    link.verified = True
    link.review_status = "verified"
    if req and req.notes:
        link.notes = req.notes

    db.commit()
    db.refresh(link)

    return {
        "status": "verified",
        "link_id": str(link.id),
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
    }


@router.post("/links/{link_id}/reject")
def reject_matching_link(
    link_id: str,
    req: VerificationRequest | None = None,
    db: Session = Depends(get_db),
):
    """Aksi penolakan manusia oleh peneliti untuk menolak kandidat tautan yang tidak tepat."""
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == link_id))
    if not link:
        raise HTTPException(status_code=404, detail="Tautan hadits–syarah tidak ditemukan.")

    link.verified = False
    link.review_status = "rejected"
    if req and req.notes:
        link.notes = req.notes

    db.commit()
    db.refresh(link)

    return {
        "status": "rejected",
        "link_id": str(link.id),
        "verified": link.verified,
        "review_status": link.review_status,
        "notes": link.notes,
    }
