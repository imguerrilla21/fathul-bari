from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.hadith_data_layer import HadithEntity, HadithIngestionJob
from app.services.hadith_data_layer.hadith_ingestion_service import run_batch_ingestion_job
from app.services.hadith_data_layer.hadith_repository import search_local_hadiths

router = APIRouter(prefix="/api/v1/hadith-layer", tags=["hadith-data-layer"])


class IngestRequest(BaseModel):
    collection_slug: Optional[str] = "bukhari"
    limit: Optional[int] = 10


@router.post("/ingest")
def trigger_batch_ingestion(req: IngestRequest, db: Session = Depends(get_db)):
    """Peluncur Batch Ingestion Job dari Ahmad Sanusi API Provider."""
    job = run_batch_ingestion_job(db, collection_slug=req.collection_slug or "bukhari", limit=req.limit or 10)
    return {
        "job_id": job.id,
        "provider": job.provider,
        "collection": job.collection,
        "status": job.status,
        "processed_items": job.processed_items,
        "total_items": job.total_items
    }


@router.get("/jobs/{job_id}")
def get_ingestion_job_status(job_id: str, db: Session = Depends(get_db)):
    """Pelacak status & progres job batch ingestion."""
    job = db.query(HadithIngestionJob).filter(HadithIngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job ID tidak ditemukan")
    return {
        "job_id": job.id,
        "provider": job.provider,
        "collection": job.collection,
        "status": job.status,
        "processed_items": job.processed_items,
        "total_items": job.total_items,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


@router.get("/search")
def search_hadiths(q: str = Query(..., min_length=1), limit: int = 10, db: Session = Depends(get_db)):
    """Pencarian Hadis Lokal Terindeks (Local Research Index Search)."""
    results = search_local_hadiths(db, query=q, limit=limit)
    return {
        "query": q,
        "total": len(results),
        "results": [
            {
                "id": h.id,
                "external_id": h.external_id,
                "hadith_number": h.hadith_number,
                "arabic_text": h.arabic_text,
                "normalized_text": h.normalized_text,
                "narrator_text": h.narrator_text,
                "grade": h.grade,
                "content_hash": h.content_hash,
                "source_url": h.source_url
            }
            for h in results
        ]
    }


@router.get("/{id}")
def get_hadith_detail(id: str, db: Session = Depends(get_db)):
    """Mengambil detail lengkap Hadis dengan metadata Provenance & SHA-256 Content Hash."""
    h = db.query(HadithEntity).filter(HadithEntity.id == id).first()
    if not h:
        h = db.query(HadithEntity).filter(HadithEntity.external_id == id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hadis tidak ditemukan")

    return {
        "id": h.id,
        "external_id": h.external_id,
        "hadith_number": h.hadith_number,
        "arabic_text": h.arabic_text,
        "normalized_text": h.normalized_text,
        "search_text": h.search_text,
        "narrator_text": h.narrator_text,
        "grade": h.grade,
        "content_hash": h.content_hash,
        "source_url": h.source_url,
        "provenance": {
            "provider": "ahmad_sanusi",
            "content_hash": h.content_hash,
            "created_at": h.created_at.isoformat() if h.created_at else None
        }
    }
