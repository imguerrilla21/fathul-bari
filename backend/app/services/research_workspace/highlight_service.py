from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.research_workspace_v2 import SourceHighlightEntity
from app.services.hadith_data_layer.arabic_normalizer import calculate_content_hash


def create_text_highlight(
    db: Session,
    workspace_id: str,
    page_id: str,
    selected_text: str,
    start_offset: int = 0,
    end_offset: int = 40,
    color: str = "yellow"
) -> SourceHighlightEntity:
    """Pembuat Penandaan Highlight Teks Sumber dengan Hash SHA-256."""
    c_hash = calculate_content_hash(selected_text)
    hl = SourceHighlightEntity(
        workspace_id=workspace_id,
        page_id=page_id,
        start_offset=start_offset,
        end_offset=end_offset,
        selected_text=selected_text,
        color=color,
        content_hash=c_hash
    )
    db.add(hl)
    db.commit()
    db.refresh(hl)
    return hl
