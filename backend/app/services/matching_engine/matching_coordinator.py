import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.hadith_data_layer import HadithEntity
from app.models.hadith_fathul_bari_matching import HadithSharhMatchEntity
from app.services.matching_engine.candidate_generator import generate_match_candidates
from app.services.matching_engine.multi_signal_scorer import calculate_hybrid_match_score, generate_match_explanation

logger = logging.getLogger("matching_coordinator")


def run_batch_matching_job(db: Session, collection_slug: str = "bukhari") -> List[HadithSharhMatchEntity]:
    """
    Eksekusi Batch Job Matching Engine Hadith ↔ Fathul Bari:
    1. Mengambil hadis terindeks
    2. Menghasilkan kandidat pencocokan multi-sinyal
    3. Menghitung skor hibrida 5 komponen & pita kepercayaan (HIGH/MEDIUM/LOW)
    4. Menyimpan entitas HadithSharhMatchEntity dengan matcher_version = "20.1.0"
    """
    hadiths = db.query(HadithEntity).limit(5).all()
    created_matches = []

    for h in hadiths:
        candidates = generate_match_candidates(db, h)
        for cand in candidates:
            sec = cand["sharh_section"]
            
            # Check existing match
            existing = db.query(HadithSharhMatchEntity).filter(
                HadithSharhMatchEntity.hadith_id == h.id,
                HadithSharhMatchEntity.sharh_chunk_id == str(sec.id)
            ).first()

            scores = calculate_hybrid_match_score(
                lexical=cand["lexical_score"],
                semantic=cand["semantic_score"],
                reference=cand["reference_score"],
                context=cand["context_score"]
            )

            explanation = generate_match_explanation(
                hadith_num=h.hadith_number or "1",
                opening_phrase=h.arabic_text[:30],
                scores=scores
            )

            if existing:
                existing.confidence_score = scores["confidence_score"]
                existing.confidence_band = scores["confidence_band"]
                existing.explanation_json = explanation
                db.commit()
                created_matches.append(existing)
            else:
                match_obj = HadithSharhMatchEntity(
                    hadith_id=h.id,
                    sharh_chunk_id=str(sec.id),
                    match_type=cand["match_type"],
                    lexical_score=scores["lexical_score"],
                    semantic_score=scores["semantic_score"],
                    reference_score=scores["reference_score"],
                    context_score=scores["context_score"],
                    confidence_score=scores["confidence_score"],
                    confidence_band=scores["confidence_band"],
                    status="PENDING",
                    matcher_version="20.1.0",
                    explanation_json=explanation
                )
                db.add(match_obj)
                db.commit()
                db.refresh(match_obj)
                created_matches.append(match_obj)

    return created_matches
