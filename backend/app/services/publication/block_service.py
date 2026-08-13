from sqlalchemy.orm import Session
from app.models.publication import PublicationBlockEntity, PublicationEvidenceEntity

def add_block(db: Session, version_id: str, block_type: str, content: str, block_order: int):
    block = PublicationBlockEntity(
        publication_version_id=version_id,
        block_type=block_type,
        content=content,
        block_order=block_order
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block

def link_evidence_to_block(db: Session, block_id: str, evidence_type: str, evidence_id: str, relation: str = "SUPPORTED_BY"):
    link = PublicationEvidenceEntity(
        publication_block_id=block_id,
        evidence_type=evidence_type,
        evidence_id=evidence_id,
        relation=relation
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def get_blocks_for_version(db: Session, version_id: str):
    return db.query(PublicationBlockEntity).filter(PublicationBlockEntity.publication_version_id == version_id).order_by(PublicationBlockEntity.block_order.asc()).all()

def get_evidence_for_block(db: Session, block_id: str):
    return db.query(PublicationEvidenceEntity).filter(PublicationEvidenceEntity.publication_block_id == block_id).all()
