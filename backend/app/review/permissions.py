from enum import Enum
from typing import Dict, List

class ReviewerRole(str, Enum):
    VIEWER = "VIEWER"
    RESEARCHER = "RESEARCHER"
    REVIEWER = "REVIEWER"
    SCHOLAR = "SCHOLAR"
    EDITOR = "EDITOR"
    ADMIN = "ADMIN"

# Simple logical RBAC implementation
ROLE_PERMISSIONS = {
    ReviewerRole.VIEWER: ["read_source"],
    ReviewerRole.RESEARCHER: ["read_source", "create_research"],
    ReviewerRole.REVIEWER: ["read_source", "create_research", "verify_evidence"],
    ReviewerRole.SCHOLAR: ["read_source", "create_research", "verify_evidence", "verify_isnad", "verify_claim"],
    ReviewerRole.EDITOR: ["read_source", "create_research", "verify_evidence", "verify_isnad", "verify_claim", "approve_publication"],
    ReviewerRole.ADMIN: ["read_source", "create_research", "verify_evidence", "verify_isnad", "verify_claim", "approve_publication", "edit_taxonomy"]
}

def has_permission(user_role: str, action: str) -> bool:
    """Check if a specific role has permission to perform an action."""
    role_enum = ReviewerRole(user_role)
    return action in ROLE_PERMISSIONS.get(role_enum, [])

def require_permission(user_role: str, action: str):
    """Raise exception if permission is denied."""
    if not has_permission(user_role, action):
        raise Exception(f"Permission denied. Role '{user_role}' cannot perform '{action}'")
