"""AI & RAG Assistant API Router for Fathul Bari Research Platform."""

import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.citation_validator import validate_citation_record
from app.services.rag_retriever import retrieve_rag_context
from app.services.rag_synthesizer import synthesize_rag_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["Syarah AI Assistant (RAG)"])


class AIResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Pertanyaan riset atau topik hadis")
    kitab: str = Field(default="shahih_bukhari", description="Slug koleksi hadis (default: shahih_bukhari)")
    hadith_number: int | None = Field(default=None, description="Nomor hadis spesifik jika ada (misal: 1, 2, dst.)")
    mode: str = Field(default="syarah_focus", description="Mode riset: 'syarah_focus', 'fiqh_faedah', 'sanad_matan'")


class ValidateCitationRequest(BaseModel):
    collection_slug: str = Field(default="shahih_bukhari")
    hadith_number: int | None = Field(default=None, ge=1)
    volume: int | None = Field(default=None, ge=1)
    page: int | None = Field(default=None, ge=1)
    sharh_id: str | None = None


@router.get("/status")
def get_ai_status():
    """Mengambil status konfigurasi AI Assistant & RAG Engine."""
    has_gemini = bool(settings.gemini_api_key)
    has_openai = bool(settings.openai_api_key)
    active_engine = "builtin_turats_engine"

    if settings.ai_provider == "gemini" or (settings.ai_provider == "auto" and has_gemini):
        active_engine = f"Google Gemini ({settings.ai_model_name})"
    elif settings.ai_provider == "openai" or (settings.ai_provider == "auto" and has_openai):
        active_engine = f"OpenAI ({settings.ai_model_name})"

    return {
        "status": "ready",
        "configured_provider": settings.ai_provider,
        "active_engine": active_engine,
        "gemini_configured": has_gemini,
        "openai_configured": has_openai,
        "model_name": settings.ai_model_name,
        "features": {
            "anti_hallucination_guard": True,
            "scholarly_turats_synthesis": True,
            "multiformat_citations": True,
            "knowledge_graph_linking": True,
        }
    }


@router.get("/suggestions")
def get_research_suggestions():
    """Mengambil daftar contoh pertanyaan riset preset untuk asisten AI."""
    return {
        "categories": [
            {
                "category": "Pondasi Niat & Ikhlas (Hadis #1)",
                "icon": "✨",
                "questions": [
                    {
                        "title": "Penjelasan Niat menurut Ibnu Hajar",
                        "prompt": "Jelaskan makna hadis 'Innamal a'malu bin-niyyat' (Hadis #1) dan bagaimana Ibnu Hajar mendefinisikan niat dalam Fathul Bari?",
                        "hadith_number": 1,
                        "tag": "Niat & Ikhlas"
                    },
                    {
                        "title": "Alasan Bukhari Mengawali Kitab dengan Hadis Niat",
                        "prompt": "Mengapa Imam Al-Bukhari meletakkan hadis niat di bagian pembuka (*Muqaddimah*) Shahih al-Bukhari?",
                        "hadith_number": 1,
                        "tag": "Metodologi Bukhari"
                    }
                ]
            },
            {
                "category": "Proses Turunnya Wahyu (Hadis #2 & #3)",
                "icon": "⚡",
                "questions": [
                    {
                        "title": "Makna Suara Lonceng dalam Wahyu",
                        "prompt": "Bagaimana penjelasan Fathul Bari mengenai bunyi 'gemerincing lonceng' (*shalsalatul jaras*) saat wahyu turun pada Hadis #2?",
                        "hadith_number": 2,
                        "tag": "Kaifa Ya'tikal Wahyu"
                    },
                    {
                        "title": "Peristiwa Gua Hira & Mimpi yang Benar",
                        "prompt": "Jelaskan tentang mimpi kenabian dan ibadah tahannuts di Gua Hira berdasarkan Hadis #3 dan Syarah Fathul Bari.",
                        "hadith_number": 3,
                        "tag": "Permulaan Wahyu"
                    }
                ]
            },
            {
                "category": "Keutamaan Ilmu & Fikih",
                "icon": "📚",
                "questions": [
                    {
                        "title": "Batasan Ilmu Syar'i Wajib",
                        "prompt": "Apa yang dimaksud dengan ilmu syar'i yang wajib dipelajari menurut penjelasan Ibnu Hajar dalam Bab Keutamaan Ilmu?",
                        "hadith_number": None,
                        "tag": "Kitab al-Ilmi"
                    }
                ]
            }
        ]
    }


@router.post("/ask")
async def ask_ai_assistant(
    request: AIResearchRequest,
    db: Session = Depends(get_db),
):
    """Mengirim pertanyaan riset hadis ke Syarah AI Assistant dengan RAG."""
    try:
        # 1. Retrieval Layer
        retrieval_res = retrieve_rag_context(
            db=db,
            query=request.query,
            kitab=request.kitab,
            hadith_number=request.hadith_number,
        )

        # 2. Synthesis Layer (Multi-Provider with Anti-Hallucination Guard)
        synthesis_res = await synthesize_rag_response(
            query=request.query,
            rag_retrieval_result=retrieval_res,
            mode=request.mode,
        )

        # 3. Knowledge Graph Expansion Layer (Tahap 9 GraphRAG)
        graph_rag_info = {}
        try:
            from app.services.graph_rag import expand_query_via_knowledge_graph
            graph_rag_info = expand_query_via_knowledge_graph(
                db=db,
                query=request.query,
                retrieval_mode="research",
                limit=3,
            )
        except Exception as g_err:
            logger.warning("Gagal memperluas graph rag: %s", g_err)

        return {
            "status": "success",
            "query": request.query,
            "mode": request.mode,
            "provider": synthesis_res.get("provider_used"),
            "answer": synthesis_res.get("answer"),
            "citations": synthesis_res.get("citations", []),
            "retrieved_summary": synthesis_res.get("retrieved_summary", {}),
            "anti_hallucination_audit": synthesis_res.get("anti_hallucination_audit", {}),
            "graph_provenance": {
                "seed_count": graph_rag_info.get("seed_count", 0),
                "expanded_nodes_count": graph_rag_info.get("expanded_nodes_count", 0),
                "evidence_chain": graph_rag_info.get("evidence_chain", []),
            },
        }
    except Exception as exc:
        logger.error("Error pada Syarah AI Assistant: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal memproses pertanyaan riset AI: {str(exc)}")


@router.post("/validate-citation")
def validate_citation(
    request: ValidateCitationRequest,
    db: Session = Depends(get_db),
):
    """Memvalidasi integritas catatan sitasi akademik terhadap basis data lokal."""
    result = validate_citation_record(
        db=db,
        collection_slug=request.collection_slug,
        hadith_number=request.hadith_number,
        volume=request.volume,
        page=request.page,
        sharh_id=request.sharh_id,
    )
    return result
