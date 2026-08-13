# Stage 19 — Ahmad Sanusi Hadits API + Hadith Data Layer

Kita lanjut dari Stage 18. Fokus tahap ini adalah membangun **data layer hadis** sehingga aplikasi sudah memiliki sumber hadis eksternal yang terstruktur, tersimpan lokal, dapat dicari, dan siap dihubungkan ke corpus *Fathul Bari*.

> Prinsip utama: **Ahmad Sanusi API menjadi source provider, PostgreSQL menjadi local research index.** Kita tidak menjadikan LLM sebagai sumber teks hadis.

---

## 19.1 Arsitektur Stage 19

```text
                    Ahmad Sanusi Hadits API
                              │
                              ▼
                   ┌────────────────────┐
                   │ AhmadSanusiClient  │
                   └─────────┬──────────┘
                             │
                   validation + normalize
                             │
                             ▼
                    ┌────────────────┐
                    │ Ingestion      │
                    │ Service        │
                    └───────┬────────┘
                            │
                  ┌─────────┴──────────┐
                  ▼                    ▼
              PostgreSQL             Redis
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
     Hadith    Variant    Reference
        │
        ▼
   Search Index
        │
        ▼
 Fathul Bari Matcher
```

---

# 19.2 Database Schema

Kita mulai dengan schema berikut:

```text
sources
   │
   ├── collections
   │       │
   │       └── books
   │               │
   │               └── hadiths
   │                       │
   │                       ├── hadith_variants
   │                       │
   │                       └── hadith_references
   │
   └── source_files
```

---

# 19.3 `sources`

Menyimpan asal data.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    base_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Contoh:

```json
{
  "name": "Ahmad Sanusi Hadits API",
  "provider": "ahmad_sanusi",
  "source_type": "API"
}
```

---

# 19.4 `collections`

Misalnya:

```text
Sahih al-Bukhari
Sahih Muslim
Sunan Abu Dawud
Jami' at-Tirmidhi
Sunan an-Nasa'i
Sunan Ibn Majah
```

Schema:

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES sources(id),
    slug VARCHAR(100) NOT NULL,
    name_ar TEXT,
    name_id TEXT,
    name_en TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(source_id, slug)
);
```

---

# 19.5 `books`

Karena satu collection dapat mempunyai struktur kitab/bab:

```sql
CREATE TABLE books (
    id UUID PRIMARY KEY,
    collection_id UUID NOT NULL REFERENCES collections(id),
    external_id VARCHAR(255),
    number INTEGER,
    name_ar TEXT,
    name_id TEXT,
    name_en TEXT,
    metadata JSONB DEFAULT '{}',

    UNIQUE(collection_id, external_id)
);
```

---

# 19.6 `hadiths`

Ini tabel inti.

```sql
CREATE TABLE hadiths (
    id UUID PRIMARY KEY,

    book_id UUID REFERENCES books(id),

    external_id VARCHAR(255) NOT NULL,

    hadith_number VARCHAR(100),

    arabic_text TEXT NOT NULL,
    normalized_text TEXT,
    search_text TEXT,

    narrator_text TEXT,

    grade VARCHAR(100),

    metadata JSONB DEFAULT '{}',

    source_url TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(external_id)
);
```

---

# 19.7 Kenapa `external_id` sangat penting?

Jangan mengandalkan:

```text
id = 123
```

karena ID tersebut adalah ID database kita.

Gunakan:

```text
external_id
```

misalnya:

```text
ahmad-sanusi:bukhari:1
```

atau sesuai identifier asli API.

Dengan demikian:

```text
Ahmad Sanusi
      │
      ▼
external_id
      │
      ▼
Local database UUID
```

---

# 19.8 Hadith Variant

Hadis yang sama bisa mempunyai variasi lafaz.

Contoh:

```text
Hadith A
 ├── riwayah variant 1
 ├── riwayah variant 2
 └── riwayah variant 3
