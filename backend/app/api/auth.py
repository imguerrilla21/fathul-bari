import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

from app.database import get_db
from app.models.user import User
from app.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    role: str = "reader"


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Otentikasi pengguna dan penerbitan Bearer JWT Token."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password tidak cocok"
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun pengguna dinonaktifkan")

    user.last_login_at = datetime.datetime.utcnow()
    db.commit()

    token = create_access_token(user_id=str(user.id), email=user.email, role=user.role)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role
        }
    }


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Pendaftaran akun pengguna baru."""
    existing = db.query(User).filter((User.email == data.email) | (User.username == data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email atau username sudah terdaftar")

    valid_roles = ["reader", "researcher", "reviewer", "admin"]
    role = data.role if data.role in valid_roles else "reader"

    usr = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        role=role,
        is_active=True
    )
    db.add(usr)
    db.commit()
    db.refresh(usr)

    return {"status": "created", "user_id": str(usr.id), "email": usr.email, "role": usr.role}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Mengambil informasi pengguna yang sedang login."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Belum otentikasi")

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
    }
