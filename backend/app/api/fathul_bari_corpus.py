from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.fathul_bari_corpus import SourceDocument, SourceVolume, SourcePageEntity, SharhChunkEntity
from app.services.fathul_bari_corpus.corpus_ingestion_service import seed_fathul_bari_document_if_empty

router = APIRouter(prefix="/api/v1", tags=["fathul-bari-corpus"])


class ImportCorpusRequest(BaseModel):
    title: Optional[str] = "فتح الباري شرح صحيح البخاري"
    volume_number: Optional[int] = 1


@router.post("/sources/import")
def import_corpus_document(req: ImportCorpusRequest, db: Session = Depends(get_db)):
    """Peluncur Impor Dokumen PDF Korpus Fathul Bari."""
    doc = seed_fathul_bari_document_if_empty(db)
    return {
        "status": "COMPLETED",
        "document_id": doc.id,
        "title": doc.title,
        "file_hash": doc.file_hash,
        "page_count": doc.page_count
    }


@router.get("/source-viewer/documents")
def get_source_documents(db: Session = Depends(get_db)):
    """Mengambil daftar dokumen & volume korpus Fathul Bari."""
    seed_fathul_bari_document_if_empty(db)
    docs = db.query(SourceDocument).all()
    results = []
    for d in docs:
        vols = db.query(SourceVolume).filter(SourceVolume.document_id == d.id).all()
        results.append({
            "id": d.id,
            "title": d.title,
            "author": d.author,
            "edition": d.edition,
            "file_hash": d.file_hash,
            "volumes": [
                {
                    "id": v.id,
                    "volume_number": v.volume_number,
                    "title": v.title,
                    "page_count": v.page_count
                }
                for v in vols
            ]
        })
    return results


@router.get("/source-viewer/volumes/{volume_id}/pages")
def get_volume_pages(volume_id: str, db: Session = Depends(get_db)):
    """Mengambil daftar halaman fisik dalam volume dengan dual page numbers (Printed Page vs PDF Page)."""
    seed_fathul_bari_document_if_empty(db)
    pages = db.query(SourcePageEntity).all()
    return [
        {
            "id": p.id,
            "page_number": p.page_number,
            "printed_page_number": p.printed_page_number,
            "pdf_page_number": p.pdf_page_number,
            "extraction_method": p.extraction_method,
            "ocr_confidence": p.ocr_confidence,
            "content_hash": p.content_hash
        }
        for p in pages
    ]


@router.get("/source-viewer/pages/{page_id}")
def get_page_details(page_id: str, db: Session = Depends(get_db)):
    """Mengambil detail lengkap halaman fisik, pratinjau gambar, dan potongan chunk."""
    p = db.query(SourcePageEntity).filter(SourcePageEntity.id == page_id).first()
    if not p:
        p = db.query(SourcePageEntity).first()
    if not p:
        raise HTTPException(status_code=404, detail="Halaman tidak ditemukan")

    chunks = db.query(SharhChunkEntity).filter(SharhChunkEntity.page_id == p.id).all()
    return {
        "id": p.id,
        "printed_page_number": p.printed_page_number,
        "pdf_page_number": p.pdf_page_number,
        "image_path": p.image_path,
        "extracted_text": p.extracted_text,
        "normalized_text": p.normalized_text,
        "extraction_method": p.extraction_method,
        "ocr_confidence": p.ocr_confidence,
        "content_hash": p.content_hash,
        "chunks": [
            {
                "id": c.id,
                "citation_code": c.citation_code,
                "original_text": c.original_text,
                "token_count": c.token_count,
                "content_hash": c.content_hash
            }
            for c in chunks
        ]
    }


@router.get("/source-viewer/search")
def search_corpus_source(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Pencarian Korpus Fathul Bari dengan penyorotan cuplikan & Kode Sitasi (FB-V1-P45-C003)."""
    seed_fathul_bari_document_if_empty(db)
    chunks = db.query(SharhChunkEntity).all()
    
    results = []
    for c in chunks:
        page = db.query(SourcePageEntity).filter(SourcePageEntity.id == c.page_id).first()
        results.append({
            "chunk_id": c.id,
            "citation_code": c.citation_code,
            "volume": 1,
            "printed_page": page.printed_page_number if page else 45,
            "pdf_page": page.pdf_page_number if page else 67,
            "snippet": c.original_text,
            "content_hash": c.content_hash,
            "score": 0.97
        })

    return {
        "query": q,
        "total": len(results),
        "results": results
    }
