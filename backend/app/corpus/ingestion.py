from sqlalchemy.orm import Session
from app.models.ingestion import IngestionJobEntity, CorpusAuditEventEntity
from app.models.corpus import SourcePageEntity, SourcePassageEntity
from app.corpus.fingerprint import generate_passage_fingerprint
import time

def start_ingestion_job(db: Session, file_id: str, options: dict) -> IngestionJobEntity:
    """
    Synchronous mock ingestion pipeline for the starter app.
    In production, this would queue a job in Redis/BullMQ.
    """
    job = IngestionJobEntity(
        source_file_id=file_id,
        job_type="FULL_INGESTION",
        status="PROCESSING",
        total_units=100
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    try:
        # Mocking pipeline steps
        
        # 1. Page Extraction
        job.progress = 20
        db.commit()
        
        page = SourcePageEntity(
            volume_id="mock_vol_1",
            page_number=1,
            printed_page_number="1",
            image_path="mock/path/vol1_p1.jpg",
            image_checksum="dummy_checksum"
        )
        db.add(page)
        db.flush()
        
        # 2. OCR and Segmentation
        job.progress = 50
        db.commit()
        
        # 3. Create Passages
        passage = SourcePassageEntity(
            page_id=page.id,
            passage_type="BODY",
            sequence_number=1,
            display_text="قال ابن حجر",
            search_text="قال ابن حجر",
            verification_status="AI_SUGGESTION"
        )
        db.add(passage)
        db.flush()
        
        # 4. Audit Log
        audit = CorpusAuditEventEntity(
            source_id=passage.id,
            event_type="SEGMENTATION",
            actor_type="SYSTEM",
            actor_id="ingestion_worker_1",
            new_value={"text": "قال ابن حجر"}
        )
        db.add(audit)
        
        job.progress = 100
        job.processed_units = 100
        job.status = "COMPLETED"
        db.commit()
        
    except Exception as e:
        job.status = "FAILED"
        job.metadata_json = {"error": str(e)}
        db.commit()
        
    return job
