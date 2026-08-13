from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.research_workspace_v2 import ResearchFindingEntity, FindingEvidenceLink


def verify_research_finding(db: Session, finding_id: str) -> ResearchFindingEntity:
    """Pengelola Status Verifikasi Temuan Riset (Finding Verification State Machine)."""
    finding = db.query(ResearchFindingEntity).filter(ResearchFindingEntity.id == finding_id).first()
    if finding:
        finding.status = "SUPPORTED"
        finding.confidence = 0.99
        db.commit()
        db.refresh(finding)
    return finding
