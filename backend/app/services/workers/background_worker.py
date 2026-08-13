import logging
import uuid
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.production_deployment import SystemWorkerJob

logger = logging.getLogger("background_worker")


def enqueue_worker_job(db: Session, job_type: str, job_key: str, volume: int = 1) -> SystemWorkerJob:
    """
    Mendaftarkan job worker latar belakang secara idempoten berbasis checksum SHA-256 / job_key.
    Mencegah redundansi jika job dengan key sama sudah pernah/sedang dijalankan.
    """
    existing = db.query(SystemWorkerJob).filter(SystemWorkerJob.job_key == job_key).first()
    if existing:
        return existing

    job = SystemWorkerJob(
        job_key=job_key,
        job_type=job_type,
        status="RUNNING",
        progress_pct=10,
        current_stage="INGEST",
        pipeline_version="17.0"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Execute pipeline stage simulation
    execute_worker_pipeline_job(db, job.id)

    return job


def execute_worker_pipeline_job(db: Session, job_id: str):
    """
    Simulasi eksekusi pipeline state machine worker:
    INGEST ➔ EXTRACT ➔ OCR ➔ NORMALIZE ➔ SECTION_DETECT ➔ HADITH_DETECT ➔ MATCH ➔ EMBED ➔ GRAPH_UPDATE ➔ QUALITY_CHECK ➔ COMPLETED
    """
    job = db.query(SystemWorkerJob).filter(SystemWorkerJob.id == job_id).first()
    if not job:
        return

    try:
        job.current_stage = "EXTRACT"
        job.progress_pct = 30
        db.commit()

        job.current_stage = "MATCH"
        job.progress_pct = 70
        db.commit()

        job.current_stage = "COMPLETED"
        job.status = "COMPLETED"
        job.progress_pct = 100
        db.commit()
    except Exception as err:
        job.status = "FAILED"
        job.error_log = str(err)
        db.commit()


def get_worker_jobs_list(db: Session) -> List[Dict[str, Any]]:
    """Mengambil daftar seluruh background worker jobs."""
    jobs = db.query(SystemWorkerJob).order_by(SystemWorkerJob.created_at.desc()).all()
    return [
        {
            "id": j.id,
            "job_key": j.job_key,
            "job_type": j.job_type,
            "status": j.status,
            "progress_pct": j.progress_pct,
            "current_stage": j.current_stage,
            "pipeline_version": j.pipeline_version,
            "error_log": j.error_log,
            "created_at": j.created_at.isoformat() if j.created_at else None
        }
        for j in jobs
    ]


def retry_failed_worker_job(db: Session, job_id: str) -> Dict[str, Any]:
    """Mengulang kembali job worker yang gagal secara idempoten."""
    job = db.query(SystemWorkerJob).filter(SystemWorkerJob.id == job_id).first()
    if not job:
        return {"error": "Job tidak ditemukan"}

    job.status = "RUNNING"
    job.error_log = None
    job.progress_pct = 10
    job.current_stage = "INGEST"
    db.commit()

    execute_worker_pipeline_job(db, job.id)

    return {
        "message": "Job berhasil diulang kembali (Idempotent Retry).",
        "job_id": job.id,
        "status": job.status
    }
