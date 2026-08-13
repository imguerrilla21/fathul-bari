import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.hadith_data_layer import HadithIngestionJob
from app.integrations.ahmad_sanusi.client import AhmadSanusiClient
from app.services.hadith_data_layer.hadith_repository import upsert_hadith_entity

logger = logging.getLogger("hadith_ingestion_service")


def run_batch_ingestion_job(db: Session, collection_slug: str = "bukhari", limit: int = 10) -> HadithIngestionJob:
    """
    Eksekusi Asynchronous Batch Ingestion Job dari Provider Ahmad Sanusi API:
    Mengambil data DTO ➔ Melakukan Validasi ➔ Arabic Normalization ➔ SHA-256 Content Hash ➔ Idempotent Upsert ke Database Local Index.
    """
    job = HadithIngestionJob(
        provider="ahmad_sanusi",
        collection=collection_slug,
        status="RUNNING",
        started_at=datetime.datetime.utcnow(),
        total_items=limit
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        client = AhmadSanusiClient()
        dtos = client.fetch_hadiths_by_collection(collection_slug=collection_slug, limit=limit)
        
        processed_count = 0
        for dto in dtos:
            upsert_hadith_entity(db, dto)
            processed_count += 1
            job.processed_items = processed_count
            db.commit()

        job.status = "COMPLETED"
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
    except Exception as err:
        job.status = "FAILED"
        job.error_message = str(err)
        db.commit()

    return job
