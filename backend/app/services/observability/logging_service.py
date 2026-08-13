from sqlalchemy.orm import Session
from app.models.observability import RequestLogEntity, AIGenerationLogEntity, IncidentEntity
import time

def log_request(db: Session, trace_id: str, endpoint: str, request_type: str, status: str, start_time: float, user_id: str = None):
    latency = int((time.time() - start_time) * 1000)
    req_log = RequestLogEntity(
        trace_id=trace_id,
        user_id=user_id,
        endpoint=endpoint,
        request_type=request_type,
        status=status,
        latency_ms=latency
    )
    db.add(req_log)
    db.commit()
    db.refresh(req_log)
    return req_log

def log_ai_generation(db: Session, trace_id: str, model_name: str, model_version: str, prompt_version: str, retrieval_version: str, input_tokens: int, output_tokens: int, finish_reason: str, start_time: float):
    latency = int((time.time() - start_time) * 1000)
    ai_log = AIGenerationLogEntity(
        trace_id=trace_id,
        model_name=model_name,
        model_version=model_version,
        prompt_version=prompt_version,
        retrieval_version=retrieval_version,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        finish_reason=finish_reason,
        latency_ms=latency
    )
    db.add(ai_log)
    db.commit()
    db.refresh(ai_log)
    return ai_log

def report_incident(db: Session, incident_code: str, severity: str, component: str, description: str, trace_id: str = None):
    incident = IncidentEntity(
        incident_code=incident_code,
        severity=severity,
        component=component,
        description=description,
        trace_id=trace_id,
        status="DETECTED"
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
