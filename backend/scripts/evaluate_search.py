import json
import math
import logging
import time
from sqlalchemy import select

from app.database import SessionLocal
from app.services.hybrid_search import hybrid_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_search")

# Golden Evaluation Dataset untuk Riset Fathul Bari & Shahih Bukhari
GOLDEN_DATASET = [
    {
        "id": "q1",
        "query": "Apa hubungan niat dengan amal menurut Ibnu Hajar?",
        "lang": "id",
        "expected_hadith": 1,
        "expected_volume": 1,
        "expected_page": 9,
        "keywords": ["niat", "amal", "النية", "الأعمال"],
    },
    {
        "id": "q2",
        "query": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
        "lang": "ar",
        "expected_hadith": 1,
        "expected_volume": 1,
        "expected_page": 9,
        "keywords": ["الأعمال", "بالنيات"],
    },
    {
        "id": "q3",
        "query": "Bagaimana permulaan wahyu turun kepada Nabi seperti gemerincing lonceng?",
        "lang": "id",
        "expected_hadith": 2,
        "expected_volume": 1,
        "expected_page": 24,
        "keywords": ["lonceng", "صلصلة", "جرس"],
    },
    {
        "id": "q4",
        "query": "صلصلة الجرس في بدء الوحي ونزول القرآن",
        "lang": "ar",
        "expected_hadith": 2,
        "expected_volume": 1,
        "expected_page": 24,
        "keywords": ["صلصلة", "الجرس"],
    },
    {
        "id": "q5",
        "query": "Mimpi yang benar sebagai awal kenabian di Gua Hira",
        "lang": "id",
        "expected_hadith": 3,
        "expected_volume": 1,
        "expected_page": 35,
        "keywords": ["mimpi", "hira", "رؤيا"],
    },
    {
        "id": "q6",
        "query": "الرؤيا الصالحة في النوم أول ما بدئ به رسول الله",
        "lang": "ar",
        "expected_hadith": 3,
        "expected_volume": 1,
        "expected_page": 35,
        "keywords": ["الرؤيا", "الصالحة"],
    },
    {
        "id": "q7",
        "query": "Jibril membacakan wahyu Al-Quran dan Rasulullah menggerakkan lidahnya karena tergesa",
        "lang": "id",
        "expected_hadith": 4,
        "expected_volume": 1,
        "expected_page": 42,
        "keywords": ["jibril", "wahyu", "lidah", "تنزيل"],
    },
    {
        "id": "q8",
        "query": "Keutamaan ilmu dan bagaimana ilmu diangkat dengan wafatnya para ulama",
        "lang": "id",
        "expected_hadith": 59,
        "expected_volume": 1,
        "expected_page": 60,
        "keywords": ["ilmu", "ulama", "علم"],
    },
    {
        "id": "q9",
        "query": "Tata cara thawaf kaum wanita dan mencium Hajar Aswad menurut Aisyah",
        "lang": "id",
        "expected_hadith": 1513,
        "expected_volume": 4,
        "expected_page": 305,
        "keywords": ["thawaf", "hajar", "aswad", "طواف"],
    },
    {
        "id": "q10",
        "query": "Muslim yang sejati adalah yang orang lain selamat dari lisan dan tangannya",
        "lang": "id",
        "expected_hadith": 10,
        "expected_volume": 1,
        "expected_page": 72,
        "keywords": ["muslim", "lisan", "tangan", "لسانه"],
    },
]


