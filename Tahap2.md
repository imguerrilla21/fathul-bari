Baik. Saya lanjutkan ke **Tahap 2: database production + migrasi Alembic + sinkronisasi Shahih Bukhari yang aman dan terukur**.

Saya juga melakukan verifikasi ulang terhadap dokumentasi Ahmad Sanusi. Saat ini dokumentasi menyebut endpoint `/v1/hadits/{kitab}` memang menggunakan **paginasi**, sedangkan endpoint detail `/v1/hadits/{kitab}/{nomor}` memberikan Arab + terjemahan. Statistik yang tampil saat ini mencantumkan **7.008 hadis Shahih Bukhari**. ([Ahmad Sanusi][1])

> **Perubahan penting:** pada tahap ini kita tidak lagi memakai `Base.metadata.create_all()` sebagai mekanisme database production. Kita pindah ke **Alembic migration**, supaya schema aplikasi nantinya dapat berevolusi tanpa merusak data.

---

# Tahap 2 — Database Production

## 1. Target arsitektur

Setelah tahap ini, arsitekturnya menjadi:

```text
                 Ahmad Sanusi API
                        │
                        │ HTTPS
                        ▼
              ┌───────────────────┐
              │  Sync Worker       │
              │  Python            │
              └─────────┬─────────┘
                        │
                validate / normalize
                        │
                        ▼
              ┌───────────────────┐
              │    PostgreSQL     │
              │                   │
              │ sources           │
              │ collections       │
              │ hadiths           │
              │ translations      │
              │ sync_runs         │
              └─────────┬─────────┘
                        │
                        ▼
                 FastAPI Backend
                        │
                        ▼
                    Frontend
```

Dan yang sangat penting:

```text
Ahmad Sanusi API
       │
       ▼
RAW DATA
       │
       ▼
NORMALIZED DATA
       │
       ▼
VERIFIED DATA
```

Kita akan mempertahankan provenance sehingga setiap hadis dapat dilacak kembali ke sumber API.

---

# 2. Tambahkan Alembic

Ubah:

```text
backend/
```

menjadi:

```text
backend/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── app/
└── scripts/
```

Tambahkan ke `requirements.txt`:

```text
alembic
```

---

# 3. Model database final tahap 2

Saya sarankan schema kita sekarang menjadi:

```text
sources
    │
    ├───────────────┐
    │               │
    ▼               ▼
collections       sync_runs
    │
    ▼
hadiths
    │
    ▼
hadith_translations
```

Nantinya:

```text
hadiths
   │
   ▼
hadith_sharh_links
   │
   ▼
sharh_sections
```

Jadi sejak awal database sudah dipersiapkan untuk Fathul Bari.

---

# 4. Tabel `sources`

Kita tingkatkan dari schema sebelumnya.

```python
# backend/app/models/source.py

import uuid

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Source(Base):

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    base_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    license: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
```

---

# 5. Tabel collection

```python
# backend/app/models/collection.py

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Collection(Base):

    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="id",
        nullable=False,
    )

    total_expected: Mapped[int | None] = mapped_column(
        nullable=True,
    )
```

Untuk Bukhari:

```text
slug:
shahih_bukhari

name:
Shahih al-Bukhari

total_expected:
7008
```

Angka 7.008 mengikuti statistik yang ditampilkan dokumentasi API saat ini. ([Ahmad Sanusi Open API][2])

---

# 6. Tabel hadis

Sekarang kita buat lebih serius.

```python
# backend/app/models/hadith.py

import uuid

from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
    String,
    DateTime,
    UniqueConstraint,
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Hadith(Base):

    __tablename__ = "hadiths"

    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "external_number",
            name="uq_hadith_collection_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id"),
        nullable=False,
        index=True,
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=False,
        index=True,
    )

    external_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    arabic_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    translation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    api_endpoint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    retrieved_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
```

---

# 7. Kenapa `content_hash` penting?

Misalnya hari ini:

```text
Bukhari #1
arab = ABC
terjemah = XYZ
```

Besok API mengubah terjemahan.

Kita dapat mendeteksinya:

```text
old hash
     ↓
new hash
     ↓
DIFFERENT
     ↓
DATA BERUBAH
```

Jadi aplikasi kita tidak sekadar menyimpan data, tetapi juga bisa melakukan **data integrity tracking**.

---

# 8. Tabel `sync_runs`

Ini sangat saya rekomendasikan.

