from sqlalchemy.orm import Session
from app.models.observability import EvaluationCaseEntity, EvaluationRunEntity, EvaluationResultEntity
from datetime import datetime, timezone
import json

def get_latest_quality_gate(db: Session):
    run = db.query(EvaluationRunEntity).order_by(EvaluationRunEntity.started_at.desc()).first()
    if not run:
        return {
            "status": "UNKNOWN",
            "checks": {
                "retrieval": False,
                "citation": False,
                "attribution": False,
                "hallucination": False
            }
        }
    
    return {
        "status": "PASS" if run.results.get("overall_pass", False) else "FAIL",
        "checks": run.results.get("checks", {})
    }

def get_recent_runs(db: Session, limit: int = 10):
    return db.query(EvaluationRunEntity).order_by(EvaluationRunEntity.started_at.desc()).limit(limit).all()

def simulate_evaluation_run(db: Session):
    # This simulates running a full evaluation suite against the golden dataset
    run = EvaluationRunEntity(
        name="Nightly RAG Evaluation",
        model_version="gpt-4-turbo-v1",
        prompt_version="research-v3",
        retrieval_version="rag-v8",
        dataset_version="eval-v4",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        results={
            "overall_pass": True,
            "checks": {
                "retrieval": True,
                "citation": True,
                "attribution": True,
                "hallucination": True
            },
            "metrics": {
                "retrieval_recall": 94.7,
                "citation_precision": 97.1,
                "attribution_accuracy": 99.0,
                "unsupported_claims": 1.2
            }
        }
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
