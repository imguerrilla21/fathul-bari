from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.syarah_reasoning import ResearchRun, EvidenceUnit, EvidenceClaim, ClaimCitation, SharhArgumentNode
from app.services.assistant.research_agent import execute_research_assistant_run
from app.services.assistant.syarah_reasoning_engine import extract_argument_nodes

router = APIRouter(prefix="/api/v1/assistant", tags=["syarah-assistant"])


class AssistantQueryRequest(BaseModel):
    question: str
    mode: Optional[str] = "RESEARCH"  # RINGKAS, DEEP, RESEARCH
    source_scope: Optional[List[str]] = ["FATH_AL_BARI"]


@router.post("/query")
def run_assistant_query(req: AssistantQueryRequest, db: Session = Depends(get_db)):
    """
    Eksekusi Asisten Syarah AI dalam 3 Mode (RINGKAS, DEEP, RESEARCH):
    Query Planner ➔ Evidence Matrix Builder ➔ Scholar Attribution ➔ Citation Guard Firewall ➔ Research Trace.
    """
    if not req.question:
        raise HTTPException(status_code=400, detail="Pertanyaan tidak boleh kosong")

    res = execute_research_assistant_run(
        db=db,
        query=req.question,
        mode=req.mode or "RESEARCH",
        source_scope=req.source_scope or ["FATH_AL_BARI"]
    )
    return res


@router.get("/runs/{run_id}")
def get_research_run_details(run_id: str, db: Session = Depends(get_db)):
    """Mengambil detail lengkap jejak riset (Research Trace), Matriks Bukti, dan Audit Sitasi."""
    run = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run ID tidak ditemukan")

    evidence_units = db.query(EvidenceUnit).filter(EvidenceUnit.run_id == run.id).all()
    claims = db.query(EvidenceClaim).filter(EvidenceClaim.run_id == run.id).all()

    return {
        "run_id": run.id,
        "query": run.query,
        "mode": run.mode,
        "overall_confidence": run.overall_confidence,
        "status": run.status,
        "evidence_matrix": [
            {
                "code": ev.evidence_code,
                "source": ev.source,
                "volume": ev.volume,
                "page": ev.page,
                "type": ev.evidence_type,
                "snippet": ev.text
            }
            for ev in evidence_units
        ],
        "claims_audit": [
            {
                "claim_text": c.claim_text,
                "support_score": c.support_score,
                "is_supported": c.is_supported
            }
            for c in claims
        ],
        "created_at": run.created_at.isoformat() if run.created_at else None
    }


@router.get("/argument-graph/{section_id}")
def get_argument_graph(section_id: str, db: Session = Depends(get_db)):
    """Mengambil node struktur argumen syarah dan atribusi ulama."""
    nodes = extract_argument_nodes(db, section_id=section_id)
    return [
        {
            "id": n.id,
            "argument_type": n.argument_type,
            "scholar_name": n.scholar_name,
            "attribution_type": n.attribution_type,
            "quoted_scholar": n.quoted_scholar,
            "text": n.text,
            "confidence": n.confidence
        }
        for n in nodes
    ]
