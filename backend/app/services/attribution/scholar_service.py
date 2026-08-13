from sqlalchemy.orm import Session
from app.models.attribution import ScholarEntity, ScholarAliasEntity

def get_scholar(db: Session, scholar_id: str):
    return db.query(ScholarEntity).filter(ScholarEntity.id == scholar_id).first()

def get_scholar_by_alias(db: Session, name_mention: str):
    alias = db.query(ScholarAliasEntity).filter(ScholarAliasEntity.alias.ilike(f"%{name_mention}%")).first()
    if alias:
        return get_scholar(db, alias.scholar_id)
    return None
