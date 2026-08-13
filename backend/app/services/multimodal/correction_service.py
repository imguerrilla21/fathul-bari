from sqlalchemy.orm import Session
from app.models.multimodal import OCRBlockEntity, SourceCorrectionEntity

def submit_correction(db: Session, block_id: str, corrected_text: str, reviewer_id: str, reason: str = None, method: str = "HUMAN"):
    block = db.query(OCRBlockEntity).filter(OCRBlockEntity.id == block_id).first()
    if not block:
        raise ValueError(f"OCRBlock with id {block_id} not found.")

    correction = SourceCorrectionEntity(
        block_id=block_id,
        original_text=block.raw_text,
        corrected_text=corrected_text,
        method=method,
        reviewer_id=reviewer_id,
        reason=reason
    )
    
    # Update the block's corrected_text
    block.corrected_text = corrected_text
    
    db.add(correction)
    db.commit()
    db.refresh(correction)
    db.refresh(block)
    
    return correction, block
