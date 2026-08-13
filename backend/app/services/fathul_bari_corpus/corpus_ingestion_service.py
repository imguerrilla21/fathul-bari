import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.fathul_bari_corpus import (
    SourceDocument, SourceVolume, SourcePageEntity, SourceSectionEntity, SharhChunkEntity
)
from app.services.fathul_bari_corpus.pdf_reader import PDFReader
from app.services.fathul_bari_corpus.section_aware_chunker import create_section_aware_chunks
from app.services.hadith_data_layer.arabic_normalizer import calculate_content_hash

logger = logging.getLogger("corpus_ingestion_service")


def seed_fathul_bari_document_if_empty(db: Session) -> SourceDocument:
    """Membuat registri dokumen Fathul Bari Jilid 1 jika belum ada."""
    doc = db.query(SourceDocument).first()
    if not doc:
        doc = SourceDocument(
            title="فتح الباري شرح صحيح البخاري",
            author="أحمد بن علي بن حجر العسقلاني",
            language="ar",
            edition="Dar al-Ma'rifah Edition",
            publisher="Dar al-Ma'rifah",
            publication_year=1379,
            source_type="PDF",
            file_name="fathul_bari_vol01.pdf",
            file_hash="8e72a4b89f1d2c3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e",
            page_count=520
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        vol = SourceVolume(
            document_id=doc.id,
            volume_number=1,
            title="الجزء الأول: كتاب بدء الوحي وكتاب الإيمان",
            page_count=520
        )
        db.add(vol)
        db.commit()
        db.refresh(vol)

        # Seed initial sample pages (Printed page 45, PDF page 67)
        reader = PDFReader()
        for pdf_p in range(65, 70):
            printed_p = pdf_p - 22
            page_txt = reader.extract_page_text(pdf_p)
            p_hash = calculate_content_hash(page_txt)

            page_ent = SourcePageEntity(
                volume_id=vol.id,
                page_number=printed_p,
                pdf_page_number=pdf_p,
                printed_page_number=printed_p,
                image_path=reader.render_page_image_url(pdf_p),
                extracted_text=page_txt,
                normalized_text=page_txt,
                extraction_method="TEXT_LAYER",
                ocr_confidence=0.98,
                content_hash=p_hash
            )
            db.add(page_ent)
            db.commit()
            db.refresh(page_ent)

            # Generate Chunks
            chunks = create_section_aware_chunks(
                volume_num=1,
                printed_page_num=printed_p,
                pdf_page_num=pdf_p,
                page_text=page_txt
            )

            for c in chunks:
                chunk_ent = SharhChunkEntity(
                    volume_id=vol.id,
                    page_id=page_ent.id,
                    chunk_index=c["chunk_index"],
                    citation_code=c["citation_code"],
                    original_text=c["original_text"],
                    normalized_text=c["normalized_text"],
                    start_offset=c["start_offset"],
                    end_offset=c["end_offset"],
                    token_count=c["token_count"],
                    content_hash=c["content_hash"]
                )
                db.add(chunk_ent)
            db.commit()

    return doc
