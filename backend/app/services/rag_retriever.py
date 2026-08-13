"""RAG Multi-Signal Hybrid Retriever for Hadith & Fathul Bari.

Mengambil konteks hadis (Shahih al-Bukhari) dan Syarah Fathul Bari dari database lokal
secara cerdas berdasarkan nomor hadis, kata kunci, teks Arab, dan relasi tautan terverifikasi.
"""

import re
from typing import Any
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Collection, Hadith, HadithSharhLink, SharhSection
from app.services.arabic_normalizer import normalize_arabic


def extract_hadith_number_from_query(query: str) -> int | None:
    """Mendeteksi apakah query mengandung penyebutan nomor hadis spesifik."""
    patterns = [
        r'(?:hadis|hadits|no\.?|nomor)\s*(?:bukhari\s*)?#?\s*(\d+)',
        r'#\s*(\d+)',
        r'\b(?:ke|no|nomor)-(\d+)\b',
    ]
    for pattern in patterns:
        m = re.search(pattern, query, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    # Khusus kata bilangan umum
    lowered = query.lower()
    if "hadis pertama" in lowered or "hadits pertama" in lowered or "hadis ke-1" in lowered or "hadis 1" in lowered:
        return 1
    if "hadis kedua" in lowered or "hadits kedua" in lowered or "hadis ke-2" in lowered:
        return 2
    if "hadis ketiga" in lowered or "hadits ketiga" in lowered or "hadis ke-3" in lowered:
        return 3
    return None


def retrieve_rag_context(
    db: Session,
    query: str,
    kitab: str = "shahih_bukhari",
    hadith_number: int | None = None,
    limit_hadiths: int = 3,
    limit_sharh: int = 5,
) -> dict[str, Any]:
    """Mengambil hadis dan syarah terkait untuk dijadikan konteks RAG."""
    detected_num = hadith_number or extract_hadith_number_from_query(query)
    collection = db.scalar(select(Collection).where(Collection.slug == kitab))

    found_hadiths: list[Hadith] = []
    found_sharh: list[dict[str, Any]] = []

    # 1. Ambil hadis berdasarkan nomor jika terdeteksi
    if detected_num is not None and collection:
        h = db.scalar(
            select(Hadith).where(
                Hadith.collection_id == collection.id,
                Hadith.external_number == detected_num,
            )
        )
        if h:
            found_hadiths.append(h)

    # 2. Jika belum cukup, lakukan pencarian kata kunci pada hadis
    clean_query = re.sub(r'[^\w\s]', ' ', query).strip()
    keywords = [w for w in clean_query.split() if len(w) >= 3 and w.lower() not in ["apa", "bagaimana", "jelaskan", "menurut", "tentang", "fathul", "bari", "hadis", "hadits", "shahih", "bukhari", "ibnu", "hajar"]]

    if len(found_hadiths) < limit_hadiths and collection:
        conditions = []
        for kw in keywords[:3]:
            conditions.append(Hadith.translation.ilike(f"%{kw}%"))
            conditions.append(Hadith.arabic_text.ilike(f"%{kw}%"))

        if conditions:
            existing_ids = [h.id for h in found_hadiths]
            extra_h = list(
                db.scalars(
                    select(Hadith)
                    .where(
                        Hadith.collection_id == collection.id,
                        or_(*conditions),
                        Hadith.id.not_in(existing_ids) if existing_ids else True,
                    )
                    .limit(limit_hadiths - len(found_hadiths))
                )
            )
            found_hadiths.extend(extra_h)

    # 3. Ambil Syarah yang terhubung ke hadis yang ditemukan (Knowledge Links)
    sharh_ids_seen = set()
    for h in found_hadiths:
        links = list(
            db.scalars(
                select(HadithSharhLink)
                .where(HadithSharhLink.hadith_id == h.id)
                .order_by(HadithSharhLink.verified.desc(), HadithSharhLink.confidence.desc())
            )
        )
        for link in links:
            sec = db.scalar(select(SharhSection).where(SharhSection.id == link.sharh_section_id))
            if sec and sec.id not in sharh_ids_seen:
                sharh_ids_seen.add(sec.id)
                found_sharh.append({
                    "id": str(sec.id),
                    "work_slug": sec.work_slug,
                    "volume": sec.volume,
                    "page": sec.page,
                    "title": sec.title,
                    "arabic_text": sec.arabic_text,
                    "translation": sec.translation,
                    "link_confidence": link.confidence,
                    "link_method": link.match_method,
                    "review_status": link.review_status,
                    "verified": link.verified,
                    "related_hadith_number": h.external_number,
                })
                if len(found_sharh) >= limit_sharh:
                    break
        if len(found_sharh) >= limit_sharh:
            break

    # 4. Jika syarah masih kurang, cari langsung di tabel SharhSection
    if len(found_sharh) < limit_sharh and keywords:
        sharh_conds = []
        for kw in keywords[:3]:
            sharh_conds.append(SharhSection.title.ilike(f"%{kw}%"))
            sharh_conds.append(SharhSection.translation.ilike(f"%{kw}%"))
            sharh_conds.append(SharhSection.arabic_text.ilike(f"%{kw}%"))

        if sharh_conds:
            direct_secs = list(
                db.scalars(
                    select(SharhSection)
                    .where(
                        or_(*sharh_conds),
                        SharhSection.id.not_in(list(sharh_ids_seen)) if sharh_ids_seen else True,
                    )
                    .limit(limit_sharh - len(found_sharh))
                )
            )
            for sec in direct_secs:
                sharh_ids_seen.add(sec.id)
                found_sharh.append({
                    "id": str(sec.id),
                    "work_slug": sec.work_slug,
                    "volume": sec.volume,
                    "page": sec.page,
                    "title": sec.title,
                    "arabic_text": sec.arabic_text,
                    "translation": sec.translation,
                    "link_confidence": None,
                    "link_method": "direct_text_match",
                    "review_status": "unlinked",
                    "verified": False,
                    "related_hadith_number": None,
                })

    # Serialize Hadith objects
    serialized_hadiths = []
    for h in found_hadiths:
        serialized_hadiths.append({
            "id": str(h.id),
            "collection": "Shahih al-Bukhari",
            "number": h.external_number,
            "arabic_text": h.arabic_text,
            "translation": h.translation,
            "source_provenance": "Ahmad Sanusi Hadits API" if h.api_endpoint else "Database Lokal",
            "endpoint": h.api_endpoint,
        })

    # Susun formatted context untuk LLM
    context_lines = []
    context_lines.append("=== KONTEKS DATA RESMI DARI DATABASE TURATS ===")

    if serialized_hadiths:
        context_lines.append("\n[Koleksi Hadis Primer: Shahih al-Bukhari]")
        for h in serialized_hadiths:
            context_lines.append(f"- Hadis #{h['number']}:")
            context_lines.append(f"  Teks Arab: {h['arabic_text']}")
            context_lines.append(f"  Terjemahan: {h['translation']}")
            context_lines.append(f"  Sumber Provenance: {h['source_provenance']}")
    else:
        context_lines.append("\n[Koleksi Hadis]: Tidak ditemukan hadis yang spesifik.")

    if found_sharh:
        context_lines.append("\n[Syarah Fathul Bari karya Al-Hafizh Ibnu Hajar al-Asqalani]")
        for idx, s in enumerate(found_sharh, start=1):
            ver_str = "TERVERIFIKASI PENELITI" if s['verified'] else f"Status: {s['review_status']} (Confidence: {s['link_confidence'] or 0:.2f})"
            context_lines.append(f"- Bagian Syarah {idx}: {s['title']}")
            context_lines.append(f"  Lokasi: Jilid {s['volume']}, Halaman {s['page']} ({ver_str})")
            if s.get("related_hadith_number"):
                context_lines.append(f"  Menjelaskan Hadis: Bukhari #{s['related_hadith_number']}")
            if s.get("arabic_text"):
                context_lines.append(f"  Kutipan Teks Arab Syarah: {s['arabic_text']}")
            if s.get("translation"):
                context_lines.append(f"  Uraian Penjelasan: {s['translation']}")
    else:
        context_lines.append("\n[Syarah Fathul Bari]: Tidak ditemukan teks syarah yang langsung cocok.")

    context_lines.append("\n=== AKHIR KONTEKS ===")
    formatted_context = "\n".join(context_lines)

    return {
        "query": query,
        "detected_hadith_number": detected_num,
        "hadiths": serialized_hadiths,
        "sharh_sections": found_sharh,
        "formatted_context": formatted_context,
    }


class RAGRetriever:
    """Wrapper class untuk RAG retriever."""
    def __init__(self, db: Session):
        self.db = db

    def retrieve_evidence(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        res = retrieve_rag_context(self.db, query, limit_hadiths=top_k, limit_sharh=top_k)
        evidence = []
        for h in res.get("hadiths", []):
            evidence.append({
                "hadith_id": h.get("id"),
                "hadith_number": h.get("number"),
                "translation": h.get("translation")
            })
        for s in res.get("sharh_sections", []):
            evidence.append({
                "sharh_id": s.get("id"),
                "title": s.get("title"),
                "volume": s.get("volume"),
                "page": s.get("page")
            })
        return evidence