```python
# backend/app/models/sync_run.py

import uuid

from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SyncRun(Base):

    __tablename__ = "sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    collection_slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    fetched: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    inserted: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    updated: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
```

Sekarang kita dapat mengetahui:

```text
SYNC RUN #17

collection:
shahih_bukhari

fetched:
7008

inserted:
120

updated:
3

failed:
0

status:
completed
```

Ini sangat berguna ketika aplikasi sudah production.

---

# 9. Update model initializer

```python
# backend/app/models/__init__.py

from app.models.source import Source
from app.models.collection import Collection
from app.models.hadith import Hadith
from app.models.sync_run import SyncRun

__all__ = [
    "Source",
    "Collection",
    "Hadith",
    "SyncRun",
]
```

---

# 10. Inisialisasi Alembic

Di dalam container:

```bash
docker exec -it fathul_bari_backend \
alembic init alembic
```

Kemudian edit:

```text
backend/alembic.ini
```

Kita tidak akan menyimpan password database secara permanen di sini.

Di:

```text
backend/alembic/env.py
```

gunakan `settings.database_url`.

---

# 11. `alembic/env.py`

Bagian penting:

```python
from app.config import settings
from app.database import Base
from app.models import (
    Source,
    Collection,
    Hadith,
    SyncRun,
)

config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)

target_metadata = Base.metadata
```

Dengan demikian Alembic mengetahui seluruh model.

---

# 12. Buat migration pertama

Jalankan:

```bash
docker exec -it fathul_bari_backend \
alembic revision --autogenerate \
-m "initial hadith schema"
```

Kemudian:

```bash
docker exec -it fathul_bari_backend \
alembic upgrade head
```

Periksa:

```bash
docker exec -it fathul_bari_postgres \
psql -U fathul -d fathul_bari
```

Kemudian:

```sql
\dt
```

Target:

```text
collections
hadiths
sources
sync_runs
alembic_version
```

---

# 13. Jangan lagi memakai `create_all()`

Hapus dari `main.py`:

```python
Base.metadata.create_all(bind=engine)
```

Karena sekarang:

```text
Alembic
   ↓
Database Schema
```

bukan:

```text
FastAPI startup
   ↓
create_all()
```

---

# 14. Kita perbaiki Sync Engine

Sekarang bagian paling penting.

API Ahmad Sanusi menyediakan endpoint daftar kitab dan endpoint daftar hadis per kitab dengan pagination. ([Ahmad Sanusi][1])

Kita buat importer yang:

1. mengambil page
2. membaca metadata pagination
3. melakukan validasi
4. melakukan upsert
5. menghitung hash
6. mencatat sync run
7. menghentikan proses dengan aman jika response aneh.

---

# 15. Utility hash

Buat:

```text
backend/app/utils/hash.py
```

```python
import hashlib


def content_hash(
    arabic: str | None,
    translation: str | None,
) -> str:

    raw = (
        f"{arabic or ''}"
        f"||"
        f"{translation or ''}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()
```

---

# 16. Normalizer response

Buat:

```text
backend/app/services/hadith_normalizer.py
```

```python
from app.utils.hash import content_hash


def normalize_hadith(
    item: dict,
) -> dict:

    nomor = item.get("nomor")

    if nomor is None:
        raise ValueError(
            "Hadith tidak memiliki nomor."
        )

    arabic = (
        item.get("arab")
        or item.get("arabic")
        or ""
    )

    translation = (
        item.get("terjemah")
        or item.get("translation")
        or ""
    )

    return {
        "external_number": int(nomor),
        "arabic_text": arabic,
        "translation": translation,
        "content_hash": content_hash(
            arabic,
            translation,
        ),
    }
```

Dengan demikian jika Ahmad Sanusi suatu hari mengubah nama field internal response, kita hanya perlu memperbaiki normalizer.

---

# 17. Sync endpoint detail

Untuk keamanan data, saya menyarankan strategi:

```text
LIST endpoint
      ↓
ambil daftar nomor
      ↓
DETAIL endpoint
      ↓
ambil data lengkap
      ↓
DATABASE
```

Mengapa?

Karena endpoint detail secara eksplisit didokumentasikan menyediakan:

```text
nomor
kitab
arab
terjemah
has_terjemah
```

sedangkan endpoint daftar adalah endpoint paginasi. ([Ahmad Sanusi][1])

