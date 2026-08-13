from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.multimodal import SourcePageEntity, PageRegionEntity, OCRBlockEntity

def search_multimodal_blocks(db: Session, query: str, page_id: str = None, region_type: str = None):
    # Base query for OCR blocks
    stmt = db.query(OCRBlockEntity, PageRegionEntity, SourcePageEntity)\
             .join(PageRegionEntity, OCRBlockEntity.region_id == PageRegionEntity.id)\
             .join(SourcePageEntity, PageRegionEntity.page_id == SourcePageEntity.id)
    
    # Filter by text matching in raw, normalized, or corrected text
    stmt = stmt.filter(or_(
        OCRBlockEntity.raw_text.ilike(f"%{query}%"),
        OCRBlockEntity.normalized_text.ilike(f"%{query}%"),
        OCRBlockEntity.corrected_text.ilike(f"%{query}%")
    ))

    if page_id:
        stmt = stmt.filter(SourcePageEntity.id == page_id)
    if region_type:
        stmt = stmt.filter(PageRegionEntity.region_type == region_type)

    results = stmt.all()
    
    formatted_results = []
    for block, region, page in results:
        formatted_results.append({
            "block_id": block.id,
            "region_id": region.id,
            "page_id": page.id,
            "text": block.corrected_text or block.raw_text,
            "confidence": block.ocr_confidence,
            "bbox": [region.x1, region.y1, region.x2, region.y2]
        })
    
    return formatted_results