```

Schema:

```sql
CREATE TABLE hadith_variants (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL REFERENCES hadiths(id),

    variant_type VARCHAR(50),

    arabic_text TEXT NOT NULL,
    normalized_text TEXT,

    source_collection TEXT,
    source_reference TEXT,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Ini nantinya sangat berguna untuk matching dengan kutipan Ibnu Hajar.

---

# 19.9 Hadith References

Untuk hubungan silang:

```text
Bukhari 1
   ↓
Muslim 1907
   ↓
Tirmidhi ...
```

Schema:

```sql
CREATE TABLE hadith_references (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL REFERENCES hadiths(id),

    target_collection VARCHAR(255),
    target_hadith_number VARCHAR(100),

    reference_type VARCHAR(50),

    confidence NUMERIC(5,4),

    metadata JSONB DEFAULT '{}",

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

`reference_type` dapat berupa:

```text
EXPLICIT
INFERRED
MANUAL
MODEL_SUGGESTED
```

---

# 19.10 Arabic Normalization

Sebelum hadis masuk search index:

```text
Arabic Raw
    ↓
Unicode Normalize
    ↓
Remove Tatweel
    ↓
Normalize Alef
    ↓
Normalize Hamzah
    ↓
Normalize Ya
    ↓
Normalize Ta Marbuta
    ↓
Remove diacritics
    ↓
Normalized Arabic
```

Contoh konsep:

```text
إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ
```

menjadi representasi pencarian yang lebih konsisten.

**Namun:** jangan mengganti `arabic_text`.

Simpan dua versi:

```text
arabic_text
normalized_text
```

Original text harus tetap immutable sebagai evidence.

---

# 19.11 Search Text

Buat:

```text
search_text
```

yang dapat menggabungkan:

```text
normalized Arabic
+
hadith number
+
narrator
+
metadata
```

Sehingga pencarian:

```text
إنما الأعمال
```

tetap dapat menemukan hadis walaupun tanda baca/harakat berbeda.

---

# 19.12 Ahmad Sanusi Client

Struktur:

```text
apps/api/app/
└── integrations/
    └── ahmad_sanusi/
        ├── __init__.py
        ├── client.py
        ├── schemas.py
        └── exceptions.py
```

Interface:

```python
class AhmadSanusiClient:

    async def get_collections(self):
        ...

    async def get_books(self, collection):
        ...

    async def get_hadith(self, collection, hadith_id):
        ...

    async def search(self, query):
        ...
```

**Endpoint aktual Ahmad Sanusi API harus kita sesuaikan dengan dokumentasi API yang Anda gunakan**, karena kita tidak boleh menebak path atau response schema API.

---

# 19.13 Adapter Pattern

Jangan membuat seluruh aplikasi tergantung pada Ahmad Sanusi.

Gunakan interface:

```python
class HadithProvider:

    async def get_hadith(self, external_id):
        raise NotImplementedError

    async def list_collections(self):
        raise NotImplementedError

    async def search(self, query):
        raise NotImplementedError
```

Kemudian:

```text
HadithProvider
      │
      ├── AhmadSanusiProvider
      │
      ├── AnotherProvider
      │
      └── LocalCorpusProvider
```

Ini membuat aplikasi kita **provider-agnostic**.

---

# 19.14 DTO / Provider Schema

Response dari API jangan langsung dimasukkan ke SQLAlchemy.

Gunakan DTO:

```python
from pydantic import BaseModel

class HadithDTO(BaseModel):
    external_id: str
    collection: str
    hadith_number: str | None = None
    arabic_text: str
    narrator_text: str | None = None
    grade: str | None = None
    source_url: str | None = None
    metadata: dict = {}
```

Flow:

```text
External JSON
     ↓
Pydantic DTO
     ↓
Validation
     ↓
Normalization
     ↓
Repository
     ↓
PostgreSQL
```

---

# 19.15 Repository

```text
apps/api/app/repositories/
    hadith_repository.py
    collection_repository.py
    source_repository.py
```

Contoh interface:

```python
class HadithRepository:

    async def get_by_external_id(self, external_id):
        ...

    async def upsert(self, hadith):
        ...

    async def search(self, query, limit=20):
        ...
```

---

# 19.16 Upsert

Ingestion harus idempotent.

```text
Fetch
 ↓
external_id
 ↓
Already exists?
 ├── YES → update metadata
 └── NO  → insert
```

Jangan menghasilkan:

```text
Bukhari 1
Bukhari 1
Bukhari 1
Bukhari 1
```

setiap kali ingestion dijalankan.

---

# 19.17 Ingestion Service

```text
apps/api/app/services/
    hadith_ingestion.py
```

Flow:

```python
async def ingest_hadith(external_id):

    raw = await provider.get_hadith(external_id)

    dto = validate(raw)

    normalized = normalize_hadith(dto)

    existing = await repository.get_by_external_id(
        normalized.external_id
    )

    if existing:
        return await repository.update(existing, normalized)

    return await repository.create(normalized)
```

---

# 19.18 Batch Ingestion

Untuk seluruh collection:

```text
Collection
   ↓
Books
   ↓
Hadith IDs
   ↓
Queue
   ↓
Worker
   ↓
Hadith
```

Jangan:

```text
HTTP request
 ↓
10.000 hadis
 ↓
wait...
```

Gunakan asynchronous job.

---

# 19.19 Job Model

Tambahkan:

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY,

    provider VARCHAR(100) NOT NULL,
    collection VARCHAR(255),

    status VARCHAR(30) NOT NULL,

    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,

    error_message TEXT,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 19.20 Job Progress

Frontend dapat menampilkan:

```text
Ahmad Sanusi Import

████████████████░░░░ 82%

Processed : 8,214
Failed    : 17
Remaining : 1,769
```

---

# 19.21 Retry Strategy

Jika API gagal:

```text
attempt 1
   ↓
2 sec
   ↓
attempt 2
   ↓
5 sec
   ↓
attempt 3
   ↓
15 sec
```

Setelah batas retry:

```text
FAILED
```

Tetapi error tetap disimpan untuk audit.

---

# 19.22 Rate Limit Provider

Client harus mempunyai:

```text
timeout
retry
backoff
rate limit
circuit breaker
```

Secara khusus:

```text
Ahmad Sanusi API
       │
       ▼
Our Adapter
       │
       ├── timeout
       ├── retry
       ├── cache
       └── rate limiter
```

---

# 19.23 Cache

Gunakan Redis:

```text
hadith:provider:ahmad-sanusi:{external_id}
```

TTL dapat disesuaikan.

Tetapi untuk research corpus, setelah data diimpor ke PostgreSQL:

> PostgreSQL menjadi **local canonical research snapshot**.

Dengan demikian penelitian tidak bergantung pada availability API eksternal setiap kali user melakukan query.

---

# 19.24 Data Provenance

Setiap hadis harus memiliki:

```json
{
  "provider": "ahmad_sanusi",
  "external_id": "...",
  "retrieved_at": "...",
  "source_url": "...",
  "content_hash": "sha256..."
}
```

`content_hash` berguna untuk mendeteksi perubahan teks.

---

# 19.25 Content Hash

Konsep:

```python
import hashlib

def content_hash(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()
```

Jika API suatu hari mengubah teks hadis:

```text
old hash
    ≠
new hash
```

kita dapat mendeteksi perubahan.

---

# 19.26 Versioning Hadis

Jangan langsung overwrite evidence lama.

Idealnya:

```text
Hadith
 ├── Version 1
 ├── Version 2
 └── Version 3
```

Untuk MVP Stage 19, kita dapat menyimpan:

```text
content_hash
updated_at
metadata
```

Kemudian Stage berikutnya dapat menambahkan full version history.

---

# 19.27 Search API

Setelah data masuk:

```http
GET /api/v1/hadith/search?q=...
```

Response:

```json
{
  "query": "إنما الأعمال",
  "total": 1,
  "results": [
    {
      "id": "...",
      "collection": "bukhari",
      "hadith_number": "1",
      "arabic_text": "...",
      "score": 0.98
    }
  ]
}
```

---

# 19.28 Endpoint Detail

```http
GET /api/v1/hadith/{id}
```

Response:

```json
{
  "id": "...",
  "external_id": "ahmad-sanusi:bukhari:1",
  "collection": {
    "slug": "bukhari",
    "name_ar": "صحيح البخاري"
  },
  "hadith_number": "1",
  "arabic_text": "...",
  "normalized_text": "...",
  "source": {
    "provider": "ahmad_sanusi",
    "source_url": "..."
  }
}
```

---

# 19.29 Jangan Menampilkan "Sahih" Secara Otomatis

Field:

```text
grade
```

harus dianggap sebagai **metadata sumber**, bukan keputusan AI.

UI sebaiknya:

```text
Derajat:
[Sumber menyediakan: Sahih]
```

bukan:

```text
AI menyatakan hadis ini sahih
```

Untuk aplikasi penelitian hadis, perbedaan ini sangat penting.

---

# 19.30 Hubungan dengan Fathul Bari

Setelah hadis tersedia:

```text
Hadith Bukhari #1
       │
       ▼
Matching Engine
       │
       ▼
Fathul Bari chunk
       │
       ▼
Evidence
```

Contoh:

```text
Hadith
صحيح البخاري رقم 1

       │
       │ exact/semantic match
       ▼

Fath al-Bari
Volume 1
Page XX
```

Tetapi **matching belum kita aktifkan di Stage 19**.

---

# 19.31 Acceptance Criteria

Stage 19 dianggap selesai jika:

```text
[ ] source table tersedia
[ ] collection table tersedia
[ ] books table tersedia
[ ] hadith table tersedia
[ ] hadith variants tersedia
[ ] provider interface tersedia
[ ] Ahmad Sanusi adapter tersedia
[ ] DTO validation tersedia
[ ] Arabic normalization tersedia
[ ] upsert tersedia
[ ] content hash tersedia
[ ] ingestion job tersedia
[ ] retry tersedia
[ ] Redis cache tersedia
[ ] search endpoint tersedia
[ ] detail endpoint tersedia
[ ] provenance tersedia
[ ] tests tersedia
```

---

# 19.32 Struktur Code setelah Stage 19

```text
apps/api/app/
│
├── main.py
│
├── core/
│   ├── config.py
│   └── database.py
│
├── integrations/
│   └── ahmad_sanusi/
│       ├── client.py
│       ├── schemas.py
│       └── exceptions.py
│
├── models/
│   ├── source.py
│   ├── collection.py
│   ├── book.py
│   ├── hadith.py
│   ├── hadith_variant.py
│   └── hadith_reference.py
│
├── repositories/
│   ├── source_repository.py
│   ├── collection_repository.py
│   └── hadith_repository.py
│
├── services/
│   ├── hadith_ingestion.py
│   └── arabic_normalizer.py
│
├── workers/
│   └── ingestion_worker.py
│
├── api/
│   └── v1/
│       ├── hadith.py
│       └── ingestion.py
│
└── tests/
    ├── test_hadith.py
    ├── test_normalizer.py
    └── test_ingestion.py
```

---

# 19.33 Target Akhir Stage 19

Kita ingin mencapai kondisi:

```text
$ curl /api/v1/hadith/search?q=إنما الأعمال

                    ↓

              PostgreSQL
                    ↓

┌────────────────────────────────────┐
│ صحيح البخاري                       │
│ حديث رقم 1                         │
│                                    │
│ إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ │
│                                    │
│ Source: Ahmad Sanusi API           │
│ Hash: ...                          │
└────────────────────────────────────┘
```
