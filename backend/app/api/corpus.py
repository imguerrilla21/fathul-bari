from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.corpus.service import CorpusService
from app.corpus.ingestion import start_ingestion_job
from app.models.ingestion import IngestionJobEntity
from app.models.corpus import SourcePageEntity, SourcePassageEntity

router = APIRouter(prefix="/api/v1/corpus", tags=["corpus"])
svc = CorpusService()

class WorkRequest(BaseModel):
    title_ar: str
    author: str
    title_id: Optional[str] = None
    work_type: Optional[str] = "SHARH"
    description: Optional[str] = ""

class EditionRequest(BaseModel):
    work_id: str
    publisher: str
    editor: str
    year: int
    total_volumes: int
    edition_number: Optional[str] = "1"

class VolumeRequest(BaseModel):
    edition_id: str
    volume_number: int
    label: Optional[str] = None

class FileRequest(BaseModel):
    filename: str
    mime_type: str
    file_size: int
    checksum: str
    uploader: str

class IngestRequest(BaseModel):
    file_id: str
    work_id: str
    edition_id: str
    options: dict

@router.post("/works")
def create_work(req: WorkRequest, db: Session = Depends(get_db)):
    work = svc.create_work(db, req.title_ar, req.author, req.title_id, req.work_type, req.description)
    return {"id": work.id, "title_ar": work.title_ar}

@router.post("/editions")
def create_edition(req: EditionRequest, db: Session = Depends(get_db)):
    edition = svc.create_edition(db, req.work_id, req.publisher, req.editor, req.year, req.total_volumes, req.edition_number)
    return {"id": edition.id, "publisher": edition.publisher, "fingerprint": edition.metadata_json.get("fingerprint")}

@router.post("/volumes")
def create_volume(req: VolumeRequest, db: Session = Depends(get_db)):
    volume = svc.create_volume(db, req.edition_id, req.volume_number, req.label)
    return {"id": volume.id, "volume_number": volume.volume_number}

@router.post("/files")
def register_file(req: FileRequest, db: Session = Depends(get_db)):
    f = svc.register_source_file(db, req.filename, req.mime_type, req.file_size, req.checksum, req.uploader)
    return {"id": f.id, "filename": f.filename}

@router.post("/ingest")
def trigger_ingestion(req: IngestRequest, db: Session = Depends(get_db)):
    # Running synchronously for mock purposes. 
    # In production, use background_tasks.add_task(start_ingestion_job, ...)
    job = start_ingestion_job(db, req.file_id, req.options)
    return {"job_id": job.id, "status": job.status}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(IngestionJobEntity).filter(IngestionJobEntity.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job.id, "status": job.status, "progress": job.progress}

@router.get("/pages/{page_id}")
def get_page(page_id: str, db: Session = Depends(get_db)):
    page = db.query(SourcePageEntity).filter(SourcePageEntity.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"id": page.id, "page_number": page.page_number}

@router.get("/passages/{passage_id}")
def get_passage(passage_id: str, db: Session = Depends(get_db)):
    passage = db.query(SourcePassageEntity).filter(SourcePassageEntity.id == passage_id).first()
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")
    return {"id": passage.id, "text": passage.display_text}
