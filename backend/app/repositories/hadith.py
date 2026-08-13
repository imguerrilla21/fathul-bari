from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Collection, Hadith, Source


def get_hadith(db: Session, kitab: str, nomor: int) -> Hadith | None:
    collection = db.scalar(select(Collection).where(Collection.slug == kitab))
    if not collection:
        return None
    return db.scalar(
        select(Hadith).where(
            Hadith.collection_id == collection.id,
            Hadith.external_number == nomor,
        )
    )


def upsert_hadith(
    db: Session,
    collection_slug: str,
    external_number: int,
    arabic_text: str,
    translation: str,
    content_hash: str,
    api_endpoint: str | None = None,
    source_name: str = "Ahmad Sanusi Hadits API",
) -> tuple[Hadith, bool]:
    """Upsert hadith data. Returns (hadith_instance, is_created)."""
    source = db.scalar(select(Source).where(Source.name == source_name))
    if not source:
        source = Source(
            name=source_name,
            source_type="api",
            base_url="https://api.ahmadsanusi.com",
        )
        db.add(source)
        db.flush()

    collection = db.scalar(select(Collection).where(Collection.slug == collection_slug))
    if not collection:
        collection = Collection(
            slug=collection_slug,
            name="Shahih al-Bukhari" if collection_slug == "shahih_bukhari" else collection_slug.replace("_", " ").title(),
            language="id",
            total_expected=7008 if collection_slug == "shahih_bukhari" else None,
        )
        db.add(collection)
        db.flush()

    hadith = db.scalar(
        select(Hadith).where(
            Hadith.collection_id == collection.id,
            Hadith.external_number == external_number,
        )
    )

    now = datetime.now(timezone.utc)
    if hadith:
        hadith.arabic_text = arabic_text
        hadith.translation = translation
        hadith.content_hash = content_hash
        hadith.api_endpoint = api_endpoint or hadith.api_endpoint
        hadith.retrieved_at = now
        db.commit()
        db.refresh(hadith)
        return hadith, False

    hadith = Hadith(
        collection_id=collection.id,
        source_id=source.id,
        external_number=external_number,
        arabic_text=arabic_text,
        translation=translation,
        content_hash=content_hash,
        api_endpoint=api_endpoint or f"/v1/hadits/{collection_slug}/{external_number}",
        retrieved_at=now,
    )
    db.add(hadith)
    db.commit()
    db.refresh(hadith)
    return hadith, True


def search_hadiths(db: Session, query: str, limit: int = 20, offset: int = 0, kitab: str | None = None) -> tuple[list[Hadith], int]:
    pattern = f"%{query}%"
    stmt = select(Hadith).where(
        (Hadith.translation.ilike(pattern)) | (Hadith.arabic_text.ilike(pattern))
    )

    if kitab:
        collection = db.scalar(select(Collection).where(Collection.slug == kitab))
        if collection:
            stmt = stmt.where(Hadith.collection_id == collection.id)
        else:
            return [], 0

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(db.scalar(count_stmt) or 0)

    rows = list(
        db.scalars(
            stmt.order_by(Hadith.external_number)
            .offset(offset)
            .limit(min(limit, 100))
        )
    )
    return rows, total


def count_hadiths(db: Session, kitab: str) -> int:
    collection = db.scalar(select(Collection).where(Collection.slug == kitab))
    if not collection:
        return 0
    return int(db.scalar(
        select(func.count()).select_from(Hadith).where(Hadith.collection_id == collection.id)
    ) or 0)


def get_collections_summary(db: Session) -> list[dict]:
    collections = list(db.scalars(select(Collection).order_by(Collection.slug)))
    results = []
    for c in collections:
        actual_count = int(db.scalar(
            select(func.count()).select_from(Hadith).where(Hadith.collection_id == c.id)
        ) or 0)
        results.append({
            "id": str(c.id),
            "slug": c.slug,
            "name": c.name,
            "language": c.language,
            "total_expected": c.total_expected,
            "actual_count": actual_count,
            "progress_percent": round((actual_count / c.total_expected * 100), 2) if c.total_expected else None,
        })
    return results
