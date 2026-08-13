from app.models.alignment import HadithSharhAlignmentEntity, AlignmentEvidenceEntity
from sqlalchemy.orm import Session
import random

class AlignmentEngine:
    """
    Mock Candidate Generator and Feature Scorer for the alignment engine.
    In production, this would interface with a Vector DB and a full-text search engine (like BM25/Elasticsearch).
    """
    def __init__(self, db: Session):
        self.db = db

    def generate_candidates(self, hadith_id: str, normalized_matn: str, kitab: str, bab: str):
        # Mocking passage candidates returned from "BM25" and "Vector Search"
        mock_passages = [
            {"passage_id": f"passage_mock_1", "exact_matn": 0.9, "semantic": 0.85, "structural": 1.0},
            {"passage_id": f"passage_mock_2", "exact_matn": 0.0, "semantic": 0.92, "structural": 0.5},
        ]
        
        candidates = []
        for p in mock_passages:
            # Simple linear combination for feature score
            score = (p["exact_matn"] * 0.4) + (p["semantic"] * 0.4) + (p["structural"] * 0.2)
            
            # Confidence Band
            if score >= 0.90:
                band = "AUTO_ACCEPT_CANDIDATE"
            elif score >= 0.75:
                band = "HIGH_CONFIDENCE"
            elif score >= 0.50:
                band = "REVIEW"
            else:
                band = "LOW_CONFIDENCE"
                
            alignment = HadithSharhAlignmentEntity(
                hadith_id=hadith_id,
                passage_id=p["passage_id"],
                alignment_type="PRIMARY_SHARH" if score > 0.8 else "RELATED_TOPIC",
                score=score,
                confidence_band=band,
                status="REVIEW_REQUIRED" if band in ["REVIEW", "HIGH_CONFIDENCE"] else "CANDIDATE",
                matched_features_json=p,
                explanation_json={"reasons": ["High semantic overlap", "Matched exact phrasing" if p["exact_matn"] > 0 else ""]}
            )
            self.db.add(alignment)
            self.db.flush()
            
            # Add Evidence
            evidence = AlignmentEvidenceEntity(
                alignment_id=alignment.id,
                evidence_type="MOCK_SEMANTIC_MATCH",
                source_text="إنما الأعمال بالنيات",
                matched_text="قال الحافظ إنما الأعمال بالنيات",
                score=score
            )
            self.db.add(evidence)
            
            candidates.append(alignment)
            
        self.db.commit()
        return candidates
