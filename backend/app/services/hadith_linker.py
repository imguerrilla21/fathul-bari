import json
import logging
import uuid
from pathlib import Path
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Collection, Hadith, HadithSharhLink, SharhSection
from app.services.arabic_normalizer import compute_matn_similarity, normalize_arabic
from app.services.hadith_reference_detector import detect_hadith_references

logger = logging.getLogger(__name__)


def score_link(
    number_score: float,
    text_score: float,
    context_score: float = 0.0,
) -> float:
    """Formula Tahap 4: final = number_score*0.50 + text_score*0.35 + context_score*0.15"""
    score = (number_score * 0.50) + (text_score * 0.35) + (context_score * 0.15)
    return round(min(1.0, max(0.0, score)), 4)


def determine_review_status(confidence: float) -> str:
    """Threshold Tahap 4:
    - >= 0.90: auto_candidate
    - 0.75–0.89: review
    - 0.50–0.74: weak_match
    - < 0.50: reject
    """
    if confidence >= 0.90:
        return "auto_candidate"
    elif confidence >= 0.75:
        return "review"
    elif confidence >= 0.50:
        return "weak_match"
    else:
        return "reject"


def get_matching_candidates(
    db: Session,
    section: SharhSection,
    collection_slug: str = "shahih_bukhari",
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Menghitung skor kecocokan antara seksi syarah dan hadis-hadis kandidat di database."""
    collection = db.scalar(select(Collection).where(Collection.slug == collection_slug))
    if not collection:
        return []

    raw_text = section.arabic_text or ""
    norm_text = section.normalized_text or normalize_arabic(raw_text)

    # 1. Deteksi referensi dari teks syarah
    references = detect_hadith_references(raw_text, norm_text)
    detected_numbers = [r.hadith_number for r in references if r.hadith_number is not None]
    quotes = [r.matched_text for r in references if r.reference_type in {"quote_parenthesis", "quote_statement"}]

    candidate_hadiths: list[Hadith] = []

    # 2. Ambil hadis berdasarkan nomor eksplisit
    if detected_numbers:
        for num in detected_numbers:
            h = db.scalar(
                select(Hadith).where(
                    Hadith.collection_id == collection.id,
                    Hadith.external_number == num,
                )
            )
            if h and h not in candidate_hadiths:
                candidate_hadiths.append(h)

    # 3. Ambil hadis berdasarkan pencarian kutipan matan
    if quotes:
        for q in quotes:
            pattern = f"%{normalize_arabic(q)[:40]}%"
            matched = list(
                db.scalars(
                    select(Hadith)
                    .where(
                        Hadith.collection_id == collection.id,
                        (Hadith.arabic_text.ilike(pattern)) | (Hadith.translation.ilike(pattern)),
                    )
                    .limit(top_k)
                )
            )
            for m in matched:
                if m not in candidate_hadiths:
                    candidate_hadiths.append(m)

    # 4. Jika kandidat masih sedikit, ambil hadis terdekat berdasarkan nomor halaman / awal kitab
    if len(candidate_hadiths) < top_k:
        fallback_num = section.printed_page or section.pdf_page or section.page or 1
        nearby = list(
            db.scalars(
                select(Hadith)
                .where(
                    Hadith.collection_id == collection.id,
                    Hadith.external_number.between(max(1, fallback_num - 2), fallback_num + 5),
                )
                .limit(top_k - len(candidate_hadiths))
            )
        )
        for nb in nearby:
            if nb not in candidate_hadiths:
                candidate_hadiths.append(nb)

    # 5. Hitung Multi-Signal Score untuk seluruh kandidat
    candidate_scores: list[dict[str, Any]] = []

    for hadith in candidate_hadiths:
        # A. Number score
        number_score = 1.0 if hadith.external_number in detected_numbers else 0.0

        # B. Text score
        best_text_score = compute_matn_similarity(norm_text, hadith.arabic_text or "")
        for q in quotes:
            q_score = compute_matn_similarity(q, hadith.arabic_text or "")
            if q_score > best_text_score:
                best_text_score = q_score

        # C. Context score (0.0 sampai metadata kitab/bab tersedia secara granular)
        context_score = 0.0

        final_score = score_link(number_score, best_text_score, context_score)
        category = determine_review_status(final_score)

        candidate_scores.append({
            "hadith_id": str(hadith.id),
            "hadith_number": hadith.external_number,
            "arabic_excerpt": (hadith.arabic_text or "")[:120] + "...",
            "translation_excerpt": (hadith.translation or "")[:150] + "...",
            "number_score": number_score,
            "text_score": best_text_score,
            "context_score": context_score,
            "final_confidence": final_score,
            "confidence_percent": round(final_score * 100, 2),
            "category": category,
            "evidence": {
                "detected_numbers": detected_numbers,
                "quotes_found": quotes,
                "number_score": number_score,
                "text_score": best_text_score,
                "context_score": context_score,
            },
        })

    # Urutkan berdasarkan final_confidence desc
    candidate_scores.sort(key=lambda x: x["final_confidence"], reverse=True)
    return candidate_scores[:top_k]


def persist_matching_candidates(
    db: Session,
    section: SharhSection,
    candidates: list[dict[str, Any]] | None = None,
    min_confidence: float = 0.50,
) -> list[HadithSharhLink]:
    """Menyimpan kandidat matching yang memenuhi batas min_confidence ke tabel hadith_sharh_links."""
    if candidates is None:
        candidates = get_matching_candidates(db, section)

    persisted: list[HadithSharhLink] = []

    for c in candidates:
        if c["final_confidence"] < min_confidence:
            continue

        raw_hadith_id = c["hadith_id"]
        hadith_uuid = raw_hadith_id if isinstance(raw_hadith_id, uuid.UUID) else uuid.UUID(str(raw_hadith_id))
        section_uuid = section.id if isinstance(section.id, uuid.UUID) else uuid.UUID(str(section.id))

        existing = db.scalar(
            select(HadithSharhLink).where(
                HadithSharhLink.hadith_id == hadith_uuid,
                HadithSharhLink.sharh_section_id == section_uuid,
            )
        )

        review_status = c["category"]
        evidence_json = json.dumps(c.get("evidence", {}), ensure_ascii=False)

        if existing:
            existing.confidence = c["final_confidence"]
            existing.match_method = "deterministic_v1"
            existing.evidence = evidence_json
            if existing.review_status != "verified":
                existing.review_status = review_status
            persisted.append(existing)
        else:
            new_link = HadithSharhLink(
                hadith_id=hadith_uuid,
                sharh_section_id=section_uuid,
                match_method="deterministic_v1",
                confidence=c["final_confidence"],
                review_status=review_status,
                verified=False,
                evidence=evidence_json,
                notes=f"Generated by Matching Engine v1 with confidence {c['confidence_percent']}%",
            )
            db.add(new_link)
            persisted.append(new_link)

    db.commit()
    return persisted


def link_sharh_section_to_hadiths(
    db: Session,
    section: SharhSection,
    collection_slug: str = "shahih_bukhari",
    candidate_limit: int = 5,
) -> list[HadithSharhLink]:
    """Legacy helper yang memanggil matching engine dan mem-persist kandidat."""
    candidates = get_matching_candidates(db, section, collection_slug=collection_slug, top_k=candidate_limit)
    return persist_matching_candidates(db, section, candidates=candidates, min_confidence=0.50)


def evaluate_against_gold(db: Session, gold_dataset_path: str = "data/fathul_bari/review/gold_links.json") -> dict[str, Any]:
    """Mengevaluasi performa linking engine terhadap dataset ground truth (Precision, Recall, F1)."""
    p = Path(gold_dataset_path)
    if not p.exists():
        return {"error": f"Gold dataset file tidak ditemukan di {gold_dataset_path}"}

    gold_items: list[dict[str, Any]] = json.loads(p.read_text(encoding="utf-8"))
    if not gold_items:
        return {"error": "Gold dataset kosong"}

    tp = 0
    fp = 0
    fn = 0
    eval_details = []

    for item in gold_items:
        vol = item.get("volume")
        page = item.get("page")
        target_hadith_num = item.get("hadith_number")

        sections = list(
            db.scalars(
                select(SharhSection).where(
                    SharhSection.work_slug == "fathul_bari",
                    SharhSection.volume == vol,
                    (SharhSection.printed_page == page) | (SharhSection.pdf_page == page) | (SharhSection.page == page),
                )
            )
        )

        matched_any = False
        for sec in sections:
            links = list(
                db.scalars(
                    select(HadithSharhLink).where(
                        HadithSharhLink.sharh_section_id == sec.id,
                    )
                )
            )
            for link in links:
                h = db.scalar(select(Hadith).where(Hadith.id == link.hadith_id))
                if h:
                    if h.external_number == target_hadith_num:
                        tp += 1
                        matched_any = True
                        eval_details.append({
                            "volume": vol,
                            "page": page,
                            "expected_hadith": target_hadith_num,
                            "predicted_hadith": h.external_number,
                            "confidence": link.confidence,
                            "result": "TRUE_POSITIVE",
                        })
                    else:
                        fp += 1
                        eval_details.append({
                            "volume": vol,
                            "page": page,
                            "expected_hadith": target_hadith_num,
                            "predicted_hadith": h.external_number,
                            "confidence": link.confidence,
                            "result": "FALSE_POSITIVE",
                        })

        if not matched_any:
            fn += 1
            eval_details.append({
                "volume": vol,
                "page": page,
                "expected_hadith": target_hadith_num,
                "predicted_hadith": None,
                "confidence": 0.0,
                "result": "FALSE_NEGATIVE",
            })

    precision = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 0.0
    recall = round((tp / (tp + fn)) * 100, 2) if (tp + fn) > 0 else 0.0
    f1 = round((2 * precision * recall) / (precision + recall), 2) if (precision + recall) > 0 else 0.0

    return {
        "total_gold_samples": len(gold_items),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision_percent": precision,
        "recall_percent": recall,
        "f1_score": f1,
        "details": eval_details,
    }
