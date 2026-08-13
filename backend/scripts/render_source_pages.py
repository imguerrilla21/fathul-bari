import argparse
import logging
from sqlalchemy import select

from app.database import SessionLocal
from app.models import SharhSection
from app.services.pdf_renderer import render_pdf_page_image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("render_source_pages")


def main():
    parser = argparse.ArgumentParser(description="Render Citra Halaman Sumber Naskah/PDF Fathul Bari (Tahap 6)")
    parser.add_argument("--volume", type=int, default=None, help="Filter nomor jilid")
    parser.add_argument("--sharh-id", type=str, default=None, help="ID seksi tertentu")
    parser.add_argument("--page", type=int, default=None, help="Nomor halaman tertentu")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        query = select(SharhSection)
        if args.sharh_id:
            query = query.where(SharhSection.id == args.sharh_id)
        if args.volume:
            query = query.where(SharhSection.volume == args.volume)
        if args.page:
            query = query.where(SharhSection.printed_page == args.page)

        sections = list(db.scalars(query.order_by(SharhSection.volume, SharhSection.printed_page)))
        if not sections:
            print("[!] Tidak ada seksi ulasan yang cocok untuk dirender.")
            return

        print("=" * 70)
        print("  FATHUL BARI SOURCE PAGE RENDERER (TAHAP 6)")
        print(f"  Memproses {len(sections)} seksi naskah...")
        print("=" * 70)

        rendered_count = 0
        for sec in sections:
            vol = sec.volume or 1
            p_page = sec.printed_page or sec.pdf_page or sec.page or 1
            img_path = render_pdf_page_image(
                volume=vol,
                pdf_page=sec.pdf_page or p_page,
                printed_page=p_page,
                text_content=sec.arabic_text or sec.title,
            )
            sec.page_image_path = str(img_path.as_posix())
            rendered_count += 1
            print(f"[✓] Jilid {vol:02d} Hal. {p_page:03d} -> {img_path}")

        db.commit()
        print("=" * 70)
        print(f"  SELESAI: {rendered_count} citra halaman berhasil dirender.")
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    main()
