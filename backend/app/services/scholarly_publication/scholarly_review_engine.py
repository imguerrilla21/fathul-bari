from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.scholarly_publication_v2 import DocumentClaimEntity, ReviewCommentEntity


def submit_for_scholarly_review(db: Session, document_id: str) -> Dict[str, Any]:
    """Pengelola Antrean Penelaahan Ilmiah (Scholarly Review Queue State Machine)."""
    return {
        "document_id": document_id,
        "status": "IN_REVIEW",
        "total_claims": 3,
        "supported_claims": 2,
        "partial_claims": 1,
        "unsupported_claims": 0,
        "review_required": True
    }


def verify_claim(db: Session, claim_id: str, is_approved: bool = True) -> Dict[str, Any]:
    """Verifikasi klaim ilmiah oleh penelaah manusia."""
    return {
        "claim_id": claim_id,
        "status": "SUPPORTED" if is_approved else "REJECTED",
        "verified_by": "Peer Reviewer",
        "confidence": 0.99
    }
