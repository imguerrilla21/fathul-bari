from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.observability.evaluation_service import get_latest_quality_gate, simulate_evaluation_run, get_recent_runs
from app.services.observability.logging_service import log_request, log_ai_generation, report_incident
from pydantic import BaseModel

router = APIRouter()

# Health endpoints
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "ok",
        "vector_store": "ok",
        "search": "ok",
        "llm": "ok",
        "storage": "ok"
    }

@router.get("/ready")
def readiness_check():
    return {
        "status": "ready"
    }

# Quality Gate
@router.get("/quality/gate")
def quality_gate(db: Session = Depends(get_db)):
    return get_latest_quality_gate(db)

# Evaluation APIs
@router.post("/evaluation/run")
def trigger_evaluation(db: Session = Depends(get_db)):
    run = simulate_evaluation_run(db)
    return run

@router.get("/evaluation/runs")
def list_eval_runs(db: Session = Depends(get_db)):
    return get_recent_runs(db)

# Telemetry Injection (for testing)
class SimRequestLog(BaseModel):
    trace_id: str
    endpoint: str
    request_type: str
    status: str
    start_time: float

@router.post("/telemetry/request")
def inject_request_log(req: SimRequestLog, db: Session = Depends(get_db)):
    return log_request(db, req.trace_id, req.endpoint, req.request_type, req.status, req.start_time)

class SimAILog(BaseModel):
    trace_id: str
    model_name: str
    model_version: str
    prompt_version: str
    retrieval_version: str
    input_tokens: int
    output_tokens: int
    finish_reason: str
    start_time: float

@router.post("/telemetry/ai_generation")
def inject_ai_log(req: SimAILog, db: Session = Depends(get_db)):
    return log_ai_generation(db, req.trace_id, req.model_name, req.model_version, req.prompt_version, req.retrieval_version, req.input_tokens, req.output_tokens, req.finish_reason, req.start_time)

class SimIncident(BaseModel):
    incident_code: str
    severity: str
    component: str
    description: str
    trace_id: str = None

@router.post("/telemetry/incident")
def inject_incident(req: SimIncident, db: Session = Depends(get_db)):
    return report_incident(db, req.incident_code, req.severity, req.component, req.description, req.trace_id)
