from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.corpus_engine import HadithCandidate, CandidateMatchScore, GoldenCorpusItem
from app.models.sharh import HadithSharhLink
from app.models.hadith import Hadith
from app.services.corpus_engine.text_quality import evaluate_text_quality, generate_triple_text_representations
from app.services.corpus_engine.section_detector import detect_sections_and_hierarchy
from app.services.corpus_engine.hadith_detector import extract_hadith_candidates
from app.services.corpus_engine.hybrid_matcher import match_candidate_with_hadiths
from app.services.corpus_engine.quality_reporter import generate_volume_quality_report, run_golden_corpus_test

router = APIRouter(prefix="/api/v1/corpus-engine", tags=["corpus-engine"])


class RejectionRequest(BaseModel):
    reason: str  # WRONG_HADITH, WRONG_MATN, WRONG_NARRATOR, FALSE_DETECTION, OCR_ERROR, DUPLICATE
    note: Optional[str] = None


@router.post("/process-document/{document_id}")
def process_corpus_document(document_id: str, volume: int = 1, db: Session = Depends(get_db)):
    """
    Menjalankan alur lengkap Corpus Processing Engine:
    Quality Evaluation ➔ Triple Text Representations ➔ Section Tree ➔ Hadith Candidates ➔ Hybrid Match Scoring
    """
    sections = detect_sections_and_hierarchy(db, volume=volume)
    candidates = extract_hadith_candidates(db, volume=volume)

    matched_scores = []
    for cand in candidates:
        score = match_candidate_with_hadiths(db, cand)
        matched_scores.append(score)

    return {
        "status": "success",
        "message": "Corpus Processing Engine berhasil mengeksekusi dokumen.",
        "document_id": document_id,
        "volume": volume,
        "sections_detected": len(sections),
        "candidates_extracted": len(candidates),
        "scores_generated": len(matched_scores)
    }


@router.get("/candidates")
def list_candidates(
    status: Optional[str] = Query(None),
    volume: int = Query(1),
    db: Session = Depends(get_db)
):
    """Mengambil daftar seluruh kandidat hadis terdeteksi beserta rincian komponen skor."""
    query = db.query(HadithCandidate)
    if status:
        query = query.filter(HadithCandidate.status == status)

    candidates = query.all()
    res = []

    for cand in candidates:
        score = db.query(CandidateMatchScore).filter(CandidateMatchScore.candidate_id == cand.id).first()
        res.append({
            "id": cand.id,
            "section_id": cand.section_id,
            "reference_text": cand.reference_text,
            "reference_number": cand.reference_number,
            "matn_text": cand.matn_text,
            "narrator": cand.narrator,
            "status": cand.status,
            "rejection_reason": cand.rejection_reason,
            "reviewer_note": cand.reviewer_note,
            "score_breakdown": {
                "reference_score": score.reference_score if score else 0.0,
                "lexical_score": score.lexical_score if score else 0.0,
                "semantic_score": score.semantic_score if score else 0.0,
                "narrator_score": score.narrator_score if score else 0.0,
                "chapter_score": score.chapter_score if score else 0.0,
                "final_score": score.final_score if score else cand.detector_confidence
            } if score else None
        })

    return res


@router.post("/candidates/{candidate_id}/verify")
def verify_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """
    Verifikasi Manual Kandidat Hadis ➔ Memperbarui status ke VERIFIED dan membuat HadithSharhLink terverifikasi.
    """
    cand = db.query(HadithCandidate).filter(HadithCandidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Kandidat tidak ditemukan")

    cand.status = "VERIFIED"
    
    # Create or update verified HadithSharhLink
    if cand.reference_number and cand.section_id:
        hadith = db.query(Hadith).filter(Hadith.external_number == cand.reference_number).first()
        if hadith:
            import uuid
            h_uuid = uuid.UUID(str(hadith.id)) if isinstance(hadith.id, str) else hadith.id
            s_uuid = uuid.UUID(str(cand.section_id)) if isinstance(cand.section_id, str) else cand.section_id

            link = db.query(HadithSharhLink).filter(
                HadithSharhLink.hadith_id == h_uuid,
                HadithSharhLink.sharh_section_id == s_uuid
            ).first()
            if not link:
                link = HadithSharhLink(
                    hadith_id=h_uuid,
                    sharh_section_id=s_uuid,
                    match_method="human_verified_corpus_engine",
                    confidence=1.00,
                    review_status="verified",
                    verified=True,
                    evidence=f"Terverifikasi manual oleh pakar dari Corpus Engine (Hadis #{cand.reference_number})"
                )
                db.add(link)
            else:
                link.review_status = "verified"
                link.verified = True

    db.commit()
    return {"message": "Kandidat berhasil diverifikasi manusia (VERIFIED).", "candidate_id": candidate_id, "status": "VERIFIED"}


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(candidate_id: str, req: RejectionRequest, db: Session = Depends(get_db)):
    """
    Penolakan Manual Kandidat Hadis dengan Alasan Wajib (Mandatory Rejection Reason).
    """
    cand = db.query(HadithCandidate).filter(HadithCandidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Kandidat tidak ditemukan")

    cand.status = "REJECTED"
    cand.rejection_reason = req.reason
    cand.reviewer_note = req.note

    db.commit()
    return {
        "message": "Kandidat ditolak dengan catatan alasan penolakan.",
        "candidate_id": candidate_id,
        "status": "REJECTED",
        "reason": req.reason,
        "note": req.note
    }


@router.get("/quality-report/{volume}")
def get_quality_report(volume: int, db: Session = Depends(get_db)):
    """Mengambil Laporan Kualitas Volume (Volume Quality Report)."""
    return generate_volume_quality_report(db, volume=volume)


@router.post("/golden-corpus/test")
def run_golden_test(db: Session = Depends(get_db)):
    """Menjalankan pengujian regresi otomatis terhadap acuan Golden Corpus."""
    return run_golden_corpus_test(db)
