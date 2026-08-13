from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.research.executor import run_research

router = APIRouter(prefix="/api/v1/research", tags=["research"])

class ResearchRequest(BaseModel):
    question: str
    mode: str = "STANDARD"

@router.post("")
def create_research_session(req: ResearchRequest, db: Session = Depends(get_db)):
    """
    Executes a research query through the Research Engine.
    For MVP, this is a synchronous endpoint. In production, Deep Research uses SSE.
    """
    result = run_research(db, req.question, req.mode)
    return result
