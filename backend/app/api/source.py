import json
import logging
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, Hadith, HadithSharhLink, SharhSection
from app.services.audit_logger import log_audit_event
from app.services.pdf_renderer import find_pdf_for_volume, render_pdf_page_image
from app.utils.db_helpers import to_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/source", tags=["Tahap 6 Source Viewer & Audit Trail"])


class CustomAuditRequest(BaseModel):
    action: str = Field(..., description="Nama aksi audit, misal 'CORRECTION', 'NOTE', 'SUPERSEDE'")
    actor: str = Field(default="reviewer", description="Nama/identitas reviewer")
    notes: str = Field(..., description="Catatan keputusan atau alasan koreksi")
    request_id: str | None = Field(default=None, description="Request ID opsional")


@router.get("/sections")
def get_source_sections(
    volume: int | None = Query(default=None, description="Filter nomor jilid"),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Mengambil daftar seluruh seksi ulasan Fathul Bari yang tersedia di database."""
    query = select(SharhSection)
    if volume:
        query = query.where(SharhSection.volume == volume)

    query = query.order_by(SharhSection.volume, SharhSection.printed_page, SharhSection.section_order).limit(limit)
    sections = list(db.scalars(query))

    items = []
    for s in sections:
        # Cek apakah seksi ini memiliki tautan terverifikasi
        links = list(db.scalars(select(HadithSharhLink).where(HadithSharhLink.sharh_section_id == s.id)))
        is_verified = any(l.verified for l in links)
        hadith_numbers = []
        for l in links:
            h = db.scalar(select(Hadith).where(Hadith.id == l.hadith_id))
            if h and h.external_number not in hadith_numbers:
                hadith_numbers.append(h.external_number)

        vol = s.volume or 1
        page_num = s.printed_page or s.pdf_page or s.page or 1
        has_pdf = find_pdf_for_volume(vol) is not None

        items.append({
            "sharh_id": str(s.id),
            "volume": vol,
            "printed_page": page_num,
            "pdf_page": s.pdf_page,
            "section_order": s.section_order,
            "title": s.title or f"Fathul Bari Jilid {vol} Hal. {page_num}",
            "arabic_snippet": (s.arabic_text[:160] + "...") if s.arabic_text and len(s.arabic_text) > 160 else s.arabic_text,
            "source_file": s.source_file,
            "pdf_available": has_pdf,
            "verified": is_verified,
            "review_status": "verified" if is_verified else ("review" if links else "unlinked"),
            "linked_hadith_numbers": hadith_numbers,
        })

    return {
        "total": len(items),
        "volume_filter": volume,
        "sections": items,
    }


@router.get("/sharh/{sharh_id}")
def get_source_metadata(sharh_id: str, db: Session = Depends(get_db)):
    """Mengambil metadata dokumen sumber primer untuk suatu seksi Fathul Bari."""
    uid = to_uuid(sharh_id)
    sec = db.scalar(select(SharhSection).where(SharhSection.id == uid)) if uid else None
    if not sec:
        raise HTTPException(status_code=404, detail="Seksi Syarah tidak ditemukan.")

    vol = sec.volume or 1
    page_num = sec.printed_page or sec.pdf_page or sec.page or 1

    pdf_file = find_pdf_for_volume(vol)
    has_pdf = pdf_file is not None and pdf_file.exists()
    pdf_size_bytes = pdf_file.stat().st_size if has_pdf else 0
    pdf_filename = pdf_file.name if has_pdf else None

    # Tentukan path dokumen sumber dan citra
    doc_path = sec.source_document_path or (str(pdf_file) if has_pdf else None)
    img_path = sec.page_image_path or f"/api/v1/source/sharh/{sec.id}/page-image"

    # Cari tautan hadis yang terhubung
    links = list(
        db.scalars(
            select(HadithSharhLink)
            .where(HadithSharhLink.sharh_section_id == sec.id)
            .order_by(desc(HadithSharhLink.confidence))
        )
    )

    linked_hadiths = []
    for l in links:
        h = db.scalar(select(Hadith).where(Hadith.id == l.hadith_id))
        if h:
            linked_hadiths.append({
                "link_id": str(l.id),
                "hadith_id": str(h.id),
                "hadith_number": h.external_number,
                "confidence": l.confidence,
                "verified": l.verified,
                "review_status": l.review_status,
                "notes": l.notes,
            })

    # Cek audit trail count
    audit_count = db.scalar(
        select(AuditLog)
        .where(AuditLog.entity_id == str(sec.id))
    )

    return {
        "sharh_id": str(sec.id),
        "work_slug": sec.work_slug,
        "work_title": "Fathul Bari Syarah Shahih al-Bukhari",
        "author": "Al-Hafizh Ibnu Hajar al-Asqalani (773–852 H)",
        "volume": vol,
        "printed_page": sec.printed_page,
        "pdf_page": sec.pdf_page,
        "page": page_num,
        "section_order": sec.section_order,
        "title": sec.title,
        "source_file": sec.source_file,
        "source_hash": sec.source_hash,
        "source_document_path": doc_path,
        "page_image_path": img_path,
        "pdf_available": has_pdf,
        "pdf_filename": pdf_filename,
        "pdf_size_bytes": pdf_size_bytes,
        "pdf_size_mb": round(pdf_size_bytes / (1024 * 1024), 2) if has_pdf else 0,
        "document_download_url": f"/api/v1/source/sharh/{sec.id}/document",
        "page_image_url": f"/api/v1/source/sharh/{sec.id}/page-image",
        "linked_hadiths": linked_hadiths,
    }


@router.get("/sharh/{sharh_id}/document")
def download_source_document(sharh_id: str, db: Session = Depends(get_db)):
    """Mengunduh atau menampilkan berkas PDF sumber primer asli dari server."""
    uid = to_uuid(sharh_id)
    sec = db.scalar(select(SharhSection).where(SharhSection.id == uid)) if uid else None
    if not sec:
        raise HTTPException(status_code=404, detail="Seksi Syarah tidak ditemukan.")

    vol = sec.volume or 1
    pdf_file = find_pdf_for_volume(vol)
    if not pdf_file or not pdf_file.exists():
        # Coba periksa file txt raw
        txt_file = Path(f"data/fathul_bari/raw/fathul_bari_jilid_{vol:02d}.txt")
        if txt_file.exists():
            return FileResponse(
                path=txt_file,
                media_type="text/plain; charset=utf-8",
                filename=txt_file.name,
            )
        raise HTTPException(status_code=404, detail=f"Dokumen sumber untuk Jilid {vol} tidak ditemukan di server.")

    return FileResponse(
        path=pdf_file,
        media_type="application/pdf",
        filename=pdf_file.name,
    )


@router.get("/sharh/{sharh_id}/page-image")
def get_source_page_image(sharh_id: str, db: Session = Depends(get_db)):
    """Mengambil citra halaman visual PNG dari naskah/PDF Fathul Bari untuk verifikasi langsung."""
    uid = to_uuid(sharh_id)
    sec = db.scalar(select(SharhSection).where(SharhSection.id == uid)) if uid else None
    if not sec:
        raise HTTPException(status_code=404, detail="Seksi Syarah tidak ditemukan.")

    vol = sec.volume or 1
    pdf_page = sec.pdf_page or sec.printed_page or 1
    printed_page = sec.printed_page or pdf_page

    img_path = render_pdf_page_image(
        volume=vol,
        pdf_page=pdf_page,
        printed_page=printed_page,
        text_content=sec.arabic_text or sec.title,
    )

    if not img_path or not img_path.exists():
        raise HTTPException(status_code=500, detail="Gagal merender citra halaman sumber.")

    return FileResponse(
        path=img_path,
        media_type="image/png",
        filename=img_path.name,
    )


@router.get("/audit/sharh_section/{sharh_id}")
def get_sharh_section_audit_trail(sharh_id: str, db: Session = Depends(get_db)):
    """Mengambil jejak audit (*audit trail*) immutable untuk seksi ulasan Fathul Bari."""
    logs = list(
        db.scalars(
            select(AuditLog)
            .where(
                (AuditLog.entity_id == sharh_id)
                | (AuditLog.entity_type == "sharh_section")
            )
            .order_by(desc(AuditLog.created_at))
            .limit(100)
        )
    )

    events = []
    for log in logs:
        if str(log.entity_id) == str(sharh_id):
            events.append({
                "id": str(log.id),
                "action": log.action,
                "actor": log.actor,
                "request_id": log.request_id,
                "before_state": json.loads(log.before_state) if log.before_state and log.before_state.startswith("{") else log.before_state,
                "after_state": json.loads(log.after_state) if log.after_state and log.after_state.startswith("{") else log.after_state,
                "notes": log.notes,
                "created_at": log.created_at.isoformat(),
            })

    return {
        "sharh_id": sharh_id,
        "total_events": len(events),
        "audit_trail": events,
    }


@router.get("/audit/link/{link_id}")
def get_link_audit_trail(link_id: str, db: Session = Depends(get_db)):
    """Mengambil jejak audit immutable untuk tautan hadis – syarah tertentu."""
    logs = list(
        db.scalars(
            select(AuditLog)
            .where(
                AuditLog.entity_id == link_id,
                AuditLog.entity_type == "hadith_sharh_link",
            )
            .order_by(desc(AuditLog.created_at))
        )
    )

    events = []
    for log in logs:
        events.append({
            "id": str(log.id),
            "action": log.action,
            "actor": log.actor,
            "request_id": log.request_id,
            "before_state": json.loads(log.before_state) if log.before_state and log.before_state.startswith("{") else log.before_state,
            "after_state": json.loads(log.after_state) if log.after_state and log.after_state.startswith("{") else log.after_state,
            "notes": log.notes,
            "created_at": log.created_at.isoformat(),
        })

    return {
        "link_id": link_id,
        "total_events": len(events),
        "audit_trail": events,
    }


@router.get("/audit/recent")
def get_recent_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None, description="Filter aksi, misal: VERIFY, REJECT, INGEST"),
    actor: str | None = Query(default=None, description="Filter aktor reviewer"),
    db: Session = Depends(get_db),
):
    """Mengambil daftar event audit trail terbaru pada platform."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    if action:
        query = query.where(AuditLog.action == action.upper())
    if actor:
        query = query.where(AuditLog.actor.ilike(f"%{actor}%"))

    logs = list(db.scalars(query.limit(limit)))

    items = []
    for log in logs:
        items.append({
            "id": str(log.id),
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "actor": log.actor,
            "request_id": log.request_id,
            "notes": log.notes,
            "created_at": log.created_at.isoformat(),
        })

    return {
        "total": len(items),
        "limit": limit,
        "items": items,
    }


@router.post("/audit/link/{link_id}/event")
def create_custom_link_audit_event(
    link_id: str,
    req: CustomAuditRequest,
    db: Session = Depends(get_db),
):
    """Menambahkan entri audit kustom (misal koreksi/supersede catatan) tanpa mengubah riwayat lama."""
    uid = to_uuid(link_id)
    link = db.scalar(select(HadithSharhLink).where(HadithSharhLink.id == uid)) if uid else None
    if not link:
        raise HTTPException(status_code=404, detail="Tautan Hadits–Syarah tidak ditemukan.")

    entry = log_audit_event(
        db=db,
        entity_type="hadith_sharh_link",
        entity_id=link.id,
        action=req.action,
        actor=req.actor,
        request_id=req.request_id,
        before_state={"review_status": link.review_status, "verified": link.verified, "notes": link.notes},
        after_state={"review_status": link.review_status, "verified": link.verified, "notes": req.notes},
        notes=req.notes,
        auto_commit=True,
    )

    return {
        "status": "success",
        "audit_id": str(entry.id),
        "action": entry.action,
        "message": "Event audit berhasil dicatat ke dalam audit trail immutable.",
    }
