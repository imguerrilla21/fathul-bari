from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.services.nlp.arabic_nlp import (
    normalize_arabic_v2,
    tokenize_and_lemmatize,
    extract_arabic_entities,
    parse_sanad_transmission,
    extract_matn_fingerprint,
    resolve_relative_reference,
)
from app.services.nlp.advanced_matcher import (
    rerank_candidates_with_explanation,
    calculate_nlp_evaluation_metrics,
)

router = APIRouter(tags=["nlp-matching"])


class AnalyzeRequest(BaseModel):
    text: str


@router.post("/api/v1/nlp/analyze")
def analyze_arabic_text(req: AnalyzeRequest):
    """
    Analisis mendalam teks Arab: Normalisasi v2, Token & Lemma, NER Entitas Teks, Sanad Transmission Graph, dan Matn Fingerprint.
    """
    if not req.text:
        raise HTTPException(status_code=400, detail="Teks Arab tidak boleh kosong")

    norm = normalize_arabic_v2(req.text)
    tokens_lemmas = tokenize_and_lemmatize(req.text)
    entities = extract_arabic_entities(req.text)
    sanad_chain = parse_sanad_transmission(req.text)
    fingerprint = extract_matn_fingerprint(req.text)

    return {
        "raw_text": req.text,
        "normalized_text_v2": norm,
        "tokens": tokens_lemmas["raw_tokens"],
        "lemmas": tokens_lemmas["lemmas"],
        "entities": entities,
        "sanad_chain_graph": sanad_chain,
        "matn_fingerprint": fingerprint
    }


@router.post("/api/v1/nlp/hadith-detect")
def detect_hadith_references(req: AnalyzeRequest):
    """
    Deteksi rujukan hadis dan resolver sitasi relatif (e.g. وقد تقدم, كما سيأتي في كتاب البيوع, وفي رواية).
    """
    if not req.text:
        raise HTTPException(status_code=400, detail="Teks tidak boleh kosong")

    rel_ref = resolve_relative_reference(req.text)
    entities = extract_arabic_entities(req.text)

    return {
        "text": req.text,
        "relative_reference": rel_ref,
        "detected_entities": [e for e in entities if e["entity_type"] in {"HADITH_REF", "BOOK_REF", "NARRATOR"}]
    }


@router.post("/api/v1/matching/hadith")
def match_hadith_advanced(candidate_id: str, db: Session = Depends(get_db)):
    """
    Advanced Hybrid Hadith Matcher & Reranker dengan Generator Kartu Penjelasan ("Why This Match?").
    """
    explanation = rerank_candidates_with_explanation(db, candidate_id)
    if "error" in explanation:
        raise HTTPException(status_code=404, detail=explanation["error"])
    return explanation


@router.get("/api/v1/matching/{id}/explanation")
def get_match_explanation(id: str, db: Session = Depends(get_db)):
    """Mengambil kartu penjelasan rasionalitas pencocokan (Explainable Match Rationale)."""
    explanation = rerank_candidates_with_explanation(db, id)
    if "error" in explanation:
        raise HTTPException(status_code=404, detail=explanation["error"])
    return explanation


@router.get("/api/v1/evaluation/matcher")
def get_matcher_evaluation(db: Session = Depends(get_db)):
    """Mengambil metrik evaluasi NLP (Recall@5, MRR, NDCG) dan antrean Active Learning."""
    return calculate_nlp_evaluation_metrics(db)
