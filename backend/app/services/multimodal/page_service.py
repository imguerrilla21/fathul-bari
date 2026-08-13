from sqlalchemy.orm import Session
from app.models.multimodal import SourcePageEntity, PageRegionEntity, OCRBlockEntity

def get_page(db: Session, page_id: str):
    return db.query(SourcePageEntity).filter(SourcePageEntity.id == page_id).first()

def get_page_regions(db: Session, page_id: str):
    return db.query(PageRegionEntity).filter(PageRegionEntity.page_id == page_id).order_by(PageRegionEntity.reading_order).all()

def get_region_ocr(db: Session, region_id: str):
    return db.query(OCRBlockEntity).filter(OCRBlockEntity.region_id == region_id).first()
