from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.review.service import ReviewService

router = APIRouter(prefix="/api/v1/scholarly_review", tags=["scholarly_review"])

class VerifyRequest(BaseModel):
    notes: Optional[str] = ""

class RejectRequest(BaseModel):
    reason: str

class CorrectRequest(BaseModel):
    corrected_text: str
    reason: str

def get_current_reviewer_role(x_user_role: str = Header(default="SCHOLAR", alias="X-User-Role")):
    """Mock dependency to extract user role from header for MVP."""
    return x_user_role
    
def get_current_reviewer_id(x_user_id: str = Header(default="mock_reviewer_123", alias="X-User-ID")):
    """Mock dependency to extract user ID from header for MVP."""
    return x_user_id

@router.post("/claims/{claim_id}/verify")
def verify_claim_endpoint(
    claim_id: str, 
    req: VerifyRequest, 
    db: Session = Depends(get_db),
    role: str = Depends(get_current_reviewer_role),
    user_id: str = Depends(get_current_reviewer_id)
):
    svc = ReviewService()
    try:
        claim = svc.verify_claim(db, claim_id, user_id, role, req.notes)
        return {"status": "success", "claim_id": claim.id, "new_status": claim.validation_status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/claims/{claim_id}/reject")
def reject_claim_endpoint(
    claim_id: str, 
    req: RejectRequest, 
    db: Session = Depends(get_db),
    role: str = Depends(get_current_reviewer_role),
    user_id: str = Depends(get_current_reviewer_id)
):
    svc = ReviewService()
    try:
        claim = svc.reject_claim(db, claim_id, user_id, role, req.reason)
        return {"status": "success", "claim_id": claim.id, "new_status": claim.validation_status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/claims/{claim_id}/correct")
def correct_claim_endpoint(
    claim_id: str, 
    req: CorrectRequest, 
    db: Session = Depends(get_db),
    role: str = Depends(get_current_reviewer_role),
    user_id: str = Depends(get_current_reviewer_id)
):
    svc = ReviewService()
    try:
        claim = svc.correct_claim(db, claim_id, user_id, role, req.corrected_text, req.reason)
        return {"status": "success", "claim_id": claim.id, "new_status": claim.validation_status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
