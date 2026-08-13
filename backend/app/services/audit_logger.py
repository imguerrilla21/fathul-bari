import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger("audit_logger")


def serialize_entity_state(obj: Any) -> str:
    """Mengubah state objek SQLAlchemy / dict menjadi string JSON yang konsisten."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return json.dumps(obj, ensure_ascii=False, default=str)
    
    # Objek SQLAlchemy model
    data = {}
    for col in getattr(obj, "__table__", {}).columns.keys():
        val = getattr(obj, col, None)
        if isinstance(val, (datetime, uuid.UUID)):
            data[col] = str(val)
        else:
            data[col] = val
    return json.dumps(data, ensure_ascii=False, default=str)


def log_audit_event(
    db: Session,
    entity_type: str,
    entity_id: str | uuid.UUID,
    action: str,
    actor: str = "system",
    request_id: str | None = None,
    before_state: Any = None,
    after_state: Any = None,
    notes: str | None = None,
    auto_commit: bool = False,
) -> AuditLog:
    """
    Mencatat event audit baru (append-only, immutable).
    Audit log tidak pernah diubah atau dihapus; setiap perubahan dicatat sebagai event baru.
    """
    clean_entity_id = str(entity_id)
    clean_before = serialize_entity_state(before_state) if before_state is not None else None
    clean_after = serialize_entity_state(after_state) if after_state is not None else None

    entry = AuditLog(
        id=uuid.uuid4(),
        entity_type=entity_type,
        entity_id=clean_entity_id,
        action=action.upper(),
        actor=actor or "system",
        request_id=str(request_id) if request_id else str(uuid.uuid4()),
        before_state=clean_before,
        after_state=clean_after,
        notes=notes,
        created_at=datetime.now(timezone.utc),
    )

    db.add(entry)
    if auto_commit:
        db.commit()
        db.refresh(entry)

    logger.info(
        "AUDIT EVENT: [%s] entity=%s:%s actor=%s req_id=%s",
        entry.action,
        entry.entity_type,
        entry.entity_id,
        entry.actor,
        entry.request_id,
    )
    return entry
