import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chunk import DocumentChunk, RetrievalLog
from app.services.hybrid_search import hybrid_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["Tahap 8 Hybrid Search Engine"])


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Teks pertanyaan atau kata kunci (Arab / Indonesia / English)")
    mode: str = Field(default="research", description="Mode retrieval: 'research' (hanya verified), 'study' (verified + candidates), 'general'")
    volume: int | None = Field(default=None, description="Filter nomor jilid Fathul Bari opsional")
    limit: int = Field(default=10, ge=1, le=50, description="Batas jumlah hasil")
    verified_only: bool = Field(default=False, description="Paksa hanya menampilkan bukti terverifikasi")


@router.post("/hybrid")
def search_hybrid(
    req: HybridSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Eksekusi Hybrid Search: BM25 Lexical + Vector Semantic + Reciprocal Rank Fusion + Reranker.
    Mendukung pencarian lintas-bahasa Indonesia <-> Arab dengan kebijakan Verified-First.
    """
    return hybrid_search(
        db=db,
        query=req.query,
        retrieval_mode=req.mode,
        volume=req.volume,
        limit=req.limit,
        verified_only=req.verified_only,
    )


@router.get("/stats")
def get_search_engine_stats(db: Session = Depends(get_db)):
    """Mengambil statistik korpus chunk terindeks dan metrik pencarian."""
    total_chunks = db.scalar(select(func.count(DocumentChunk.id))) or 0
    verified_chunks = db.scalar(select(func.count(DocumentChunk.id)).where(DocumentChunk.verified == True)) or 0
    
    # Distribusi bahasa
    ar_chunks = db.scalar(select(func.count(DocumentChunk.id)).where(DocumentChunk.language == "ar")) or 0
    id_chunks = db.scalar(select(func.count(DocumentChunk.id)).where(DocumentChunk.language == "id")) or 0

    # Tipe chunk
    hadith_matan_chunks = db.scalar(select(func.count(DocumentChunk.id)).where(DocumentChunk.chunk_type == "hadith_matan")) or 0
    sharh_chunks = db.scalar(select(func.count(DocumentChunk.id)).where(DocumentChunk.chunk_type == "sharh_section")) or 0
    trans_chunks = db.scalar(select(func.count(DocumentChunk.id)).where(DocumentChunk.chunk_type == "translation")) or 0

    # Metrik latency dari log
    total_logs = db.scalar(select(func.count(RetrievalLog.id))) or 0
    avg_latency = db.scalar(select(func.avg(RetrievalLog.latency_ms))) or 0.0

    return {
        "total_chunks_indexed": total_chunks,
        "verified_chunks": verified_chunks,
        "verified_percentage": round((verified_chunks / total_chunks * 100.0), 1) if total_chunks > 0 else 0.0,
        "language_distribution": {
            "arabic": ar_chunks,
            "indonesian": id_chunks,
            "other": total_chunks - (ar_chunks + id_chunks),
        },
        "chunk_types": {
            "hadith_matan": hadith_matan_chunks,
            "sharh_section": sharh_chunks,
            "translation": trans_chunks,
        },
        "total_queries_logged": total_logs,
        "average_retrieval_latency_ms": round(avg_latency, 2),
    }


@router.get("/logs")
def get_recent_retrieval_logs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Mengambil riwayat log retrieval untuk audit performa mesin pencarian."""
    logs = list(
        db.scalars(
            select(RetrievalLog).order_by(desc(RetrievalLog.created_at)).limit(limit)
        )
    )

    items = []
    for l in logs:
        items.append({
            "id": str(l.id),
            "query": l.query,
            "query_language": l.query_language,
            "retrieval_mode": l.retrieval_mode,
            "retrieved_chunks_count": l.retrieved_chunks_count,
            "latency_ms": l.latency_ms,
            "created_at": l.created_at.isoformat(),
        })

    return {
        "total": len(items),
        "limit": limit,
        "items": items,
    }


@router.post("/evaluate")
def run_evaluation_benchmark(db: Session = Depends(get_db)):
    """Menjalankan pengujian evaluasi otomatis terhadap Golden Dataset (Recall@k, MRR, NDCG)."""
    from scripts.evaluate_search import evaluate
    results = evaluate()
    return {
        "status": "success",
        "benchmark_results": results,
    }
