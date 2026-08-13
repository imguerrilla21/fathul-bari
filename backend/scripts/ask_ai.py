"""CLI Script untuk menguji Syarah AI Assistant & RAG Engine langsung dari terminal.

Contoh penggunaan:
python scripts/ask_ai.py --query "Jelaskan hadis tentang niat menurut Ibnu Hajar"
python scripts/ask_ai.py --hadith-number 2 --query "Bagaimana wahyu turun seperti gemerincing lonceng?"
"""

import argparse
import asyncio
import sys
from app.database import SessionLocal
from app.services.rag_retriever import retrieve_rag_context
from app.services.rag_synthesizer import synthesize_rag_response


async def main():
    parser = argparse.ArgumentParser(description="Uji Syarah AI Assistant (RAG) Fathul Bari.")
    parser.add_argument("--query", "-q", type=str, required=True, help="Pertanyaan riset atau topik hadis")
    parser.add_argument("--hadith-number", "-n", type=int, default=None, help="Nomor hadis spesifik (opsional)")
    parser.add_argument("--mode", "-m", type=str, default="syarah_focus", choices=["syarah_focus", "fiqh_faedah", "sanad_matan"], help="Mode riset AI")
    parser.add_argument("--kitab", "-k", type=str, default="shahih_bukhari", help="Slug kitab hadis")

    args = parser.parse_args()

    print(f"\n=======================================================")
    print(f"🤖 SYARAH AI ASSISTANT (RAG) — Fathul Bari Research")
    print(f"=======================================================")
    print(f"Query  : {args.query}")
    print(f"Mode   : {args.mode}")
    if args.hadith_number:
        print(f"Hadis  : #{args.hadith_number}")
    print(f"-------------------------------------------------------\n")

    db = SessionLocal()
    try:
        print("🔍 Menjalankan Hybrid Retrieval...")
        retrieval = retrieve_rag_context(
            db=db,
            query=args.query,
            kitab=args.kitab,
            hadith_number=args.hadith_number,
        )

        print(f"[✓] Hadis ditemukan  : {len(retrieval['hadiths'])}")
        print(f"[✓] Syarah ditemukan : {len(retrieval['sharh_sections'])}\n")

        print("⚡ Menjalankan AI Synthesis & Anti-Hallucination Audit...")
        synthesis = await synthesize_rag_response(
            query=args.query,
            rag_retrieval_result=retrieval,
            mode=args.mode,
        )

        print(f"[✓] Model / Provider : {synthesis['provider_used']}\n")
        print("===================== JAWABAN AI =====================")
        print(synthesis['answer'])
        print("\n======================================================")

        audit = synthesis.get('anti_hallucination_audit', {})
        print(f"\n🛡️ Anti-Hallucination Audit: {'PASSED (Clean)' if audit.get('passed') else 'WARNING'}")
        if not audit.get('passed'):
            print(f"   Unverified hadiths : {audit.get('unverified_hadiths')}")
            print(f"   Unverified pages   : {audit.get('unverified_pages')}")

        print(f"\n📚 Sitasi Terverifikasi ({len(synthesis.get('citations', []))} item):")
        for cit in synthesis.get('citations', []):
            ver_text = "Human Verified" if cit.get('verified') else "Auto Candidate"
            print(f"  - [{ver_text}] {cit.get('standard_citation')}")

    except Exception as exc:
        print(f"\n❌ Terjadi kesalahan: {exc}", file=sys.stderr)
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
