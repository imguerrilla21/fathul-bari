import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class RequestLogEntity(Base):
    __tablename__ = "request_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(Text, nullable=False)
    user_id = Column(String(36), nullable=True)
    endpoint = Column(Text, nullable=True)
    request_type = Column(String(50), nullable=True)
    status = Column(String(30), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class AIGenerationLogEntity(Base):
    __tablename__ = "ai_generation_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(Text, nullable=True)
    model_name = Column(Text, nullable=True)
    model_version = Column(Text, nullable=True)
    prompt_version = Column(Text, nullable=True)
    retrieval_version = Column(Text, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    finish_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class EvaluationCaseEntity(Base):
    __tablename__ = "evaluation_cases"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(Text, unique=True, nullable=True)
    category = Column(String(50), nullable=True)
    question = Column(Text, nullable=False)
    expected = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class EvaluationRunEntity(Base):
    __tablename__ = "evaluation_runs_v2" # using v2 to avoid conflict with analytics.py if any
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=True)
    model_version = Column(Text, nullable=True)
    prompt_version = Column(Text, nullable=True)
    retrieval_version = Column(Text, nullable=True)
    dataset_version = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    results = Column(JSON, nullable=True)

class EvaluationResultEntity(Base):
    __tablename__ = "evaluation_results"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), nullable=True)
    case_id = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    metrics = Column(JSON, nullable=True)
    failure_reason = Column(Text, nullable=True)

class IncidentEntity(Base):
    __tablename__ = "incidents"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_code = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)
    component = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    trace_id = Column(Text, nullable=True)
    status = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
