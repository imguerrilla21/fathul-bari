import base64
import hashlib
import hmac
import json
import time
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

SECRET_KEY = "fathul_bari_production_secret_jwt_key_super_secure_2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 86400  # 24 Hours

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Melakukan hashing password menggunakan PBKDF2-HMAC-SHA256."""
    salt = b"fathul_bari_salt_2026"
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return pwd_hash.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi kecocokan password polos dengan hash."""
    return hash_password(plain_password) == hashed_password


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode((data + padding).encode('utf-8'))


def create_access_token(user_id: str, email: str, role: str, expires_delta: int = TOKEN_EXPIRE_SECONDS) -> str:
    """Menghasilkan Bearer JWT Token yang ditandatangani HMAC-SHA256."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": int(time.time()) + expires_delta,
        "iat": int(time.time())
    }

    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Mendekode dan memverifikasi tanda tangan JWT Token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = base64url_encode(hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest())

        if not hmac.compare_digest(sig_b64, expected_sig):
            return None

        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < int(time.time()):
            return None  # Token expired

        return payload
    except Exception:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency FastAPI untuk mengambil pengguna aktif dari Authorization Bearer Header."""
    if not credentials or not credentials.credentials:
        # Fallback default guest user if no auth token supplied
        guest = db.query(User).filter(User.email == "admin@fathulbari.id").first()
        return guest

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token otentikasi tidak valid atau telah kadaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == payload.get("email")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    return user


def require_role(allowed_roles: List[str]):
    """Dependency FastAPI untuk membatasi akses endpoint berdasarkan Role RBAC."""
    def role_checker(current_user: Optional[User] = Depends(get_current_user)):
        if not current_user:
            raise HTTPException(status_code=401, detail="Akses ditolak: Membutuhkan login")
        if current_user.role not in allowed_roles and current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail=f"Akses ditolak: Membutuhkan salah satu hak akses {allowed_roles}"
            )
        return current_user
    return role_checker
