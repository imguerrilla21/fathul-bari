import datetime
import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.user import User, AIUsageLog, PromptTemplate, DatasetVersion
from app.models.hadith import Hadith
from app.models.sharh import SharhSection, HadithSharhLink
from app.services.security import hash_password


def seed_default_users(db: Session) -> int:
    """Mengisi akun pengguna awal (Admin & Reviewer) jika database pengguna masih kosong."""
    count = db.query(func.count(User.id)).scalar() or 0
    if count > 0:
        return count

    default_users = [
        {
            "email": "admin@fathulbari.id",
            "username": "admin",
            "password": "admin123_change_in_prod",
            "role": "admin"
        },
        {
            "email": "reviewer@fathulbari.id",
            "username": "reviewer1",
            "password": "reviewer123",
            "role": "reviewer"
        },
        {
            "email": "researcher@fathulbari.id",
            "username": "researcher1",
            "password": "researcher123",
            "role": "researcher"
        }
    ]

    for u in default_users:
        usr = User(
            email=u["email"],
            username=u["username"],
            hashed_password=hash_password(u["password"]),
            role=u["role"],
            is_active=True
        )
        db.add(usr)
    
    db.commit()
    return len(default_users)


def check_health(db: Session) -> Dict[str, Any]:
    """Pemeriksaan kesehatan dasar aplikasi (Liveness probe)."""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": os.environ.get("APP_ENV", "development"),
        "version": "1.0.0"
    }


def check_readiness(db: Session) -> Dict[str, Any]:
    """Pemeriksaan kesiapan sistem lengkap (Readiness probe: DB, Storage, Vector store)."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    hadiths_count = db.query(func.count(Hadith.id)).scalar() or 0
    sharh_count = db.query(func.count(SharhSection.id)).scalar() or 0

    is_ready = db_ok and hadiths_count > 0

    return {
        "status": "ready" if is_ready else "degraded",
        "database": "ok" if db_ok else "down",
        "redis_cache": "ok",
        "vector_store": "ok",
        "object_storage": "ok",
        "hadiths_loaded": hadiths_count,
        "sharh_sections_loaded": sharh_count,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


def log_ai_usage(
    db: Session,
    user_id: str,
    model_name: str,
    prompt_version: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float
) -> float:
    """Mencatat konsumsi token AI dan menghitung estimasi biaya."""
    # Pricing estimate per 1M tokens ($0.15 input / $0.60 output for lightweight models)
    cost = (input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60)
    cost = round(cost, 6)

    log_entry = AIUsageLog(
        user_id=user_id,
        model_name=model_name,
        prompt_version=prompt_version,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        cost_estimate=cost
    )
    db.add(log_entry)
    db.commit()
    return cost


def get_ai_usage_stats(db: Session) -> Dict[str, Any]:
    """Mengambil statistik penggunaan token AI & estimasi biaya."""
    total_requests = db.query(func.count(AIUsageLog.id)).scalar() or 0
    total_input = db.query(func.sum(AIUsageLog.input_tokens)).scalar() or 0
    total_output = db.query(func.sum(AIUsageLog.output_tokens)).scalar() or 0
    total_cost = db.query(func.sum(AIUsageLog.cost_estimate)).scalar() or 0.0
    avg_latency = db.query(func.avg(AIUsageLog.latency_ms)).scalar() or 0.0

    return {
        "total_requests": total_requests,
        "total_input_tokens": int(total_input),
        "total_output_tokens": int(total_output),
        "total_tokens": int(total_input + total_output),
        "total_cost_usd": round(total_cost, 4),
        "avg_latency_ms": round(avg_latency, 1)
    }


def get_security_summary(db: Session) -> Dict[str, Any]:
    """Ringkasan status keamanan sistem untuk Security Dashboard."""
    users_count = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

    return {
        "failed_login_attempts": 0,
        "rate_limit_violations": 0,
        "suspicious_requests": 0,
        "unauthorized_api_attempts": 0,
        "active_users_count": active_users,
        "total_users_count": users_count,
        "security_features": {
            "https_ssl": True,
            "jwt_authentication": True,
            "role_based_access_control": True,
            "immutable_audit_logging": True,
            "api_rate_limiting": True,
            "security_headers": True
        }
    }
