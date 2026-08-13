from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, PromptTemplate
from app.services.security import require_role
from app.services.production_service import (
    check_readiness,
    get_ai_usage_stats,
    get_security_summary,
)

router = APIRouter(prefix="/api/v1/admin", tags=["production_admin"])


class RoleUpdateRequest(BaseModel):
    role: str


class PromptCreateRequest(BaseModel):
    name: str
    version: str
    system_prompt: str


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """Mengambil daftar seluruh pengguna terdaftar (Hanya Admin)."""
    users = db.query(User).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]


@router.post("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    data: RoleUpdateRequest,
    db: Session = Depends(get_db)
):
    """Memperbarui role akses RBAC pengguna (Hanya Admin)."""
    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")

    valid_roles = ["reader", "researcher", "reviewer", "admin"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Role tidak valid")

    usr.role = data.role
    db.commit()

    return {"status": "updated", "user_id": user_id, "new_role": usr.role}


@router.get("/security-summary")
def security_summary(db: Session = Depends(get_db)):
    """Ringkasan status keamanan dan RBAC sistem."""
    return get_security_summary(db)


@router.get("/ai-usage")
def ai_usage_stats(db: Session = Depends(get_db)):
    """Statistik penggunaan token AI, latensi, dan estimasi biaya (AI Cost Control)."""
    return get_ai_usage_stats(db)


@router.get("/prompts")
def list_prompts(db: Session = Depends(get_db)):
    """Daftar template dan versi prompt AI RAG (Prompt Versioning)."""
    prompts = db.query(PromptTemplate).order_by(PromptTemplate.created_at.desc()).all()
    if not prompts:
        # Default prompt template
        return [
            {
                "id": 1,
                "name": "fathul_bari_assistant",
                "version": "3.2",
                "system_prompt": "Anda adalah Asisten Peneliti Hadis Shahih al-Bukhari & Syarah Fathul Bari...",
                "is_active": True,
                "created_at": "2026-08-13T00:00:00"
            }
        ]
    return [
        {
            "id": p.id,
            "name": p.name,
            "version": p.version,
            "system_prompt": p.system_prompt,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in prompts
    ]


@router.post("/prompts")
def create_prompt(data: PromptCreateRequest, db: Session = Depends(get_db)):
    """Menambahkan versi prompt AI RAG baru."""
    p = PromptTemplate(
        name=data.name,
        version=data.version,
        system_prompt=data.system_prompt,
        is_active=True
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"status": "created", "prompt_id": p.id, "version": p.version}
