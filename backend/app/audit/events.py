from sqlalchemy.orm import Session
from app.models.audit import AuditEventEntity
from typing import Dict, Any, Optional

def log_audit_event(
    db: Session,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None
) -> AuditEventEntity:
    """
    Writes an immutable record to the audit trail.
    """
    event = AuditEventEntity(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        reason=reason
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
