import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

from app.database import SessionLocal
from app.models import AuditLog, SharhSection
from app.services.arabic_normalizer import normalize_arabic
from app.services.audit_logger import log_audit_event
from app.services.hadith_reference_detector import detect_hadith_references
from app.services.pdf_renderer import find_pdf_for_volume, render_pdf_page_image
from app.services.sharh_segmenter import segment_page_to_sections

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_fathul_bari")


def parse_raw_vol_file(file_path: Path, volume: int) -> list[dict[str, Any]]:
    """Membaca file raw volume Fathul Bari dan membaginya per halaman."""
    content = file_path.read_text(encoding="utf-8")
    page_blocks = re.split(r"===\s*\[FATHUL BARI JILID \d+ - HALAMAN (\d+)\]\s*===", content)
    
    pdf_file = find_pdf_for_volume(volume)
    doc_path = str(pdf_file.as_posix()) if pdf_file else str(file_path.as_posix())

    pages = []
    if len(page_blocks) > 1:
        # page_blocks[0] adalah preamble/header jika ada
        for i in range(1, len(page_blocks), 2):
            page_num = int(page_blocks[i])
            text = page_blocks[i + 1].strip()
            if text:
                file_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                pages.append({
                    "volume": volume,
                    "pdf_page": page_num,
                    "printed_page": page_num,
                    "page": page_num,
                    "text": text,
                    "normalized_text": normalize_arabic(text),
                    "source_file": file_path.name,
                    "source_hash": file_hash,
                    "source_document_path": doc_path,
                })
    else:
        # Single page fallback
        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        pages.append({
            "volume": volume,
            "pdf_page": 1,
            "printed_page": 1,
            "page": 1,
            "text": content.strip(),
            "normalized_text": normalize_arabic(content),
            "source_file": file_path.name,
            "source_hash": file_hash,
            "source_document_path": doc_path,
        })
    return pages


def run_ingestion():
    raw_dir = Path("data/fathul_bari/raw")
    extracted_dir = Path("data/fathul_bari/extracted")
    normalized_dir = Path("data/fathul_bari/normalized")
    rendered_dir = Path("data/fathul_bari/rendered")

    extracted_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    rendered_dir.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(raw_dir.glob("fathul_bari_jilid_*.txt"))
    if not raw_files:
        logger.warning("Tidak ada file raw yang ditemukan di %s", raw_dir)
        return

    all_pages = []
    all_sections = []
    all_references = []

    print("=" * 70)
    print("  FATHUL BARI COMPREHENSIVE INGESTION & AUDIT PIPELINE")
    print(f"  Memproses {len(raw_files)} volume naskah...")
    print("=" * 70)

    for rf in raw_files:
        match_vol = re.search(r"jilid_(\d+)", rf.name)
        volume = int(match_vol.group(1)) if match_vol else 1
        
        pages = parse_raw_vol_file(rf, volume)
        print(f"[*] {rf.name}: Diekstrak {len(pages)} halaman ulasan.")

        for p in pages:
            # 1. Simpan file teks per halaman di extracted/
            page_filename = f"jilid_{volume:02d}_hal_{p['printed_page']:03d}.txt"
            extracted_path = extracted_dir / page_filename
            extracted_path.write_text(p["text"], encoding="utf-8")

            # 2. Render citra visual naskah/PDF ke rendered/
            img_path = render_pdf_page_image(
                volume=volume,
                pdf_page=p["pdf_page"],
                printed_page=p["printed_page"],
                text_content=p["text"],
            )
            p["page_image_path"] = str(img_path.as_posix())

            # 3. Deteksi referensi hadis
            refs = detect_hadith_references(p["text"], p["normalized_text"])
            if refs:
                all_references.append({
                    "volume": volume,
                    "page": p["printed_page"],
                    "references": [r.model_dump() for r in refs],
                })

            # 4. Segmentasi halaman ke seksi syarah terstruktur
            sections = segment_page_to_sections(p, volume=volume)
            for sec in sections:
                sec["source_document_path"] = p.get("source_document_path")
                sec["page_image_path"] = p.get("page_image_path")
            all_sections.extend(sections)
            all_pages.append(p)

    # Simpan JSON hasil
    pages_json_path = normalized_dir / "pages.json"
    pages_json_path.write_text(json.dumps(all_pages, ensure_ascii=False, indent=2), encoding="utf-8")

    refs_json_path = normalized_dir / "references.json"
    refs_json_path.write_text(json.dumps(all_references, ensure_ascii=False, indent=2), encoding="utf-8")

    sections_json_path = normalized_dir / "sections.json"
    sections_json_path.write_text(json.dumps(all_sections, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[✓] Berhasil menyimpan {len(all_pages)} halaman ke {pages_json_path}")
    print(f"[✓] Berhasil menyimpan {len(all_references)} referensi ke {refs_json_path}")
    print(f"[✓] Terbentuk {len(all_sections)} seksi ulasan syarah di {sections_json_path}")

    # Simpan/update ke database dan catat AuditLog
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        for sec in all_sections:
            existing = db.query(SharhSection).filter(
                SharhSection.work_slug == sec["work_slug"],
                SharhSection.volume == sec["volume"],
                SharhSection.printed_page == sec["printed_page"],
                SharhSection.section_order == sec["section_order"],
            ).first()

            if existing:
                existing.title = sec["title"]
                existing.arabic_text = sec["arabic_text"]
                existing.normalized_text = sec["normalized_text"]
                existing.source_file = sec["source_file"]
                existing.source_hash = sec["source_hash"]
                existing.source_document_path = sec.get("source_document_path")
                existing.page_image_path = sec.get("page_image_path")
                updated += 1
            else:
                new_sec = SharhSection(
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
                    source_document_path=sec.get("source_document_path"),
                    page_image_path=sec.get("page_image_path"),
                    extraction_status="segmented",
                )
                db.add(new_sec)
                db.flush()

                # Catat event audit INGEST untuk seksi baru
                log_audit_event(
                    db=db,
                    entity_type="sharh_section",
                    entity_id=new_sec.id,
                    action="INGEST",
                    actor="system_pipeline",
                    after_state={
                        "volume": new_sec.volume,
                        "page": new_sec.printed_page,
                        "title": new_sec.title,
                        "source_file": new_sec.source_file,
                        "source_hash": new_sec.source_hash,
                    },
                    notes=f"Diekstrak dari {new_sec.source_file} halaman {new_sec.printed_page}",
                )
                inserted += 1

        db.commit()
        print(f"[✓] Database Sinkronisasi: {inserted} baru, {updated} diperbarui.")
    finally:
        db.close()

    print("=" * 70)
    print("  INGESTION & AUDIT DATA FATHUL BARI SELESAI!")
    print("=" * 70)


if __name__ == "__main__":
    run_ingestion()
