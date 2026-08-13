from datetime import datetime, timezone
import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Collection, Hadith, Source, SyncRun
from app.services.ahmad_sanusi import AhmadSanusiClient
from app.services.hadith_normalizer import normalize_hadith

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class SyncRequest(BaseModel):
    collection_slug: str = Field(default="shahih_bukhari", description="Slug koleksi kitab")
    start: int = Field(default=1, ge=1, description="Nomor awal hadis")
    end: int = Field(default=10, ge=1, description="Nomor akhir hadis")


async def execute_sync_background(run_id: str, collection_slug: str, start: int, end: int):
    """Background task runner for hadith sync."""
    db: Session = SessionLocal()
    try:
        run = db.scalar(select(SyncRun).where(SyncRun.id == run_id))
        if not run:
            return

        source = db.scalar(select(Source).where(Source.name == "Ahmad Sanusi Hadits API"))
        collection = db.scalar(select(Collection).where(Collection.slug == collection_slug))

        if not source or not collection:
            run.status = "failed"
            run.error_message = "Source atau Collection belum di-seed."
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            return

        client = AhmadSanusiClient()

        for nomor in range(start, end + 1):
            try:
                payload = await client.get_hadith(collection_slug, nomor)
                data = payload.get("data")
                if not isinstance(data, dict):
                    raise ValueError(f"Response data tidak valid untuk #{nomor}")

                item = normalize_hadith(data)
                run.fetched += 1

                existing = db.scalar(select(Hadith).where(
                    Hadith.collection_id == collection.id,
                    Hadith.external_number == nomor,
                ))

                now = datetime.now(timezone.utc)
                if existing:
                    if existing.content_hash != item["content_hash"]:
                        existing.arabic_text = item["arabic_text"]
                        existing.translation = item["translation"]
                        existing.content_hash = item["content_hash"]
                        existing.retrieved_at = now
                        run.updated += 1
                else:
                    db.add(Hadith(
                        collection_id=collection.id,
                        source_id=source.id,
                        external_number=nomor,
                        arabic_text=item["arabic_text"],
                        translation=item["translation"],
                        content_hash=item["content_hash"],
                        api_endpoint=f"/v1/hadits/{collection_slug}/{nomor}",
                        retrieved_at=now,
                    ))
                    run.inserted += 1

                db.commit()
            except Exception as exc:
                db.rollback()
                run.failed += 1
                logger.warning("Sync failed for #%d: %s", nomor, exc)
                db.commit()

        run.status = "completed" if run.failed == 0 else "completed_with_errors"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        run = db.scalar(select(SyncRun).where(SyncRun.id == run_id))
        if run:
            run.status = "failed"
            run.error_message = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@router.post("/sync")
async def trigger_sync(
    req: SyncRequest,
    background_tasks: BackgroundTasks,
    sync_mode: str = Query(default="sync", enum=["sync", "async"], description="sync (tunggu hasil) atau async (background)"),
    db: Session = Depends(get_db),
):
    """Memicu proses sinkronisasi hadis dari Ahmad Sanusi API ke database lokal."""
    if req.end < req.start:
        raise HTTPException(status_code=400, detail="Nomor akhir harus lebih besar atau sama dengan nomor awal.")
    if req.end - req.start > 500 and sync_mode == "sync":
        sync_mode = "async"

    # Pastikan source & collection ada
    source = db.scalar(select(Source).where(Source.name == "Ahmad Sanusi Hadits API"))
    if not source:
        source = Source(name="Ahmad Sanusi Hadits API", source_type="api", base_url="https://api.ahmadsanusi.com")
        db.add(source)
        db.flush()

    collection = db.scalar(select(Collection).where(Collection.slug == req.collection_slug))
    if not collection:
        collection = Collection(
            slug=req.collection_slug,
            name="Shahih al-Bukhari" if req.collection_slug == "shahih_bukhari" else req.collection_slug.replace("_", " ").title(),
            language="id",
            total_expected=7008 if req.collection_slug == "shahih_bukhari" else None,
        )
        db.add(collection)
        db.flush()

    run = SyncRun(
        collection_slug=req.collection_slug,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if sync_mode == "async":
        background_tasks.add_task(execute_sync_background, run.id, req.collection_slug, req.start, req.end)
        return {
            "message": f"Sinkronisasi {req.collection_slug} #{req.start} - #{req.end} dimulai di background.",
            "run_id": str(run.id),
            "status": "running",
        }

    # Synchronous execution
    await execute_sync_background(run.id, req.collection_slug, req.start, req.end)
    db.refresh(run)
    return {
        "run_id": str(run.id),
        "status": run.status,
        "fetched": run.fetched,
        "inserted": run.inserted,
        "updated": run.updated,
        "failed": run.failed,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "error": run.error_message,
    }


@router.get("/data-quality")
def data_quality(db: Session = Depends(get_db)):
    collection = db.scalar(select(Collection).where(Collection.slug == "shahih_bukhari"))
    if not collection:
        return {"status": "not_initialized", "message": "Jalankan seed.py terlebih dahulu."}

    actual = int(db.scalar(
        select(func.count()).select_from(Hadith).where(Hadith.collection_id == collection.id)
    ) or 0)

    missing_arabic = int(db.scalar(
        select(func.count()).select_from(Hadith).where(
            Hadith.collection_id == collection.id,
            (Hadith.arabic_text.is_(None)) | (func.trim(Hadith.arabic_text) == "")
        )
    ) or 0)

    missing_translation = int(db.scalar(
        select(func.count()).select_from(Hadith).where(
            Hadith.collection_id == collection.id,
            (Hadith.translation.is_(None)) | (func.trim(Hadith.translation) == "")
        )
    ) or 0)

    total_runs = int(db.scalar(select(func.count()).select_from(SyncRun)) or 0)
    last_run = db.scalar(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1))

    expected = collection.total_expected or 7008
    progress_percent = round((actual / expected * 100), 2) if expected > 0 else 0

    return {
        "collection": collection.slug,
        "collection_name": collection.name,
        "expected": expected,
        "actual": actual,
        "progress_percent": progress_percent,
        "missing_arabic": missing_arabic,
        "missing_translation": missing_translation,
        "total_sync_runs": total_runs,
        "last_sync_run": {
            "id": str(last_run.id),
            "status": last_run.status,
            "started_at": last_run.started_at.isoformat() if last_run.started_at else None,
            "finished_at": last_run.finished_at.isoformat() if last_run.finished_at else None,
            "fetched": last_run.fetched,
            "inserted": last_run.inserted,
            "failed": last_run.failed,
        } if last_run else None,
        "status": "healthy" if actual >= expected and not missing_arabic and not missing_translation else "in_progress" if actual > 0 else "empty",
    }


@router.get("/sync-runs")
def sync_runs(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(SyncRun).order_by(SyncRun.started_at.desc()).limit(limit)
    )
    return [
        {
            "id": str(x.id),
            "collection": x.collection_slug,
            "status": x.status,
            "fetched": x.fetched,
            "inserted": x.inserted,
            "updated": x.updated,
            "failed": x.failed,
            "started_at": x.started_at.isoformat() if x.started_at else None,
            "finished_at": x.finished_at.isoformat() if x.finished_at else None,
            "error": x.error_message,
        }
        for x in rows
    ]

