import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.graph_builder import build_knowledge_graph
from app.services.graph_rag import expand_query_via_knowledge_graph
from app.services.graph_service import (
    find_shortest_path,
    get_graph_stats,
    get_node_neighbors,
    get_subgraph_for_hadith,
    get_subgraph_for_sharh,
    search_graph_nodes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["Tahap 9 Knowledge Graph & GraphRAG"])


class GraphRAGRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Teks pertanyaan penelitian")
    mode: str = Field(default="research", description="'research' (verified only) atau 'study'")
    limit: int = Field(default=5, ge=1, le=20, description="Batas bibit pencarian awal")


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Mengambil rekapitulasi jumlah node, edge, dan rasio verified pada Knowledge Graph."""
    return get_graph_stats(db)


@router.get("/nodes")
def search_nodes(
    q: str = Query(default="", description="Kata kunci pencarian label simpul"),
    node_type: str | None = Query(default=None, description="Filter tipe simpul: hadith, sharh_section, book, topic, person, source_page"),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Mencari dan mendaftar simpul graf berdasarkan teks dan tipe."""
    nodes = search_graph_nodes(db=db, query=q, node_type=node_type, limit=limit)
    return {
        "total": len(nodes),
        "query": q,
        "node_type": node_type,
        "nodes": nodes,
    }


@router.get("/hadith/{hadith_number}")
def get_hadith_graph(
    hadith_number: int,
    verified_only: bool = Query(default=False, description="Hanya tampilkan relasi terverifikasi"),
    db: Session = Depends(get_db),
):
    """Mengambil subgraf relasi hadis Shahih Bukhari tertentu (Syarah, Kitab, Topik, Halaman Naskah)."""
    subgraph = get_subgraph_for_hadith(db=db, hadith_number=hadith_number, verified_only=verified_only)
    if not subgraph.get("root_node_id"):
        raise HTTPException(status_code=404, detail=f"Hadis #{hadith_number} tidak ditemukan di Knowledge Graph.")
    return subgraph


@router.get("/sharh/{sharh_id}")
def get_sharh_graph(
    sharh_id: str,
    verified_only: bool = Query(default=False, description="Hanya tampilkan relasi terverifikasi"),
    db: Session = Depends(get_db),
):
    """Mengambil subgraf untuk seksi Fathul Bari tertentu beserta hadis dan halaman fisiknya."""
    subgraph = get_subgraph_for_sharh(db=db, sharh_id=sharh_id, verified_only=verified_only)
    if not subgraph.get("root_node_id"):
        raise HTTPException(status_code=404, detail="Seksi Syarah tidak ditemukan di Knowledge Graph.")
    return subgraph


@router.get("/node/{node_id}/neighbors")
def get_neighbors(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=3, description="Kedalaman hop traversal (1-3)"),
    verified_only: bool = Query(default=False, description="Hanya ikuti relasi terverifikasi"),
    db: Session = Depends(get_db),
):
    """Melakukan traversal tetangga $k$-hop dari sebuah simpul."""
    result = get_node_neighbors(db=db, node_id=node_id, depth=depth, verified_only=verified_only)
    if not result.get("root_node_id"):
        raise HTTPException(status_code=404, detail="Simpul tidak ditemukan di Knowledge Graph.")
    return result


@router.get("/path")
def get_path_between_nodes(
    source_id: str = Query(..., description="ID simpul asal"),
    target_id: str = Query(..., description="ID simpul tujuan"),
    verified_only: bool = Query(default=False, description="Hanya lewati relasi terverifikasi"),
    db: Session = Depends(get_db),
):
    """Mencari jalur relasi multi-hop terpendek antara dua simpul menggunakan BFS."""
    return find_shortest_path(db=db, source_id=source_id, target_id=target_id, verified_only=verified_only)


@router.post("/build")
def trigger_build_graph(db: Session = Depends(get_db)):
    """Memicu rekonstruksi dan sinkronisasi seluruh Knowledge Graph dari basis data."""
    res = build_knowledge_graph(db)
    return {
        "status": "success",
        "message": "Knowledge Graph berhasil dibangun ulang.",
        "details": res,
    }


@router.post("/rag-expand")
def expand_graph_rag(
    req: GraphRAGRequest,
    db: Session = Depends(get_db),
):
    """
    Eksekusi GraphRAG:
    Menggabungkan Hybrid Search dengan Graph Expansion multi-hop untuk bukti riset komprehensif.
    """
    return expand_query_via_knowledge_graph(
        db=db,
        query=req.query,
        retrieval_mode=req.mode,
        limit=req.limit,
    )
