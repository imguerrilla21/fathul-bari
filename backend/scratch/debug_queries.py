from app.database import SessionLocal
from app.services.hybrid_search import hybrid_search

db = SessionLocal()
try:
    print("=== DEBUG QUERY 4 ===")
    res4 = hybrid_search(db, "صلصلة الجرس في بدء الوحي", retrieval_mode="study", limit=8)
    for i, r in enumerate(res4["results"], 1):
        print(f"Rank {i}: Hadith #{r.get('hadith_number')} Vol {r.get('volume')} Hal {r.get('printed_page')} | Lex: {r['lexical_score']} Vec: {r['vector_score']} Final: {r['relevance_score']} | Verified: {r['verified']} | Type: {r['chunk_type']}")

    print("\n=== DEBUG QUERY 9 ===")
    res9 = hybrid_search(db, "Hukum jual beli dan larangan menimbun barang atau riba dalam muamalah", retrieval_mode="study", limit=10)
    for i, r in enumerate(res9["results"], 1):
        print(f"Rank {i}: Hadith #{r.get('hadith_number')} Vol {r.get('volume')} Hal {r.get('printed_page')} | Lex: {r['lexical_score']} Vec: {r['vector_score']} Final: {r['relevance_score']} | Verified: {r['verified']} | Type: {r['chunk_type']}")
finally:
    db.close()
