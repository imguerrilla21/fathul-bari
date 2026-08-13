import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, JSON, Uuid
from app.database import Base


class User(Base):
    """Model Pengguna sistem dengan Role-Based Access Control (RBAC)."""
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default="reader", nullable=False)  # reader, researcher, reviewer, admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)


class AIUsageLog(Base):
    """Pencatatan penggunaan token, latensi, dan estimasi biaya AI (AI Cost Control)."""
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True)
    model_name = Column(String(100), default="gemini-1.5-flash")
    prompt_version = Column(String(50), default="1.0")
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    cost_estimate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PromptTemplate(Base):
    """Pengelolaan & versioning prompt AI RAG (Prompt Versioning)."""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    version = Column(String(20), nullable=False)
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DatasetVersion(Base):
    """Pencatatan versi korpus data Fathul Bari & checksum (Data Versioning)."""
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    imported_hadiths = Column(Integer, default=0)
    verified_links = Column(Integer, default=0)
    sha256_checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
