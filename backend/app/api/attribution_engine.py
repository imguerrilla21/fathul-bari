from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.services.attribution.scholar_service import get_scholar
from app.services.attribution.claim_extraction_service import analyze_attribution, get_attribution_graph
from app.services.attribution.attribution_validator import validate_attribution
from app.models.attribution import AttributedClaimEntity

router = APIRouter(prefix="/api/v1/attribution", tags=["attribution-engine"])

class AnalyzeRequest(BaseModel):
    passage_id: str
    text: str

class ValidateRequest(BaseModel):
    claim_id: str
    detected_speaker_id: str
    expected_speaker_id: str

@router.post("/analyze")
def analyze_passage_attribution(req: AnalyzeRequest, db: Session = Depends(get_db)):
    result = analyze_attribution(db, req.passage_id, req.text)
    return result

@router.get("/claims/{claim_id}")
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    claim = db.query(AttributedClaimEntity).filter(AttributedClaimEntity.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

@router.get("/scholar/{scholar_id}")
def get_scholar_profile(scholar_id: str, db: Session = Depends(get_db)):
    scholar = get_scholar(db, scholar_id)
    if not scholar:
        raise HTTPException(status_code=404, detail="Scholar not found")
    return scholar

@router.get("/graph/{passage_id}")
def get_passage_attribution_graph(passage_id: str, db: Session = Depends(get_db)):
    graph = get_attribution_graph(db, passage_id)
    return graph

@router.post("/verify")
def verify_attribution(req: ValidateRequest, db: Session = Depends(get_db)):
    audit = validate_attribution(
        db=db,
        claim_id=req.claim_id,
        detected_speaker_id=req.detected_speaker_id,
        expected_speaker_id=req.expected_speaker_id
    )
    return {"status": audit.status, "audit_id": audit.id}