Jadi untuk **initial authoritative import**, kita gunakan:

```text
/v1/hadits/shahih_bukhari/{nomor}
```

sebagai payload final.

---

# 18. Importer tahap awal

```python
# backend/scripts/sync_bukhari.py

import asyncio

from datetime import datetime, timezone

from app.database import SessionLocal

from app.models import (
    Source,
    Collection,
    Hadith,
    SyncRun,
)

from app.services.ahmad_sanusi import (
    AhmadSanusiClient,
)

from app.services.hadith_normalizer import (
    normalize_hadith,
)


KITAB = "shahih_bukhari"

START = 1
END = 10


async def sync():

    db = SessionLocal()

    run = SyncRun(
        collection_slug=KITAB,
        status="running",
        started_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(run)
    db.commit()

    try:

        source = (
            db.query(Source)
            .filter(
                Source.name ==
                "Ahmad Sanusi Hadits API"
            )
            .first()
        )

        collection = (
            db.query(Collection)
            .filter(
                Collection.slug == KITAB
            )
            .first()
        )

        if not source:
            raise RuntimeError(
                "Source tidak ditemukan."
            )

        if not collection:
            raise RuntimeError(
                "Collection tidak ditemukan."
            )

        client = AhmadSanusiClient()

        for nomor in range(
            START,
            END + 1,
        ):

            print(
                f"Fetching "
                f"{KITAB} #{nomor}"
            )

            response = await client.get_hadith(
                KITAB,
                nomor,
            )

            data = response.get(
                "data"
            )

            if not data:
                raise RuntimeError(
                    f"Response kosong "
                    f"untuk #{nomor}"
                )

            normalized = normalize_hadith(
                data
            )

            run.fetched += 1

            existing = (
                db.query(Hadith)
                .filter(
                    Hadith.collection_id ==
                    collection.id,

                    Hadith.external_number ==
                    nomor,
                )
                .first()
            )

            if existing:

                if (
                    existing.content_hash
                    != normalized[
                        "content_hash"
                    ]
                ):

                    existing.arabic_text = (
                        normalized[
                            "arabic_text"
                        ]
                    )

                    existing.translation = (
                        normalized[
                            "translation"
                        ]
                    )

                    existing.content_hash = (
                        normalized[
                            "content_hash"
                        ]
                    )

                    run.updated += 1

                continue

            hadith = Hadith(
                collection_id=collection.id,
                source_id=source.id,
                external_number=nomor,
                arabic_text=normalized[
                    "arabic_text"
                ],
                translation=normalized[
                    "translation"
                ],
                content_hash=normalized[
                    "content_hash"
                ],
                api_endpoint=(
                    f"/v1/hadits/"
                    f"{KITAB}/{nomor}"
                ),
                retrieved_at=datetime.now(
                    timezone.utc
                ),
            )

            db.add(hadith)

            run.inserted += 1

            db.commit()

        run.status = "completed"

    except Exception as exc:

        db.rollback()

        run.status = "failed"

        run.error_message = str(exc)

        db.commit()

        raise

    finally:

        run.finished_at = datetime.now(
            timezone.utc
        )

        db.commit()

        db.close()


if __name__ == "__main__":

    asyncio.run(sync())
```

---

# 19. Mengapa kita mulai 10 hadis?

Jangan langsung:

```text
1 → 7008
```

Kita lakukan:

```text
1 → 10
```

kemudian:

```text
1 → 100
```

kemudian:

```text
1 → 1000
```

kemudian:

```text
1 → 7008
```

Ini memungkinkan kita mendeteksi:

* response berubah
* rate limit
* nomor tidak berurutan
* hadis kosong
* encoding Arab bermasalah
* duplicate
* error API
* timeout

sebelum database penuh.

---

# 20. Jalankan import

```bash
docker exec -it fathul_bari_backend \
python scripts/sync_bukhari.py
```

Target output:

```text
Fetching shahih_bukhari #1
Fetching shahih_bukhari #2
Fetching shahih_bukhari #3
...
Fetching shahih_bukhari #10
```

Kemudian periksa database:

```sql
SELECT
    external_number,
    length(arabic_text),
    length(translation)
FROM hadiths
ORDER BY external_number;
```

Target:

```text
1
2
3
...
10
```

---

# 21. Validasi jumlah hadis

Buat script:

```text
backend/scripts/validate_bukhari.py
```

