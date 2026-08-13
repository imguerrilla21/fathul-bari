from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.database import get_db
from app.models.analytics import EvaluationQuery
from app.services.evaluation_runner import (
    run_retrieval_evaluation,
    get_evaluation_queries,
    get_evaluation_history,
)

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


class EvaluationQueryCreate(BaseModel):
    query: str
    category: str = "General"
    expected_hadith_ids: List[int] = []
    expected_sharh_ids: List[int] = []


@router.get("/queries")
def list_queries(db: Session = Depends(get_db)):
    """Mengambil daftar seluruh pertanyaan pengujian standar (Golden Dataset)."""
    return get_evaluation_queries(db)


@router.post("/queries")
def create_query(data: EvaluationQueryCreate, db: Session = Depends(get_db)):
    """Menambahkan pertanyaan baru ke dalam Golden Dataset."""
    eq = EvaluationQuery(
        query=data.query,
        category=data.category,
        expected_hadith_ids=data.expected_hadith_ids,
        expected_sharh_ids=data.expected_sharh_ids
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return {"status": "created", "query_id": eq.id}


@router.post("/run")
def execute_evaluation(db: Session = Depends(get_db)):
    """Menjalankan benchmark pengujian retrieval & RAG di seluruh Golden Dataset."""
    results = run_retrieval_evaluation(db)
    return results


@router.get("/results")
def list_results(db: Session = Depends(get_db)):
    """Histori hasil eksekusi pengujian benchmark."""
    return get_evaluation_history(db)
