import argparse
import json
import logging
from pathlib import Path

from app.database import SessionLocal
from app.models import SharhSection
from app.services.arabic_normalizer import normalize_arabic
from app.services.pdf_extractor import extract_pdf
from app.services.sharh_segmenter import segment_page_to_sections

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Ekstraksi & Normalisasi PDF Fathul Bari")
    parser.add_argument("--pdf", type=str, required=True, help="Path ke file PDF Fathul Bari")
    parser.add_argument("--volume", type=int, default=1, help="Nomor Jilid kitab (default: 1)")
    parser.add_argument("--output-extracted", type=str, default="data/fathul_bari/extracted", help="Direktori teks per halaman")
    parser.add_argument("--output-normalized", type=str, default="data/fathul_bari/normalized", help="Direktori pages.json")
    parser.add_argument("--save-db", action="store_true", help="Simpan seksi langsung ke database")
    args = parser.parse_args()

    print("=" * 65)
    print("  FATHUL BARI RESEARCH - PDF EXTRACTION PIPELINE")
    print(f"  PDF File : {args.pdf}")
    print(f"  Volume   : Jilid {args.volume}")
    print("=" * 65)

    # 1. Ekstraksi teks dari PDF
    pages = extract_pdf(args.pdf, args.output_extracted)
    print(f"[✓] Berhasil mengekstrak {len(pages)} halaman dari PDF.")

    # 2. Normalisasi & Simpan pages.json
    normalized_pages = []
    all_sections = []

    for p in pages:
        norm_text = normalize_arabic(p["text"])
        normalized_pages.append({
            "pdf_page": p["pdf_page"],
            "printed_page": p["printed_page"],
            "text": p["text"],
            "normalized_text": norm_text,
            "source_file": p["source_file"],
            "source_hash": p["source_hash"],
        })

        # Segmentasi halaman ke seksi-seksi syarah
        sections = segment_page_to_sections(p, volume=args.volume)
        all_sections.extend(sections)

    norm_dir = Path(args.output_normalized)
    norm_dir.mkdir(parents=True, exist_ok=True)
    json_path = norm_dir / "pages.json"
    json_path.write_text(json.dumps(normalized_pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Berhasil menyimpan metadata normalisasi ke {json_path}")
    print(f"[✓] Terbentuk {len(all_sections)} seksi ulasan syarah terstruktur.")

    # 3. Simpan ke database jika diminta
    if args.save_db:
        db = SessionLocal()
        try:
            inserted = 0
            for sec in all_sections:
                db_sec = SharhSection(
                    work_slug=sec["work_slug"],
                    volume=sec["volume"],
                    pdf_page=sec["pdf_page"],
                    printed_page=sec["printed_page"],
                    page=sec["page"],
                    section_order=sec["section_order"],
                    title=sec["title"],
                    arabic_text=sec["arabic_text"],
                    normalized_text=sec["normalized_text"],
                    source_file=sec["source_file"],
                    source_hash=sec["source_hash"],
                    extraction_status="segmented",
                )
                db.add(db_sec)
                inserted += 1
            db.commit()
            print(f"[✓] Berhasil menyimpan {inserted} seksi syarah ke PostgreSQL database.")
        finally:
            db.close()

    print("=" * 65)
    print("  EKSTRAKSI TAHAP 3 SELESAI")
    print("=" * 65)


if __name__ == "__main__":
    main()
