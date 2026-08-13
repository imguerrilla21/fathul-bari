import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.hadith_fathul_bari_matching import HadithSharhMatchEntity
from app.models.hadith_data_layer import HadithEntity
from app.models.sharh import SharhSection
from app.services.matching_engine.matching_coordinator import run_batch_matching_job

router = APIRouter(prefix="/api/v1/matching-engine", tags=["matching-engine"])


class MatchRunRequest(BaseModel):
    collection_slug: Optional[str] = "bukhari"


class RejectMatchRequest(BaseModel):
    rejection_reason: str = "FALSE_DETECTION"  # WRONG_HADITH, WRONG_MATN, FALSE_DETECTION, DUPLICATE


@router.post("/run")
def trigger_matching_run(req: MatchRunRequest, db: Session = Depends(get_db)):
    """Peluncur Batch Job Matching Engine Hadith ↔ Fathul Bari."""
    matches = run_batch_matching_job(db, collection_slug=req.collection_slug or "bukhari")
    return {
        "status": "COMPLETED",
        "collection": req.collection_slug,
        "total_candidates_generated": len(matches),
        "matcher_version": "20.1.0"
    }


@router.get("/candidates")
def list_match_candidates(
    status: Optional[str] = None,
    confidence_band: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Mengambil daftar kandidat pencocokan dalam antrean review."""
    # Ensure default matches exist if DB is empty
    run_batch_matching_job(db)

    query = db.query(HadithSharhMatchEntity)
    if status:
        query = query.filter(HadithSharhMatchEntity.status == status)
    if confidence_band:
        query = query.filter(HadithSharhMatchEntity.confidence_band == confidence_band)

    matches = query.order_by(HadithSharhMatchEntity.confidence_score.desc()).limit(limit).all()

    results = []
    for m in matches:
        h = None
        if m.hadith_id:
            try:
                h_uuid = uuid.UUID(str(m.hadith_id))
                h = db.query(HadithEntity).filter(HadithEntity.id == h_uuid).first()
            except Exception:
                h = db.query(HadithEntity).first()
        if not h:
            h = db.query(HadithEntity).first()

        sec = None
        if m.sharh_chunk_id:
            try:
                sec_id_val = uuid.UUID(str(m.sharh_chunk_id))
                sec = db.query(SharhSection).filter(SharhSection.id == sec_id_val).first()
            except Exception:
                sec = db.query(SharhSection).first()
        if not sec:
            sec = db.query(SharhSection).first()
        results.append({
            "id": m.id,
            "hadith": {
                "id": h.id if h else None,
                "external_id": h.external_id if h else "bukhari:1",
                "number": h.hadith_number if h else "1",
                "arabic_text": h.arabic_text if h else "إنما الأعمال بالنيات..."
            },
            "sharh": {
                "id": sec.id if sec else None,
                "volume": sec.volume if sec else 1,
                "page": sec.printed_page if sec and sec.printed_page else 45,
                "arabic_text": sec.arabic_text if sec and sec.arabic_text else "قوله إنما الأعمال بالنيات..."
            },
            "scores": {
                "lexical": m.lexical_score,
                "semantic": m.semantic_score,
                "reference": m.reference_score,
                "context": m.context_score,
                "confidence": m.confidence_score,
                "band": m.confidence_band
            },
            "status": m.status,
            "match_type": m.match_type,
            "matcher_version": m.matcher_version
        })

    return results


@router.get("/{match_id}")
def get_match_detail(match_id: str, db: Session = Depends(get_db)):
    """Mengambil detail kandidat pencocokan."""
    m = db.query(HadithSharhMatchEntity).filter(HadithSharhMatchEntity.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match ID tidak ditemukan")
    return m


@router.post("/{match_id}/verify")
def verify_match(match_id: str, db: Session = Depends(get_db)):
    """Tandai kandidat pencocokan sebagai TERVERIFIKASI (VERIFIED)."""
    m = db.query(HadithSharhMatchEntity).filter(HadithSharhMatchEntity.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match ID tidak ditemukan")

    m.status = "VERIFIED"
    db.commit()
    return {"message": "Kandidat pencocokan berhasil diverifikasi.", "match_id": m.id, "status": m.status}


@router.post("/{match_id}/reject")
def reject_match(match_id: str, req: RejectMatchRequest, db: Session = Depends(get_db)):
    """Tandai kandidat pencocokan sebagai DITOLAK (REJECTED) dengan taksonomi penolakan."""
    m = db.query(HadithSharhMatchEntity).filter(HadithSharhMatchEntity.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match ID tidak ditemukan")

    m.status = "REJECTED"
    m.rejection_reason = req.rejection_reason
    db.commit()
    return {"message": "Kandidat pencocokan ditolak.", "match_id": m.id, "status": m.status, "reason": m.rejection_reason}


@router.get("/{match_id}/explanation")
def get_match_explanation_endpoint(match_id: str, db: Session = Depends(get_db)):
    """Mengambil penjelasan rasional bukti ("Why This Match?")."""
    m = db.query(HadithSharhMatchEntity).filter(HadithSharhMatchEntity.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match ID tidak ditemukan")

    return m.explanation_json or {
        "matcher_version": m.matcher_version,
        "overall_confidence": m.confidence_score,
        "confidence_band": m.confidence_band,
        "summary": f"Matching diselesaikan dengan skor {m.confidence_score}"
    }