def evaluate():
    print("=" * 80)
    print("  EVALUASI GOLDEN DATASET: HYBRID ARABIC & MULTILINGUAL SEARCH ENGINE")
    print("=" * 80)

    db = SessionLocal()
    try:
        hits_at_1 = 0
        hits_at_5 = 0
        hits_at_10 = 0
        reciprocal_ranks = []
        ndcg_scores = []
        precision_at_5_list = []
        latencies = []

        print(f"{'No':<4} {'Bahasa':<8} {'Query':<42} {'Target':<10} {'Rank':<6} {'Score':<8} {'Status'}")
        print("-" * 95)

        for i, item in enumerate(GOLDEN_DATASET, start=1):
            t0 = time.perf_counter()
            res = hybrid_search(
                db=db,
                query=item["query"],
                retrieval_mode="study",
                limit=10,
            )
            lat = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat)

            # Evaluasi posisi rank target hadith/volume/page
            target_h = item.get("expected_hadith")
            target_vol = item.get("expected_volume")
            target_p = item.get("expected_page")

            found_rank = None
            found_score = 0.0

            results = res.get("results", [])
            for r_idx, r in enumerate(results, start=1):
                is_match = False
                if target_h and r.get("hadith_number") == target_h:
                    is_match = True
                elif target_vol and target_p and r.get("volume") == target_vol and r.get("printed_page") == target_p:
                    is_match = True
                elif target_vol and r.get("volume") == target_vol and any(kw.lower() in r.get("text", "").lower() for kw in item["keywords"]):
                    is_match = True

                if is_match and found_rank is None:
                    found_rank = r_idx
                    found_score = r.get("relevance_score", 0.0)

            # Hitung metrik
            if found_rank == 1:
                hits_at_1 += 1
            if found_rank is not None and found_rank <= 5:
                hits_at_5 += 1
                precision_at_5_list.append(1.0 / min(5, len(results)))
            else:
                precision_at_5_list.append(0.0)

            if found_rank is not None and found_rank <= 10:
                hits_at_10 += 1

            if found_rank is not None:
                rr = 1.0 / found_rank
                reciprocal_ranks.append(rr)
                dcg = 1.0 / math.log2(found_rank + 1)
                idcg = 1.0 / math.log2(1 + 1)
                ndcg_scores.append(dcg / idcg)
            else:
                reciprocal_ranks.append(0.0)
                ndcg_scores.append(0.0)

            status_str = f"[✓ TOP {found_rank}]" if found_rank else "[✗ MISS]"
            q_short = (item['query'][:38] + "..") if len(item['query']) > 40 else item['query']
            print(
                f"{i:<4} {item['lang'].upper():<8} {q_short:<42} #{target_h or '-' :<9} {found_rank or '-' :<6} {found_score:<8.3f} {status_str}"
            )

        n = len(GOLDEN_DATASET)
        recall_at_1 = (hits_at_1 / n) * 100.0
        recall_at_5 = (hits_at_5 / n) * 100.0
        recall_at_10 = (hits_at_10 / n) * 100.0
        mrr = sum(reciprocal_ranks) / n
        avg_ndcg = sum(ndcg_scores) / n
        avg_prec_5 = sum(precision_at_5_list) / n
        avg_lat = sum(latencies) / n

        print("=" * 80)
        print("  REKAPITULASI METRIK EVALUASI:")
        print(f"  • Recall@1         : {recall_at_1:.1f}%")
        print(f"  • Recall@5 (Target > 90%): {recall_at_5:.1f}% {'[PASS ✓]' if recall_at_5 >= 90 else '[ATTN !]'}")
        print(f"  • Recall@10        : {recall_at_10:.1f}%")
        print(f"  • MRR (Target > 0.80)   : {mrr:.3f} {'[PASS ✓]' if mrr >= 0.80 else '[ATTN !]'}")
        print(f"  • NDCG@5           : {avg_ndcg:.3f}")
        print(f"  • Rata-rata Latensi: {avg_lat:.2f} ms")
        print("=" * 80)

        return {
            "total_queries": n,
            "recall_at_1": round(recall_at_1, 2),
            "recall_at_5": round(recall_at_5, 2),
            "recall_at_10": round(recall_at_10, 2),
            "mrr": round(mrr, 3),
            "ndcg_at_5": round(avg_ndcg, 3),
            "avg_precision_at_5": round(avg_prec_5, 3),
            "avg_latency_ms": round(avg_lat, 2),
            "passed_targets": bool(recall_at_5 >= 90.0 and mrr >= 0.80),
        }
    finally:
        db.close()


if __name__ == "__main__":
    evaluate()
