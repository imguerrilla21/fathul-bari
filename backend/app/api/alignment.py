from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.alignment.service import AlignmentService
from app.models.alignment import HadithIdentityEntity

router = APIRouter(prefix="/api/v1/alignment", tags=["alignment"])
svc = AlignmentService()

class RegisterHadithRequest(BaseModel):
    external_source: str
    external_id: str
    collection: str
    hadith_number: str
    kitab: str
    bab: str
    arabic_matn: str

class RejectAlignmentRequest(BaseModel):
    reason: str

@router.post("/hadith/register")
def register_hadith(req: RegisterHadithRequest, db: Session = Depends(get_db)):
    identity = svc.register_hadith(
        db, req.external_source, req.external_id, req.collection, 
        req.hadith_number, req.kitab, req.bab, req.arabic_matn
    )
    return {"id": identity.id, "matn_fingerprint": identity.matn_fingerprint}

@router.post("/hadith/{hadith_id}")
def run_alignment_for_hadith(hadith_id: str, db: Session = Depends(get_db)):
    try:
        candidates = svc.run_alignment(db, hadith_id)
        return {
            "hadith_id": hadith_id,
            "status": "COMPLETED",
            "candidates": [{"alignment_id": c.id, "passage_id": c.passage_id, "score": float(c.score), "status": c.status} for c in candidates]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{alignment_id}/verify")
def verify_alignment(alignment_id: str, db: Session = Depends(get_db), x_user_id: str = Header("mock_scholar")):
    try:
        alignment = svc.verify_alignment(db, alignment_id, x_user_id)
        return {"alignment_id": alignment.id, "status": alignment.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{alignment_id}/reject")
def reject_alignment(alignment_id: str, req: RejectAlignmentRequest, db: Session = Depends(get_db), x_user_id: str = Header("mock_scholar")):
    try:
        alignment = svc.reject_alignment(db, alignment_id, req.reason, x_user_id)
        return {"alignment_id": alignment.id, "status": alignment.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