```python
from app.database import SessionLocal
from app.models import Hadith, Collection


EXPECTED = 7008


db = SessionLocal()

try:

    collection = (
        db.query(Collection)
        .filter(
            Collection.slug ==
            "shahih_bukhari"
        )
        .first()
    )

    count = (
        db.query(Hadith)
        .filter(
            Hadith.collection_id ==
            collection.id
        )
        .count()
    )

    print(
        f"Database : {count}"
    )

    print(
        f"Expected : {EXPECTED}"
    )

    if count == EXPECTED:

        print(
            "PASS: jumlah hadis sesuai."
        )

    else:

        print(
            "WARNING: jumlah belum sesuai."
        )

finally:

    db.close()
```

---

# 22. Validasi nomor yang hilang

Ini lebih penting daripada sekadar count.

```python
numbers = {
    row.external_number
    for row in (
        db.query(Hadith)
        .filter(
            Hadith.collection_id ==
            collection.id
        )
        .all()
    )
}

missing = [
    number
    for number in range(
        1,
        EXPECTED + 1
    )
    if number not in numbers
]

print("Missing:", missing)
```

Target:

```text
Missing: []
```

---

# 23. Validasi duplicate

Karena kita sudah membuat:

```sql
UNIQUE (
    collection_id,
    external_number
)
```

database sendiri akan membantu menjaga integritas.

Query:

```sql
SELECT
    collection_id,
    external_number,
    COUNT(*)
FROM hadiths
GROUP BY
    collection_id,
    external_number
HAVING COUNT(*) > 1;
```

Target:

```text
0 rows
```

---

# 24. Validasi hadis kosong

```sql
SELECT external_number
FROM hadiths
WHERE
    arabic_text IS NULL
    OR trim(arabic_text) = ''
    OR translation IS NULL
    OR trim(translation) = '';
```

Hasil ini akan masuk:

```text
DATA QUALITY REVIEW
```

bukan langsung dianggap valid.

---

# 25. Dashboard kualitas data

Kita nantinya bisa membuat endpoint:

```text
GET /api/v1/admin/data-quality
```

Response:

```json
{
  "collection": "shahih_bukhari",
  "expected": 7008,
  "actual": 7008,
  "missing": 0,
  "duplicate": 0,
  "missing_arabic": 0,
  "missing_translation": 0,
  "status": "healthy"
}
```

Ini akan sangat berguna ketika aplikasi sudah besar.

---

# 26. Endpoint internal yang lebih baik

Sekarang endpoint:

```text
GET
/api/v1/hadith/shahih_bukhari/1
```

tidak perlu lagi memanggil Ahmad Sanusi secara live.

Alurnya:

```text
Browser
   ↓
FastAPI
   ↓
PostgreSQL
   ↓
Hadith
```

Bukan:

```text
Browser
   ↓
FastAPI
   ↓
Ahmad Sanusi
```

Dengan demikian aplikasi tetap bisa membaca hadis meskipun API eksternal sedang mengalami gangguan.

---

# 27. Repository layer

Buat:

```text
backend/app/repositories/hadith.py
```

```python
from sqlalchemy.orm import Session

from app.models import Hadith, Collection


def get_hadith(
    db: Session,
    kitab: str,
    nomor: int,
):

    collection = (
        db.query(Collection)
        .filter(
            Collection.slug == kitab
        )
        .first()
    )

    if not collection:
        return None

    return (
        db.query(Hadith)
        .filter(
            Hadith.collection_id ==
            collection.id,

            Hadith.external_number ==
            nomor,
        )
        .first()
    )
```

---

# 28. API membaca database

Sekarang `api/hadith.py`:

```python
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.repositories.hadith import (
    get_hadith,
)


router = APIRouter(
    prefix="/api/v1/hadith",
    tags=["Hadith"],
)


@router.get(
    "/{kitab}/{nomor}"
)
def read_hadith(
    kitab: str,
    nomor: int,
    db: Session = Depends(get_db),
):

    hadith = get_hadith(
        db,
        kitab,
        nomor,
    )

    if not hadith:

        raise HTTPException(
            status_code=404,
            detail="Hadith tidak ditemukan.",
        )

    return {
        "id": str(hadith.id),
        "kitab": kitab,
        "nomor": hadith.external_number,
        "arab": hadith.arabic_text,
        "terjemah": hadith.translation,
        "source": {
            "name":
                "Ahmad Sanusi Hadits API",
            "endpoint":
                hadith.api_endpoint,
        },
    }
```

