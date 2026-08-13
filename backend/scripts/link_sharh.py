import argparse
import json
from sqlalchemy import select

from app.database import SessionLocal
from app.models import SharhSection
from app.services.hadith_linker import evaluate_against_gold, link_sharh_section_to_hadiths


def main():
    parser = argparse.ArgumentParser(description="Hadith-Sharh Linking Engine CLI")
    parser.add_argument("--volume", type=int, default=None, help="Batasi ke jilid tertentu")
    parser.add_argument("--gold-eval", action="store_true", help="Jalankan evaluasi Precision/Recall terhadap gold_links.json")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("=" * 65)
        print("  FATHUL BARI RESEARCH - HADITH–SHARH LINKING ENGINE")
        print("=" * 65)

        stmt = select(SharhSection).where(SharhSection.work_slug == "fathul_bari")
        if args.volume is not None:
            stmt = stmt.where(SharhSection.volume == args.volume)

        sections = list(db.scalars(stmt))
        print(f"Mengevaluasi {len(sections)} seksi ulasan Fathul Bari...")

        total_links = 0
        for sec in sections:
            links = link_sharh_section_to_hadiths(db, sec)
            total_links += len(links)

        print(f"[✓] Berhasil menghasilkan {total_links} tautan hadits–syarah.")

        if args.gold_eval:
            print("\n" + "-" * 65)
            print("  EVALUASI TERHADAP GROUND TRUTH (GOLD DATASET)")
            print("-" * 65)
            res = evaluate_against_gold(db)
            if "error" in res:
                print(f"[!] {res['error']}")
            else:
                print(f"  Total Sampel Gold : {res['total_gold_samples']}")
                print(f"  True Positives (TP): {res['true_positives']}")
                print(f"  False Positives(FP): {res['false_positives']}")
                print(f"  False Negatives(FN): {res['false_negatives']}")
                print(f"  Precision          : {res['precision_percent']}%")
                print(f"  Recall             : {res['recall_percent']}%")
                print(f"  F1-Score           : {res['f1_score']}")
            print("-" * 65)

        print("=" * 65)
        print("  LINKING ENGINE SELESAI")
        print("=" * 65)

    finally:
        db.close()


if __name__ == "__main__":
    main()
