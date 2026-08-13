import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class SystemWorkerJob(Base):
    """Model pelacak job worker latar belakang idempoten (Idempotent Async Worker Job)."""
    __tablename__ = "system_worker_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_key = Column(String(255), unique=True, index=True, nullable=False)
    job_type = Column(String(50), default="CORPUS_PIPELINE")  # OCR, NLP, MATCHING, EMBEDDING, CORPUS_PIPELINE
    status = Column(String(30), default="QUEUED", index=True) # QUEUED, RUNNING, PAUSED, FAILED, COMPLETED, CANCELLED
    progress_pct = Column(Integer, default=0)
    current_stage = Column(String(50), default="INGEST")
    error_log = Column(Text, nullable=True)
    pipeline_version = Column(String(30), default="17.0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ProductionMetricLog(Base):
    """Log metrik operasional Prometheus & OpenTelemetry telemetry."""
    __tablename__ = "production_metric_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(30), default="LATENCY")  # LATENCY, RECALL, CITATION_VALIDITY, ERROR_RATE
    unit = Column(String(20), default="ms")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)


class DatabaseMigrationLog(Base):
    """Log riwayat migrasi skema database Alembic."""
    __tablename__ = "database_migration_logs"

    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(String(64), nullable=False, index=True)
    version_num = Column(String(30), nullable=False)
    description = Column(String(255), nullable=False)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