---

# 29. Sekarang kita sudah punya dua layer

```text
                    APPLICATION
                         │
                         ▼
                   FastAPI API
                         │
                         ▼
                   PostgreSQL
                         │
                         ▼
                    Hadith DB
                         ▲
                         │
                  Sync Worker
                         │
                         ▼
                Ahmad Sanusi API
```

Ini jauh lebih aman daripada aplikasi yang bergantung pada API eksternal setiap kali pengguna membaca hadis.

---

# 30. Setelah 10 hadis berhasil

Ubah:

```python
START = 1
END = 10
```

menjadi:

```python
START = 1
END = 100
```

Tes.

Kemudian:

```python
END = 1000
```

Tes.

Terakhir:

```python
END = 7008
```

Tetapi **sebelum menjalankan 7.008 request**, kita perlu mengukur rate limit akun/API Anda. Dokumentasi menyatakan API menggunakan API-key authentication dan rate limiting per tier. ([Ahmad Sanusi Open API][2])

Jadi jangan melakukan 7.008 request paralel.

Gunakan:

```text
1 request
 ↓
response
 ↓
delay kecil
 ↓
request berikutnya
```

dan kemudian kita tambahkan retry/backoff.

---

# 31. Retry mechanism

Tahap berikutnya sebaiknya menggunakan:

```text
429 Too Many Requests
        ↓
wait
        ↓
retry

500
        ↓
exponential backoff
        ↓
retry
```

Contoh konsep:

```text
retry 1 → 1 detik
retry 2 → 2 detik
retry 3 → 4 detik
retry 4 → 8 detik
```

Jangan retry tanpa batas.

---

# 32. Setelah Bukhari selesai

Database akan menjadi:

```text
sources
│
└── Ahmad Sanusi Hadits API

collections
│
└── Shahih al-Bukhari
      │
      ├── #1
      ├── #2
      ├── #3
      ├── ...
      └── #7008
```

Dan masing-masing hadis memiliki:

```text
UUID
nomor asli
Arab
terjemahan
source
endpoint
hash
retrieved_at
```

---

# 33. Baru kemudian kita masuk Fathul Bari

Ini milestone penting:

```text
                 MILESTONE 1
                      │
                      ▼
             Ahmad Sanusi API
                      │
                      ▼
              7.008 Bukhari
                      │
                      ▼
              PostgreSQL
                      │
                      ▼
              DATA VALIDATED
                      │
                      ▼
                 MILESTONE 2
                      │
                      ▼
               Fathul Bari
```

Untuk Fathul Bari, kita **jangan mengandalkan OCR mentah langsung menjadi syarah**. Kita akan membuat pipeline khusus:

```text
PDF
 ↓
Extract text
 ↓
OCR jika diperlukan
 ↓
Arabic normalization
 ↓
Page segmentation
 ↓
Volume/chapter detection
 ↓
Hadith reference detection
 ↓
Matching dengan Bukhari
 ↓
Human verification
```

---

## Milestone yang saya rekomendasikan sekarang

**Jangan lanjut ke frontend dulu.** Selesaikan milestone berikut:

```text
[✓] Docker PostgreSQL
[✓] FastAPI
[✓] Ahmad Sanusi Client
[✓] Alembic
[✓] Schema
[✓] Source
[✓] Collection
[✓] Hadith
[✓] Sync Run
[ ] Import 10 hadis
[ ] Validasi 10 hadis
[ ] Import 100 hadis
[ ] Retry/backoff
[ ] Import 7.008 hadis
[ ] Data-quality report
```

Setelah itu kita masuk ke **Tahap 3: mesin ekstraksi dan pemetaan Fathul Bari → hadis Bukhari**. Tahap tersebut akan menjadi bagian paling penting dari aplikasi, karena kita perlu membuat **Hadith–Sharh Linking Engine** yang mampu menangani hadis yang muncul berulang di berbagai bab serta memastikan syarah benar-benar terkait dengan hadis yang tepat.

[1]: https://ahmadsanusi.com/islami/hadits?utm_source=chatgpt.com "API Hadits Indonesia — 60.000+ Hadits Shahih dari 10 Kitab | Ahmad Sanusi Open API"
[2]: https://api.ahmadsanusi.com/?utm_source=chatgpt.com "Ahmad Sanusi Open API — Data Islami untuk Developers"
