import argparse
import asyncio
from datetime import datetime, timezone
import sys
import time

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Source, Collection, Hadith, SyncRun
from app.services.ahmad_sanusi import AhmadSanusiClient
from app.services.hadith_normalizer import normalize_hadith

KITAB = "shahih_bukhari"


async def sync(start: int, end: int, delay: float | None = None):
    sleep_delay = delay if delay is not None else settings.sync_delay_seconds
    total_items = end - start + 1
    start_time = time.time()

    print("=" * 65)
    print(f"  FATHUL BARI RESEARCH - SYNC PIPELINE: {KITAB.upper()}")
    print(f"  Rentang: #{start} s/d #{end} ({total_items} hadis)")
    print(f"  Delay antar request: {sleep_delay} detik")
    print("=" * 65)

    db = SessionLocal()
    run = SyncRun(
        collection_slug=KITAB,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        source = db.scalar(select(Source).where(Source.name == "Ahmad Sanusi Hadits API"))
        collection = db.scalar(select(Collection).where(Collection.slug == KITAB))

        if not source or not collection:
            raise RuntimeError("Database belum di-seed. Jalankan 'python scripts/seed.py' terlebih dahulu.")

        client = AhmadSanusiClient()

        for idx, nomor in enumerate(range(start, end + 1), start=1):
            now_dt = datetime.now(timezone.utc)
            progress = (idx / total_items) * 100
            bar_len = 20
            filled = int(bar_len * idx / total_items)
            bar = "█" * filled + "░" * (bar_len - filled)

            print(f"[{bar}] {progress:5.1f}% (#{nomor:4d}) ... ", end="", flush=True)

            try:
                payload = await client.get_hadith(KITAB, nomor)
                data = payload.get("data")
                if not isinstance(data, dict):
                    raise ValueError(f"Payload hadis #{nomor} kosong atau tidak valid.")

                item = normalize_hadith(data)
                run.fetched += 1

                existing = db.scalar(select(Hadith).where(
                    Hadith.collection_id == collection.id,
                    Hadith.external_number == nomor,
                ))

                if existing:
                    if existing.content_hash != item["content_hash"]:
                        existing.arabic_text = item["arabic_text"]
                        existing.translation = item["translation"]
                        existing.content_hash = item["content_hash"]
                        existing.retrieved_at = now_dt
                        run.updated += 1
                        print("UPDATED", flush=True)
                    else:
                        print("CACHED/MATCH", flush=True)
                else:
                    db.add(Hadith(
                        collection_id=collection.id,
                        source_id=source.id,
                        external_number=nomor,
                        arabic_text=item["arabic_text"],
                        translation=item["translation"],
                        content_hash=item["content_hash"],
                        api_endpoint=f"/v1/hadits/{KITAB}/{nomor}",
                        retrieved_at=now_dt,
                    ))
                    run.inserted += 1
                    print("INSERTED", flush=True)

                db.commit()

            except Exception as exc:
                db.rollback()
                run.failed += 1
                print(f"ERROR ({exc})", flush=True)
                db.commit()

            if sleep_delay > 0 and idx < total_items:
                await asyncio.sleep(sleep_delay)

        elapsed = time.time() - start_time
        run.status = "completed" if run.failed == 0 else "completed_with_errors"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()

        print("\n" + "=" * 65)
        print("  RINGKASAN SINKRONISASI")
        print("=" * 65)
        print(f"  Total diproses : {total_items}")
        print(f"  Inserted (baru): {run.inserted}")
        print(f"  Updated        : {run.updated}")
        print(f"  Failed (gagal) : {run.failed}")
        print(f"  Waktu total    : {elapsed:.2f} detik ({total_items / max(elapsed, 0.001):.2f} hadis/detik)")
        print(f"  Status akhir   : {run.status}")
        print("=" * 65)

    except KeyboardInterrupt:
        db.rollback()
        run.status = "interrupted"
        run.error_message = "Dihentikan oleh user (KeyboardInterrupt)."
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        print("\n[!] Sinkronisasi dihentikan oleh user.")
    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        print(f"\n[!] Error fatal selama sinkronisasi: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Sinkronisasi Shahih Bukhari dari Ahmad Sanusi API")
    parser.add_argument("--start", type=int, default=1, help="Nomor hadis awal (default: 1)")
    parser.add_argument("--end", type=int, default=10, help="Nomor hadis akhir (default: 10)")
    parser.add_argument("--delay", type=float, default=None, help="Delay antar request dalam detik")
    args = parser.parse_args()
    asyncio.run(sync(args.start, args.end, args.delay))

