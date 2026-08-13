from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.services.analytics_service import (
    get_overview_analytics,
    get_coverage_analytics,
    get_confidence_analytics,
    get_reviewer_performance,
    get_inter_rater_agreement,
    detect_and_get_quality_issues,
    resolve_quality_issue,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    """Ringkasan eksekutif seluruh data penelitian dan cakupan status verifikasi."""
    return get_overview_analytics(db)


@router.get("/coverage")
def coverage(db: Session = Depends(get_db)):
    """Statistik cakupan dataset hadis dan syarah per volume."""
    return get_coverage_analytics(db)


@router.get("/confidence")
def confidence(db: Session = Depends(get_db)):
    """Distribusi confidence score & kurva kalibrasi (predicted confidence vs actual rate)."""
    return get_confidence_analytics(db)


@router.get("/reviewer-performance")
def reviewer_performance(db: Session = Depends(get_db)):
    """Analisis performa, rasio persetujuan, dan statistik beban kerja reviewer."""
    return get_reviewer_performance(db)


@router.get("/inter-rater-agreement")
def inter_rater_agreement(db: Session = Depends(get_db)):
    """Analisis konsistensi antar verifikator menggunakan Cohen's Kappa Coefficient."""
    return get_inter_rater_agreement(db)


@router.get("/issues")
def quality_issues(db: Session = Depends(get_db)):
    """Deteksi otomatis bendera & isu kualitas data (Quality Flags Pipeline)."""
    return detect_and_get_quality_issues(db)


@router.post("/issues/{issue_id}/resolve")
def resolve_issue(
    issue_id: str,
    status: str = Query("resolved", enum=["resolved", "ignored"]),
    db: Session = Depends(get_db)
):
    """Menandai isu kualitas data sebagai terlesaikan atau diabaikan."""
    success = resolve_quality_issue(db, issue_id, status)
    return {"status": "ok", "issue_id": issue_id, "resolved_status": status, "success": success}
