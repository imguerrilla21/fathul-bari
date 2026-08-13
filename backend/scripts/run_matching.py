import argparse
import sys
from sqlalchemy import select

from app.database import SessionLocal
from app.models import SharhSection
from app.services.hadith_linker import get_matching_candidates, persist_matching_candidates


def main():
    parser = argparse.ArgumentParser(description="Tahap 4 Hadith–Sharh Matching Engine (v1)")
    parser.add_argument("--sharh-id", type=str, default=None, help="UUID seksi syarah tertentu")
    parser.add_argument("--top-k", type=int, default=10, help="Jumlah kandidat teratas yang dievaluasi (default: 10)")
    parser.add_argument("--persist", action="store_true", help="Simpan hasil matching ke database hadith_sharh_links")
    parser.add_argument("--min-confidence", type=float, default=0.50, help="Ambang batas confidence minimal untuk disimpan (default: 0.50)")
    parser.add_argument("--volume", type=int, default=None, help="Batasi ke jilid tertentu")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("=" * 80)
        print("  FATHUL BARI RESEARCH - HADITH–SHARH MATCHING ENGINE (v1)")
        print("  Formula: final = number_score*0.50 + text_score*0.35 + context_score*0.15")
        print("  Thresholds: >=0.90 auto_candidate | 0.75-0.89 review | 0.50-0.74 weak_match")
        print("=" * 80)

        sections: list[SharhSection] = []

        if args.sharh_id:
            sec = db.scalar(select(SharhSection).where(SharhSection.id == args.sharh_id))
            if not sec:
                print(f"[!] ERROR: Seksi syarah dengan ID {args.sharh_id} tidak ditemukan.")
                return
            sections = [sec]
        else:
            stmt = select(SharhSection).where(SharhSection.work_slug == "fathul_bari")
            if args.volume is not None:
                stmt = stmt.where(SharhSection.volume == args.volume)
            sections = list(db.scalars(stmt.order_by(SharhSection.volume, SharhSection.printed_page)))

        if not sections:
            print("[!] Tidak ada seksi syarah yang ditemukan. Jalankan seed-sample atau extract_fathul_bari.py terlebih dahulu.")
            return

        print(f"Menjalankan matching engine untuk {len(sections)} seksi ulasan...\n")

        total_persisted = 0

        for sec in sections:
            page_info = sec.printed_page or sec.pdf_page or sec.page or "-"
            print(f"┌─ [{sec.work_slug.upper()}] Jilid {sec.volume} Hal. {page_info}: {sec.title}")
            print(f"│  ID: {sec.id}")
            print("├" + "─" * 78)

            candidates = get_matching_candidates(db, sec, top_k=args.top_k)

            if not candidates:
                print("│  (Tidak ada kandidat hadis yang cocok di database)")
            else:
                print(f"│  {'Rank':<4} {'Hadis':<10} {'No.Score':<10} {'Text.Score':<12} {'Ctx.Score':<10} {'Final':<10} {'Kategori':<15}")
                print("│  " + "-" * 74)

                for idx, c in enumerate(candidates, start=1):
                    star = "★" if c["final_confidence"] >= 0.90 else " "
                    print(
                        f"│  {idx:<2} {star} #{c['hadith_number']:<8} "
                        f"{c['number_score']:<10.2f} {c['text_score']:<12.4f} {c['context_score']:<10.2f} "
                        f"{c['final_confidence']:<10.4f} {c['category']:<15}"
                    )

            if args.persist:
                persisted = persist_matching_candidates(db, sec, candidates=candidates, min_confidence=args.min_confidence)
                total_persisted += len(persisted)
                print(f"│  >> [PERSISTED] {len(persisted)} tautan disimpan ke hadith_sharh_links (min_conf: {args.min_confidence})")

            print("└" + "─" * 78 + "\n")

        print("=" * 80)
        if args.persist:
            print(f"  SELESAI: Total {total_persisted} tautan kandidat berhasil disimpan ke database.")
        else:
            print("  SELESAI (Dry-Run Mode). Gunakan flag '--persist' untuk menyimpan hasil ke database.")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()
