import uuid
from sqlalchemy.orm import Session
from app.models.publication import PublicationEntity, PublicationVersionEntity

def create_publication(db: Session, project_id: str, title: str, slug: str, content_type: str, language: str = 'id'):
    pub = PublicationEntity(
        project_id=project_id,
        title=title,
        slug=slug,
        content_type=content_type,
        language=language,
        status="DRAFT"
    )
    db.add(pub)
    db.commit()
    db.refresh(pub)
    return pub

def get_publication_by_id(db: Session, pub_id: str):
    return db.query(PublicationEntity).filter(PublicationEntity.id == pub_id).first()

def get_publication_by_slug(db: Session, slug: str):
    return db.query(PublicationEntity).filter(PublicationEntity.slug == slug).first()

def create_publication_version(db: Session, pub_id: str, content: str = "", change_summary: str = "Initial draft"):
    # Get max version
    last_ver = db.query(PublicationVersionEntity).filter(PublicationVersionEntity.publication_id == pub_id).order_by(PublicationVersionEntity.version_number.desc()).first()
    ver_num = (last_ver.version_number + 1) if last_ver else 1
    
    import hashlib
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest() if content else ""
    
    ver = PublicationVersionEntity(
        publication_id=pub_id,
        version_number=ver_num,
        content=content,
        content_hash=content_hash,
        change_summary=change_summary
    )
    db.add(ver)
    db.commit()
    db.refresh(ver)
    return ver
