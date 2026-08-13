from sqlalchemy import func, select
from app.database import SessionLocal
from app.models import Collection, Hadith, SyncRun, SharhSection, HadithSharhLink

EXPECTED = 7008

db = SessionLocal()

try:
    print("=" * 65)
    print("  FATHUL BARI RESEARCH - VALIDASI DATA INTEGRITAS")
    print("=" * 65)

    collection = db.scalar(select(Collection).where(Collection.slug == "shahih_bukhari"))
    if not collection:
        print("[!] ERROR: Collection 'shahih_bukhari' belum di-seed.")
        raise SystemExit(1)

    numbers = list(db.scalars(
        select(Hadith.external_number)
        .where(Hadith.collection_id == collection.id)
        .order_by(Hadith.external_number)
    ))

    count = len(numbers)
    missing = [n for n in range(1, EXPECTED + 1) if n not in set(numbers)]

    missing_arabic = db.scalar(select(func.count()).select_from(Hadith).where(
        Hadith.collection_id == collection.id,
        (Hadith.arabic_text.is_(None)) | (func.trim(Hadith.arabic_text) == "")
    )) or 0

    missing_translation = db.scalar(select(func.count()).select_from(Hadith).where(
        Hadith.collection_id == collection.id,
        (Hadith.translation.is_(None)) | (func.trim(Hadith.translation) == "")
    )) or 0

    # Deteksi Duplikasi
    duplicate_rows = list(db.execute(
        select(Hadith.external_number, func.count())
        .where(Hadith.collection_id == collection.id)
        .group_by(Hadith.external_number)
        .having(func.count() > 1)
    ).all())

    sharh_count = db.scalar(select(func.count()).select_from(SharhSection)) or 0
    link_count = db.scalar(select(func.count()).select_from(HadithSharhLink)) or 0
    total_syncs = db.scalar(select(func.count()).select_from(SyncRun)) or 0

    pct = (count / EXPECTED) * 100 if EXPECTED > 0 else 0

    print(f"  Kitab               : {collection.name} ({collection.slug})")
    print(f"  Target Ekspektasi   : {EXPECTED} hadis")
    print(f"  Tersimpan di DB     : {count} hadis ({pct:.2f}%)")
    print(f"  Hadis Belum Diambil : {len(missing)}")
    if missing:
        sample_missing = missing[:10]
        print(f"  Sample Belum Ada    : {sample_missing}{' ...' if len(missing) > 10 else ''}")
    print(f"  Duplikasi Data      : {len(duplicate_rows)} nomor terduplikasi")
    print(f"  Missing Teks Arab   : {missing_arabic}")
    print(f"  Missing Terjemahan  : {missing_translation}")
    print("-" * 65)
    print(f"  Syarah Sections     : {sharh_count}")
    print(f"  Hadith-Sharh Links  : {link_count}")
    print(f"  Riwayat Sync Runs   : {total_syncs}")
    print("=" * 65)

    if count == EXPECTED and missing_arabic == 0 and missing_translation == 0 and len(duplicate_rows) == 0:
        print("  STATUS: [✓] INTEGRITAS SEMPURNA (100% LENGKAP & VALID)")
    elif count > 0:
        print(f"  STATUS: [⚡] SEBAGIAN TERSEDIA ({count}/{EXPECTED} hadis tersimpan)")
    else:
        print("  STATUS: [!] KOSONG - Silakan jalankan sync_bukhari.py atau gunakan UI untuk import.")
    print("=" * 65)

finally:
    db.close()

