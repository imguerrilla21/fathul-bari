from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.services.multimodal.page_service import get_page, get_page_regions, get_region_ocr
from app.services.multimodal.correction_service import submit_correction
from app.services.multimodal.multimodal_search import search_multimodal_blocks

router = APIRouter(prefix="/api/v1", tags=["multimodal-source"])

class CorrectionRequest(BaseModel):
    block_id: str
    corrected_text: str
    reviewer_id: str
    reason: Optional[str] = None

class MultimodalSearchRequest(BaseModel):
    query: str
    page_id: Optional[str] = None
    region_type: Optional[str] = None

@router.get("/source/pages/{page_id}")
def get_source_page(page_id: str, db: Session = Depends(get_db)):
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.get("/source/pages/{page_id}/regions")
def get_source_page_regions(page_id: str, db: Session = Depends(get_db)):
    regions = get_page_regions(db, page_id)
    return regions

@router.get("/source/regions/{region_id}/ocr")
def get_ocr_for_region(region_id: str, db: Session = Depends(get_db)):
    ocr = get_region_ocr(db, region_id)
    if not ocr:
        raise HTTPException(status_code=404, detail="OCR Block not found")
    return ocr

@router.post("/source/corrections")
def submit_ocr_correction(req: CorrectionRequest, db: Session = Depends(get_db)):
    try:
        correction, block = submit_correction(
            db=db,
            block_id=req.block_id,
            corrected_text=req.corrected_text,
            reviewer_id=req.reviewer_id,
            reason=req.reason
        )
        return {"status": "SUCCESS", "correction_id": correction.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rag/multimodal-search")
def run_multimodal_search(req: MultimodalSearchRequest, db: Session = Depends(get_db)):
    results = search_multimodal_blocks(
        db=db,
        query=req.query,
        page_id=req.page_id,
        region_type=req.region_type
    )
    return {"results": results}
