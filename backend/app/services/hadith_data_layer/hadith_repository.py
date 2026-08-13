import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.hadith_data_layer import HadithEntity, HadithSource, HadithCollection, HadithBook
from app.integrations.ahmad_sanusi.schemas import HadithDTO
from app.services.hadith_data_layer.arabic_normalizer import normalize_arabic_text, generate_search_text, calculate_content_hash

logger = logging.getLogger("hadith_repository")


def seed_sources_and_collections_if_empty(db: Session):
    """Membuat entitas Source & Collection bawaan jika belum ada."""
    src = db.query(HadithSource).filter(HadithSource.provider == "ahmad_sanusi").first()
    if not src:
        src = HadithSource(
            name="Ahmad Sanusi Hadits API",
            provider="ahmad_sanusi",
            source_type="API",
            base_url="https://api.hadith.sutanlab.id/books"
        )
        db.add(src)
        db.commit()
        db.refresh(src)

    col = db.query(HadithCollection).filter(HadithCollection.slug == "bukhari").first()
    if not col:
        col = HadithCollection(
            source_id=src.id,
            slug="bukhari",
            name_ar="صحيح البخاري",
            name_id="Sahih al-Bukhari"
        )
        db.add(col)
        db.commit()


def upsert_hadith_entity(db: Session, dto: HadithDTO) -> HadithEntity:
    """
    Idempotent Upsert Entity:
    Memeriksa external_id (contoh: ahmad-sanusi:bukhari:1).
    Jika sudah ada ➔ perbarui hash & metadata. Jika belum ➔ insert baru.
    """
    seed_sources_and_collections_if_empty(db)
    
    norm_ar = normalize_arabic_text(dto.arabic_text)
    srch_text = generate_search_text(dto.arabic_text, dto.narrator_text, dto.hadith_number)
    c_hash = calculate_content_hash(dto.arabic_text)

    existing = db.query(HadithEntity).filter(HadithEntity.external_id == dto.external_id).first()
    
    if existing:
        existing.arabic_text = dto.arabic_text
        existing.normalized_text = norm_ar
        existing.search_text = srch_text
        existing.narrator_text = dto.narrator_text
        existing.grade = dto.grade
        existing.content_hash = c_hash
        existing.source_url = dto.source_url
        db.commit()
        db.refresh(existing)
        return existing

    entity = HadithEntity(
        external_id=dto.external_id,
        hadith_number=dto.hadith_number,
        arabic_text=dto.arabic_text,
        normalized_text=norm_ar,
        search_text=srch_text,
        narrator_text=dto.narrator_text,
        grade=dto.grade or "Sahih",
        content_hash=c_hash,
        source_url=dto.source_url,
        metadata_json=dto.metadata_json or {}
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def search_local_hadiths(db: Session, query: str, limit: int = 10) -> List[HadithEntity]:
    """Pencarian Hadis Lokal Terindeks (Local Research Index Search)."""
    norm_q = normalize_arabic_text(query)
    
    entities = db.query(HadithEntity).filter(
        or_(
            HadithEntity.arabic_text.contains(query),
            HadithEntity.normalized_text.contains(norm_q),
            HadithEntity.search_text.contains(query),
            HadithEntity.external_id.contains(query)
        )
    ).limit(limit).all()

    if not entities:
        entities = db.query(HadithEntity).limit(limit).all()

    return entities
