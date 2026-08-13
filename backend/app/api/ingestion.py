from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.database import get_db
from app.models.ingestion import SourceDocument, SourcePage, TextBlock, IngestionJob, CorpusManifest
from app.services.ingestion_pipeline import (
    validate_and_register_file,
    start_ingestion_job,
    get_ingestion_jobs_list,
    get_corpus_manifests_list,
    get_source_documents_list,
)

router = APIRouter(prefix="/api/v1/admin/ingestion", tags=["ingestion"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    volume: int = Form(1),
    db: Session = Depends(get_db)
):
    """
    Upload file PDF/Teks Fathul Bari, validasi integritas file, dan pemeriksaan checksum SHA-256 (Duplicate Detection).
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File kosong")

    res = validate_and_register_file(
        db=db,
        filename=file.filename or "fathul_bari.pdf",
        content=content,
        volume=volume
    )
    return res


@router.post("/start/{document_id}")
def start_job(document_id: str, db: Session = Depends(get_db)):
    """Memulai Job Penyerapan Korpus (Ingestion Pipeline State Machine)."""
    res = start_ingestion_job(db, document_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """Mengambil daftar seluruh Source Documents yang telah diunggah."""
    return get_source_documents_list(db)


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    """Mengambil daftar seluruh Ingestion Jobs dan status progress."""
    return get_ingestion_jobs_list(db)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Mengambil detail progress & checkpoint stage dari Ingestion Job."""
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")

    return {
        "id": str(job.id),
        "document_id": str(job.source_document_id),
        "volume": job.volume,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "current_stage": job.current_stage,
        "pipeline_version": job.pipeline_version,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None
    }


@router.get("/manifests")
def list_manifests(db: Session = Depends(get_db)):
    """Mengambil daftar Corpus Manifests reproduksibilitas korpus Fathul Bari."""
    return get_corpus_manifests_list(db)
