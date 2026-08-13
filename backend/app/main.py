from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.ai import router as ai_router
from app.api.graph import router as graph_router
from app.api.hadith import router as hadith_router
from app.api.hybrid_search import router as hybrid_search_router
from app.api.matching import router as matching_router
from app.api.review import router as review_router
from app.api.sharh import router as sharh_router
from app.api.source import router as source_router
from app.api.workspace import router as workspace_router
from app.api.analytics import router as analytics_router
from app.api.evaluation import router as evaluation_router
from app.api.auth import router as auth_router
from app.api.production import router as production_router
from app.api.ingestion import router as ingestion_router
from app.api.corpus_engine import router as corpus_engine_router
from app.api.nlp_matching import router as nlp_matching_router
from app.api.syarah_reasoning import router as syarah_reasoning_router
from app.api.production_deployment import router as production_deployment_router
from app.api.hadith_data_layer import router as hadith_data_layer_router
from app.api.hadith_fathul_bari_matching import router as hadith_fathul_bari_matching_router
from app.api import workspace_engine
from app.api import observability_engine
from app.api import publication_engine
from app.api.fathul_bari_corpus import router as fathul_bari_corpus_router
from app.api.rag_evidence_engine import router as rag_evidence_engine_router
from app.api.research_workspace import router as research_workspace_v2_router
from app.api.scholarly_citation import router as scholarly_citation_v2_router
from app.api.scholarly_publication import router as scholarly_publication_v2_router
from app.api.nlp import router as nlp_router
from app.api.intelligence import router as intelligence_router
from app.api.research import router as research_router
from app.api.scholarly_review import router as scholarly_review_router
from app.api.corpus import router as corpus_router
from app.api.alignment import router as alignment_router
from app.api.multimodal_source import router as multimodal_source_router
from app.api.attribution_engine import router as attribution_router
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.production_service import check_readiness, seed_default_users
import app.models  # Ensure all models are registered

# Create database tables for newly added models
Base.metadata.create_all(bind=engine)

# Seed default admin & reviewer accounts
try:
    with SessionLocal() as db_session:
        seed_default_users(db_session)
except Exception:
    pass

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend riset dan penelitian hadis Shahih Bukhari & Syarah Fathul Bari.",
)

# CORS middleware for modern browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(intelligence_router)
app.include_router(hadith_router)
app.include_router(admin_router)
app.include_router(sharh_router)
app.include_router(matching_router)
app.include_router(review_router)
app.include_router(ai_router)
app.include_router(source_router)
app.include_router(hybrid_search_router)
app.include_router(graph_router)
app.include_router(workspace_router)
app.include_router(analytics_router)
app.include_router(evaluation_router)
app.include_router(auth_router)
app.include_router(production_router)
app.include_router(ingestion_router)
app.include_router(corpus_engine_router)
app.include_router(nlp_matching_router)
app.include_router(syarah_reasoning_router)
app.include_router(production_deployment_router)
app.include_router(hadith_data_layer_router)
app.include_router(hadith_fathul_bari_matching_router)
app.include_router(workspace_engine.router)
app.include_router(observability_engine.router, prefix="/api/v1", tags=["observability"])
app.include_router(publication_engine.router, prefix="/api/v1", tags=["publication"])
app.include_router(fathul_bari_corpus_router)
app.include_router(rag_evidence_engine_router)
app.include_router(research_workspace_v2_router)
app.include_router(scholarly_citation_v2_router)
app.include_router(scholarly_publication_v2_router)
app.include_router(nlp_router)
app.include_router(research_router)
app.include_router(scholarly_review_router)
app.include_router(corpus_router)
app.include_router(alignment_router)
app.include_router(multimodal_source_router)
app.include_router(attribution_router)
app.include_router(workspace_router)

@app.get("/ready")
def readiness():
    with SessionLocal() as db_session:
        return check_readiness(db_session)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "ui": "/ui/",
            "review_dashboard": "/review/",
            "source_viewer": "/source-viewer/",
            "source_audit_recent": "/api/v1/source/audit/recent",
            "ai_suggestions": "/api/v1/ai/suggestions",
            "ai_ask": "/api/v1/ai/ask",
            "ai_status": "/api/v1/ai/status",
            "review_queue": "/api/v1/review/queue?status=pending",
            "review_stats": "/api/v1/review/stats",
            "hadith_example": "/api/v1/hadith/shahih_bukhari/1",
            "search_example": "/api/v1/hadith/search?q=niat",
            "data_quality": "/api/v1/admin/data-quality",
            "sharh_example": "/api/v1/sharh/hadith/shahih_bukhari/1",
        },
    }



@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/ui", include_in_schema=False)
def ui_redirect():
    return RedirectResponse(url="/ui/")


@app.get("/ui/", include_in_schema=False)
def ui():
    path = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(path)


@app.get("/review", include_in_schema=False)
def review_redirect():
    return RedirectResponse(url="/review/")


@app.get("/review/", include_in_schema=False)
def review_dashboard():
    path = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(path)


@app.get("/source-viewer", include_in_schema=False)
def source_viewer_redirect():
    return RedirectResponse(url="/source-viewer/")


@app.get("/source-viewer/", include_in_schema=False)
def source_viewer():
    path = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(path)



