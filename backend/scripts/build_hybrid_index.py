import json
import logging
import uuid
from sqlalchemy import select

from app.database import SessionLocal, engine, Base
from app.models import DocumentChunk, Hadith, HadithSharhLink, SharhSection
from app.services.arabic_normalizer import normalize_arabic
from app.services.hybrid_chunker import (
    detect_language,
    generate_multilingual_embedding,
    split_text_into_chunks,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_hybrid_index")


def build_index():
    print("=" * 70)
    print("  MEMBANGUN INDEKS HYBRID SEARCH (BM25 & MULTILINGUAL VECTOR)")
    print("=" * 70)

    # Pastikan tabel terbuat di database
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Ambil semua link verified untuk menandai chunk yang verified
        verified_links = list(db.scalars(select(HadithSharhLink).where(HadithSharhLink.verified == True)))
        verified_hadith_ids = {l.hadith_id for l in verified_links if l.hadith_id}
        verified_sharh_ids = {l.sharh_section_id for l in verified_links if l.sharh_section_id}

        print(f"[*] Terdeteksi {len(verified_links)} tautan relasi terverifikasi (Verified-First).")

        # 2. Hapus indeks lama jika ada
        db.query(DocumentChunk).delete()
        db.commit()
        print("[*] Indeks lama dibersihkan.")

        # 3. Indeks Hadis (Matan Arab & Terjemahan Indonesia)
        hadiths = list(db.scalars(select(Hadith)))
        print(f"[*] Mengindeks {len(hadiths)} data Hadis Shahih Bukhari...")

        chunk_count = 0
        for h in hadiths:
            is_v = h.id in verified_hadith_ids

            # A. Matan Arab
            if h.arabic_text:
                norm_ar = normalize_arabic(h.arabic_text)
                vec_ar = generate_multilingual_embedding(h.arabic_text)
                ch_ar = DocumentChunk(
                    id=uuid.uuid4(),
                    hadith_id=h.id,
                    chunk_type="hadith_matan",
                    text=h.arabic_text,
                    normalized_text=norm_ar,
                    language="ar",
                    volume=1,
                    printed_page=h.external_number,
                    verified=is_v,
                    embedding_json=json.dumps(vec_ar),
                )
                db.add(ch_ar)
                chunk_count += 1

            # B. Terjemahan Indonesia
            if h.translation:
                norm_id = normalize_arabic(h.translation)
                vec_id = generate_multilingual_embedding(h.translation)
                ch_id = DocumentChunk(
                    id=uuid.uuid4(),
                    hadith_id=h.id,
                    chunk_type="translation",
                    text=h.translation,
                    normalized_text=norm_id,
                    language="id",
                    volume=1,
                    printed_page=h.external_number,
                    verified=is_v,
                    embedding_json=json.dumps(vec_id),
                )
                db.add(ch_id)
                chunk_count += 1

        db.commit()
        print(f"[✓] {chunk_count} chunk Hadis berhasil diindeks.")

        # 4. Indeks Seksi Syarah Fathul Bari
        sections = list(db.scalars(select(SharhSection)))
        print(f"[*] Mengindeks {len(sections)} Seksi Naskah Fathul Bari...")

        sharh_chunk_count = 0
        for sec in sections:
            is_v = sec.id in verified_sharh_ids
            raw_text = sec.arabic_text or sec.title or ""
            if not raw_text:
                continue

            sub_chunks = split_text_into_chunks(raw_text, max_chars=900, overlap=150)
            for sub in sub_chunks:
                norm_sub = normalize_arabic(sub)
                vec_sub = generate_multilingual_embedding(sub)
                lang = detect_language(sub)

                ch_sec = DocumentChunk(
                    id=uuid.uuid4(),
                    sharh_section_id=sec.id,
                    chunk_type="sharh_section",
                    text=sub,
                    normalized_text=norm_sub,
                    language=lang,
                    volume=sec.volume,
                    pdf_page=sec.pdf_page,
                    printed_page=sec.printed_page or sec.page,
                    verified=is_v,
                    embedding_json=json.dumps(vec_sub),
                )
                db.add(ch_sec)
                sharh_chunk_count += 1

        db.commit()
        print(f"[✓] {sharh_chunk_count} chunk Syarah Fathul Bari berhasil diindeks.")

        total_indexed = chunk_count + sharh_chunk_count
        print("=" * 70)
        print(f"  BERHASIL: Total {total_indexed} chunk terindeks ke database.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    build_index()
