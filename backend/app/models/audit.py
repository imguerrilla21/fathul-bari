import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, String, Text, Uuid, Column, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """Tabel immutable audit trail untuk melacak setiap keputusan penelitian, verifikasi, dan modifikasi data."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "sharh_section", "hadith_sharh_link", "hadith"
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "VERIFY", "REJECT", "AUTO_MATCH", "UPDATE", "INGEST", "CORRECTION"
    actor: Mapped[str] = mapped_column(String(100), default="system", nullable=False, index=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    before_state: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON Snapshot
    after_state: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON Snapshot
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

class AuditEventEntity(Base):
    __tablename__ = "audit_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(36), nullable=False)
    action = Column(String(100), nullable=False) # e.g. VERIFY_CLAIM, REJECT_EVIDENCE
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
