import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.hadith import (
    get_collections_summary,
    get_hadith,
    search_hadiths,
    upsert_hadith,
)
from app.services.ahmad_sanusi import AhmadSanusiClient, AhmadSanusiError
from app.services.hadith_normalizer import normalize_hadith

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hadith", tags=["Hadith"])


def serialize(h, synced_on_demand: bool = False):
    return {
        "id": str(h.id),
        "kitab": "shahih_bukhari",
        "nomor": h.external_number,
        "arab": h.arabic_text,
        "terjemah": h.translation,
        "content_hash": h.content_hash,
        "source": {
            "type": "ahmad_sanusi",
            "endpoint": h.api_endpoint,
            "retrieved_at": h.retrieved_at.isoformat() if h.retrieved_at else None,
            "synced_on_demand": synced_on_demand,
        },
    }


@router.get("/collections")
def list_collections(db: Session = Depends(get_db)):
    """Mengambil daftar kitab/koleksi hadis beserta statistik jumlah tersimpan."""
    return get_collections_summary(db)


@router.get("/search")
def search(
    q: str = Query(min_length=2, description="Kata kunci pencarian"),
    kitab: str | None = Query(default=None, description="Slug kitab (contoh: shahih_bukhari)"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Pencarian hadis di database lokal berdasarkan teks Arab atau terjemahan."""
    rows, total = search_hadiths(db, query=q, limit=limit, offset=offset, kitab=kitab)
    return {
        "query": q,
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [serialize(h) for h in rows],
    }


@router.get("/{kitab}/{nomor}")
async def read_hadith(
    kitab: str,
    nomor: int,
    auto_sync: bool = Query(default=True, description="Otomatis sinkronisasi dari Ahmad Sanusi API jika belum ada di lokal"),
    db: Session = Depends(get_db),
):
    """Mengambil hadis per nomor kitab. Jika belum ada di lokal dan auto_sync=true, otomatis proxy-sync ke Ahmad Sanusi API."""
    hadith = get_hadith(db, kitab, nomor)
    if hadith:
        return serialize(hadith, synced_on_demand=False)

    if not auto_sync:
        raise HTTPException(status_code=404, detail=f"Hadis {kitab} #{nomor} belum tersedia di database lokal.")

    # Proxy-sync on-demand ke Ahmad Sanusi Hadits API
    try:
        client = AhmadSanusiClient()
        payload = await client.get_hadith(kitab, nomor)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise HTTPException(status_code=404, detail=f"Data hadis #{nomor} tidak ditemukan pada API sumber.")

        item = normalize_hadith(data)
        saved_hadith, _ = upsert_hadith(
            db=db,
            collection_slug=kitab,
            external_number=nomor,
            arabic_text=item["arabic_text"],
            translation=item["translation"],
            content_hash=item["content_hash"],
            api_endpoint=f"/v1/hadits/{kitab}/{nomor}",
        )
        return serialize(saved_hadith, synced_on_demand=True)
    except AhmadSanusiError as exc:
        logger.warning("Gagal on-demand proxy sync hadis %s #%d: %s", kitab, nomor, exc)
        raise HTTPException(status_code=502, detail=f"Gagal mengambil hadis dari sumber eksternal: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error tidak terduga pada proxy sync: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")

