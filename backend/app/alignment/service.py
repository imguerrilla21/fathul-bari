from sqlalchemy.orm import Session
from app.models.alignment import HadithIdentityEntity, HadithSharhAlignmentEntity
from app.alignment.normalizer import normalize_arabic, generate_matn_fingerprint
from app.alignment.engine import AlignmentEngine
from datetime import datetime, timezone

class AlignmentService:
    def register_hadith(self, db: Session, external_source: str, external_id: str, collection: str, hadith_number: str, kitab: str, bab: str, arabic_matn: str):
        normalized = normalize_arabic(arabic_matn)
        fingerprint = generate_matn_fingerprint(normalized)
        
        identity = HadithIdentityEntity(
            external_source=external_source,
            external_id=external_id,
            collection=collection,
            hadith_number=hadith_number,
            kitab=kitab,
            bab=bab,
            arabic_matn=arabic_matn,
            normalized_matn=normalized,
            matn_fingerprint=fingerprint
        )
        db.add(identity)
        db.commit()
        db.refresh(identity)
        return identity

    def run_alignment(self, db: Session, hadith_id: str):
        hadith = db.query(HadithIdentityEntity).filter(HadithIdentityEntity.id == hadith_id).first()
        if not hadith:
            raise ValueError("Hadith not found")
            
        engine = AlignmentEngine(db)
        candidates = engine.generate_candidates(
            hadith_id=hadith.id,
            normalized_matn=hadith.normalized_matn,
            kitab=hadith.kitab,
            bab=hadith.bab
        )
        return candidates
        
    def verify_alignment(self, db: Session, alignment_id: str, user_id: str):
        alignment = db.query(HadithSharhAlignmentEntity).filter(HadithSharhAlignmentEntity.id == alignment_id).first()
        if not alignment:
            raise ValueError("Alignment not found")
            
        alignment.status = "HUMAN_VERIFIED"
        alignment.verified_by = user_id
        alignment.verified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alignment)
        return alignment

    def reject_alignment(self, db: Session, alignment_id: str, reason: str, user_id: str):
        alignment = db.query(HadithSharhAlignmentEntity).filter(HadithSharhAlignmentEntity.id == alignment_id).first()
        if not alignment:
            raise ValueError("Alignment not found")
            
        alignment.status = "REJECTED"
        alignment.explanation_json["rejection_reason"] = reason
        db.commit()
        db.refresh(alignment)
        return alignment
