# BLUEPRINT APLIKASI FATHUL BARI

## Terintegrasi Ahmad Sanusi Hadits API

**Versi:** 2.0
**Tanggal:** 11 Agustus 2026
**Arsitektur:** API + Local Database + Search + Fathul Bari + RAG
**Primary Hadith API:** Ahmad Sanusi Hadits API
**Primary Sharh Layer:** Fathul Bari

---

# 1. KONSEP UTAMA

Aplikasi tidak mengambil seluruh data hadis langsung dari browser.

Gunakan arsitektur:

```text
                    USER
                      │
                      ▼
               ┌─────────────┐
               │  FRONTEND   │
               │   Next.js   │
               └──────┬──────┘
                      │
                      ▼
               ┌─────────────┐
               │  BACKEND    │
               │   FastAPI   │
               └──────┬──────┘
                      │
             ┌────────┴─────────┐
             ▼                  ▼
      LOCAL DATABASE       AHMED SANUSI API
             │                  │
             │                  ▼
             │             Hadith Data
             │
             ▼
        FATHUL BARI
             │
             ▼
       SEARCH / RAG / AI
```

**Prinsip penting:**

> Ahmad Sanusi API = sumber hadis dan terjemahan.

> Database lokal = cache, indexing, cross-reference, dan fondasi aplikasi.

> Fathul Bari = database syarah.

> AI = lapisan interpretasi/pencarian, bukan sumber primer.

---

# 2. PERAN AHMAD SANUSI API

Ahmad Sanusi API memiliki endpoint hadis berikut:

```text
GET /v1/hadits
GET /v1/hadits/search?q=
GET /v1/hadits/{kitab}
GET /v1/hadits/{kitab}/{nomor}
GET /v1/hadits/daily
```

API menyediakan teks Arab dan terjemahan Bahasa Indonesia untuk koleksi utama seperti Bukhari, Muslim, Abu Dawud, Tirmidzi, Nasa'i, Ibnu Majah, Musnad Ahmad, Musnad Syafi'i, dan Riyadhus Shalihin.

---

# 3. JANGAN CONNECT FRONTEND LANGSUNG KE API

Hindari:

```text
Browser
   │
   └──────► Ahmad Sanusi API
```

Gunakan:

```text
Browser
   │
   ▼
Your Backend
   │
   ├────► Local PostgreSQL
   │
   └────► Ahmad Sanusi API
```

Alasannya:

1. API Key tidak terekspos.
2. Bisa melakukan caching.
3. Bisa membuat pencarian sendiri.
4. Bisa menggabungkan hadis dengan Fathul Bari.
5. Bisa mengontrol rate limit.
6. Bisa melakukan audit data.
7. Tidak bergantung pada API untuk setiap page view.

---

# 4. API KEY

Ahmad Sanusi menggunakan:

```http
X-API-Key: YOUR_API_KEY
```

dan dokumentasinya menyatakan API key diperoleh setelah registrasi akun.

Simpan di server:

```env
AHMAD_SANUSI_API_KEY=xxxxxxxx
AHMAD_SANUSI_BASE_URL=https://api.ahmadsanusi.com
```

**Jangan pernah memasukkan API key ke JavaScript frontend.**

---

# 5. SERVICE LAYER

Buat service khusus:

```text
backend/
└── services/
    └── ahmad_sanusi/
        ├── client.py
        ├── hadith.py
        ├── search.py
        ├── collections.py
        └── exceptions.py
```

Tujuannya supaya seluruh aplikasi tidak bergantung langsung pada implementasi API.

---

# 6. AHMAD SANUSI API CLIENT

Contoh Python:

```python
import httpx

class AhmadSanusiClient:

    BASE_URL = "https://api.ahmadsanusi.com"

    def __init__(self, api_key):
        self.api_key = api_key

    def _headers(self):
        return {
            "X-API-Key": self.api_key
        }

    async def get_hadith(self, kitab, nomor):
        url = f"{self.BASE_URL}/v1/hadits/{kitab}/{nomor}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._headers(),
                timeout=15
            )

        response.raise_for_status()

        return response.json()
```

---

# 7. CONTOH PEMANGGILAN

Untuk Shahih Bukhari nomor 1:

```http
GET /v1/hadits/shahih_bukhari/1
```

Header:

```http
X-API-Key: YOUR_API_KEY
```

Response menyediakan:

```json
{
  "status": "success",
  "data": {
    "nomor": 1,
    "kitab": "shahih_bukhari",
    "arab": "...",
    "terjemah": "...",
    "has_terjemah": true
  }
}
```

Format tersebut tercantum pada dokumentasi API.

---

# 8. LOCAL DATABASE

Walaupun Ahmad Sanusi API dapat menyediakan data secara live, aplikasi tetap sebaiknya mempunyai:

```text
PostgreSQL
```

Struktur:

```text
hadith_db
│
├── sources
├── collections
├── books
├── chapters
├── hadiths
├── hadith_translations
├── hadith_references
├── hadith_sources
├── sharh
├── sharh_sections
├── narrators
├── sanad
├── sanad_narrators
├── scholars
├── topics
└── embeddings
```

---

# 9. TABEL HADITH

```sql
CREATE TABLE hadiths (
    id UUID PRIMARY KEY,
    collection_id UUID NOT NULL,
    external_number VARCHAR(50) NOT NULL,
    arabic_text TEXT,
    normalized_arabic TEXT,
    search_text TEXT,
    source_status VARCHAR(30),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

# 10. TABEL TERJEMAHAN

Jangan memasukkan terjemahan langsung ke tabel hadis.

Gunakan:

```sql
CREATE TABLE hadith_translations (
    id UUID PRIMARY KEY,
    hadith_id UUID NOT NULL,
    language VARCHAR(10) NOT NULL,
    translation TEXT NOT NULL,
    source_id UUID,
    created_at TIMESTAMP
);
```

Contoh:

```text
hadith_id
   │
   ├── id → Indonesian
   ├── en → English
   └── ar → Original
```

---

# 11. TABEL SOURCE

Ini sangat penting.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    source_type VARCHAR(50),
    base_url TEXT,
    license TEXT,
    retrieved_at TIMESTAMP,
    version VARCHAR(100)
);
```

Contoh:

```text
source_id
   │
   └── Ahmad Sanusi Hadits API
```

Dengan demikian setiap hadis mempunyai provenance.

---

# 12. PROVENANCE

Contoh:

```json
{
  "source": "Ahmad Sanusi Hadits API",
  "endpoint": "/v1/hadits/shahih_bukhari/1",
  "retrieved_at": "2026-08-11T10:00:00+07:00"
}
```

Jangan hanya menyimpan:

```text
source = Ahmad Sanusi
```

Simpan juga:

```text
endpoint
timestamp
API response hash
dataset version
```

---

# 13. SYNC ENGINE

Buat proses:

```text
AHMAD SANUSI API
       │
       ▼
    FETCH
       │
       ▼
    VALIDATE
       │
       ▼
   NORMALIZE
       │
       ▼
     HASH
       │
       ▼
   UPSERT
       │
       ▼
 POSTGRESQL
```

---

# 14. MODE SYNC

Gunakan dua mode.

## Mode A — Initial Sync

Mengambil seluruh koleksi:

```text
Bukhari
Muslim
Abu Dawud
Tirmidzi
Nasa'i
Ibnu Majah
Musnad Ahmad
Musnad Syafi'i
Riyadhus Shalihin
```

Data statistik API saat ini mencantumkan 60.229 hadis dari 10 kitab.

---

## Mode B — Incremental Sync

Hanya mengambil:

```text
new
changed
missing
```

Contoh:

```text
cron:
setiap malam 02:00
```

---

# 15. JANGAN MEMANGGIL API UNTUK SETIAP HADIS

Salah:

```text
User buka hadis 1
→ API

User buka hadis 2
→ API

User buka hadis 3
→ API
```

Lebih baik:

```text
Sync
 ↓
Local DB
 ↓
User
 ↓
Local DB
```

API hanya digunakan untuk:

```text
initial import
periodic synchronization
manual verification
```

---

# 16. CACHE

Tambahkan Redis:

```text
User
 │
 ▼
FastAPI
 │
 ▼
Redis
 │
 ├── HIT → return
 │
 └── MISS
       │
       ▼
   PostgreSQL
```

Cache key:

```text
hadith:shahih_bukhari:1
```

Search:

```text
hadith:search:niat
```

---

# 17. INTEGRASI DENGAN FATHUL BARI

Ini inti aplikasi.

```text
Ahmad Sanusi
      │
      ▼
Hadith
      │
      ▼
hadith_id
      │
      ▼
Fathul Bari Link
      │
      ▼
Sharh Section
```

Contoh:

```text
bukhari:1571
       │
       ▼
fath_bari:
volume 4
page XXX
paragraph YYY
```

---

# 18. TABEL HADITH_SHARH

```sql
CREATE TABLE hadith_sharh_links (
    id UUID PRIMARY KEY,
    hadith_id UUID NOT NULL,
    sharh_section_id UUID NOT NULL,
    confidence DECIMAL(5,4),
    link_method VARCHAR(50),
    verified BOOLEAN DEFAULT FALSE
);
```

`link_method`:

```text
manual
number_match
chapter_match
text_match
semantic_match
ocr_reference
```

---

# 19. AUTOMATIC HADITH ↔ FATHUL BARI MATCHING

Pipeline:

```text
Hadith
 │
 ├── nomor
 ├── kitab
 ├── bab
 └── Arabic text
 │
 ▼
Matching Engine
 │
 ├── Number Match
 ├── Chapter Match
 ├── Text Match
 └── Semantic Match
 │
 ▼
Candidate Sharh
 │
 ▼
Confidence Score
 │
 ▼
Human Verification
```

---

# 20. CONFIDENCE SCORE

Contoh:

```text
Hadith number match      = 40%
Chapter match            = 20%
Arabic text similarity   = 25%
Semantic similarity      = 15%
```

Total:

```text
0.97
```

Jika:

```text
confidence >= 0.95
```

bisa:

```text
AUTO VERIFIED
```

Jika:

```text
0.70–0.94
```

masuk:

```text
REVIEW QUEUE
```

Jika:

```text
< 0.70
```

jangan otomatis dipublikasikan.

---

# 21. HALAMAN HADIS

Contoh UI:

```text
┌──────────────────────────────────────────────┐
│ SAHIH AL-BUKHARI                            │
│ Hadis No. 1571                              │
├──────────────────────────────────────────────┤
│                                              │
│ النص العربي                                  │
│                                              │
│ حَدَّثَنَا ...                               │
│                                              │
├──────────────────────────────────────────────┤
│ TERJEMAHAN INDONESIA                         │
│                                              │
│ Telah menceritakan kepada kami...            │
│                                              │
├──────────────────────────────────────────────┤
│ SUMBER                                       │
│ Ahmad Sanusi Hadits API                      │
├──────────────────────────────────────────────┤
│                                              │
│ 📖 BACA SYARAH FATHUL BARI                  │
│                                              │
└──────────────────────────────────────────────┘
```

---

# 22. HALAMAN SYARAH

Saat user menekan:

> Baca Syarah Fathul Bari

aplikasi membuka:

```text
┌──────────────────────────────────────────────┐
│ FATHUL BARI                                 │
│                                              │
│ Kitab: XXXXX                                │
│ Bab: XXXXX                                  │
│                                              │
├──────────────────────────────────────────────┤
│                                              │
│ شرح الحافظ ابن حجر                           │
│                                              │
│ ...                                          │
│                                              │
├──────────────────────────────────────────────┤
│ HADIS YANG DIJELASKAN                       │
│                                              │
│ Shahih Bukhari #1571                        │
│                                              │
└──────────────────────────────────────────────┘
```

---

# 23. SEARCH

Pencarian dapat menggunakan Ahmad Sanusi sebagai sumber awal:

```text
GET /v1/hadits/search?q=niat
```

Tetapi untuk production:

```text
User
 ↓
Local Search
 ↓
PostgreSQL FTS
 ↓
Vector Search
 ↓
Hadith
 ↓
Fathul Bari
```

Endpoint search Ahmad Sanusi memang tersedia untuk pencarian keyword pada terjemahan.

---

# 24. HYBRID SEARCH

Gunakan:

```text
40% keyword
30% semantic
20% metadata
10% popularity/relevance
```

Contoh query:

> "hadis tentang niat"

Sistem mencari:

```text
niat
نية
النية
intention
```

kemudian menghubungkan dengan syarah.

---

# 25. SEARCH RESULT

```text
HASIL PENCARIAN: "NIAT"

┌─────────────────────────────────────┐
│ Bukhari #1                          │
│                                     │
│ إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ │
│                                     │
│ "Sesungguhnya amal itu tergantung   │
│ pada niat..."                       │
│                                     │
│ 📖 Fathul Bari tersedia             │
└─────────────────────────────────────┘
```

---

# 26. FITUR "ADA SYARAH?"

Pada hasil hadis:

```text
✓ Hadis tersedia
✓ Terjemahan tersedia
✓ Fathul Bari tersedia
✓ 3 hadis terkait
✓ 2 referensi ulama
```

Ini menjadi metadata yang sangat berguna.

---

# 27. HADITH DETAIL API INTERNAL

Frontend memanggil:

```http
GET /api/v1/hadith/bukhari/1571
```

Backend mengembalikan:

```json
{
  "id": "uuid",
  "collection": {
    "slug": "shahih_bukhari",
    "name": "Shahih al-Bukhari"
  },
  "number": 1571,
  "arabic": "...",
  "translation": {
    "id": "..."
  },
  "source": {
    "name": "Ahmad Sanusi Hadits API"
  },
  "sharh": {
    "available": true,
    "sections": []
  }
}
```

---

# 28. FATHUL BARI API INTERNAL

```http
GET /api/v1/hadith/bukhari/1571/sharh
```

Response:

```json
{
  "hadith": "bukhari:1571",
  "sharh": [
    {
      "volume": 4,
      "page": 125,
      "paragraph": 3,
      "arabic": "...",
      "verified": true
    }
  ]
}
```

---

# 29. AI ASSISTANT

AI berada setelah database:

```text
Ahmad Sanusi
       │
       ▼
PostgreSQL
       │
       ▼
Fathul Bari
       │
       ▼
Vector Search
       │
       ▼
RAG
       │
       ▼
LLM
```

User:

> "Apa penjelasan Ibnu Hajar mengenai hadis ini?"

AI:

```text
1. Ambil hadis
2. Ambil syarah
3. Ambil hadis terkait
4. Ambil referensi ulama
5. Buat jawaban
6. Validasi citation
```

---

# 30. AI TIDAK BOLEH

```text
❌ Mengarang syarah
❌ Mengarang nomor hadis
❌ Mengarang halaman
❌ Mengarang kutipan Arab
❌ Mengubah status hadis
❌ Menyatakan pendapat AI sebagai pendapat Ibnu Hajar
```

---

# 31. CITATION

Jawaban AI harus:

```text
[Hadis]
Shahih al-Bukhari #1571
Sumber data: Ahmad Sanusi Hadits API

[Syarah]
Fathul Bari
Jilid X, halaman Y
```

Jika halaman belum diverifikasi:

```text
Fathul Bari
Lokasi syarah: belum diverifikasi
```

Jangan mengarang halaman.

---

# 32. DATABASE SOURCE PRIORITY

Untuk aplikasi ini:

```text
                HADITH
                  │
                  ▼
       Ahmad Sanusi API
                  │
                  ▼
          Local Hadith DB
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
   Translation          Cross Reference
        │                   │
        └─────────┬─────────┘
                  ▼
             FATHUL BARI
                  │
                  ▼
          Knowledge Graph
                  │
                  ▼
                 RAG
                  │
                  ▼
                  AI
```

---

# 33. KEUNGGULAN INTEGRASI INI

Ahmad Sanusi memberikan:

```text
✓ Bahasa Indonesia
✓ Teks Arab
✓ Nomor hadis
✓ Koleksi kitab
✓ Search API
✓ REST API
✓ API key
```

Sementara aplikasi Anda menambahkan:

```text
✓ Fathul Bari
✓ Cross-reference
✓ Sanad
✓ Rijal
✓ Search lanjutan
✓ Knowledge graph
✓ RAG
✓ AI research
```

Dengan demikian kita tidak perlu membangun database hadis dari nol.

---

# 34. FITUR TAMBAHAN DARI EKOSISTEM AHMAD SANUSI

Menariknya, Ahmad Sanusi juga menyediakan API Al-Qur'an dengan:

* teks Arab
* transliterasi
* terjemahan Indonesia
* tafsir Wajiz
* tafsir Tahlili
* asbabun nuzul

serta API kitab kuning yang menyediakan metadata dan teks beberapa kitab klasik.

Jadi arsitektur dapat diperluas:

```text
             ISLAMIC KNOWLEDGE PLATFORM
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      HADITH         QURAN          KITAB
        │              │              │
        ▼              ▼              ▼
   Fathul Bari      Tafsir       Classical Books
```

Tetapi **MVP tetap fokus pada Hadis + Fathul Bari**.

---

# 35. ROADMAP BARU

## PHASE 1 — API Integration

```text
[1] Register API
[2] Simpan API Key
[3] Buat API Client
[4] Test endpoint
[5] Test response
```

---

## PHASE 2 — Hadith Database

```text
[1] PostgreSQL
[2] Collections
[3] Hadith
[4] Translation
[5] Source
[6] Provenance
```

---

## PHASE 3 — Sync Engine

```text
Ahmad Sanusi
      ↓
Downloader
      ↓
Normalizer
      ↓
Validator
      ↓
PostgreSQL
```

---

## PHASE 4 — Fathul Bari

```text
PDF
 ↓
OCR
 ↓
Normalization
 ↓
Segmentation
 ↓
Hadith detection
 ↓
Hadith linking
 ↓
Verification
```

---

## PHASE 5 — User Interface

```text
Home
Hadith
Books
Chapters
Hadith Detail
Fathul Bari
Search
```

---

## PHASE 6 — Advanced Search

```text
Keyword
Arabic
Translation
Narrator
Book
Chapter
Semantic
```

---

## PHASE 7 — Knowledge Graph

```text
Hadith
Narrator
Sanad
Scholar
Sharh
Quran
Topic
```

---

## PHASE 8 — AI

```text
Embedding
 ↓
Vector Search
 ↓
Reranker
 ↓
RAG
 ↓
LLM
 ↓
Citation Validator
```

---

# 36. MVP YANG SAYA SARANKAN

Jangan langsung membangun 60.000 hadis.

Mulai dengan:

```text
             MVP
              │
              ▼
      ┌───────────────┐
      │ SHAHIH BUKHARI│
      └───────┬───────┘
              │
              ▼
        HADITH API
              │
              ▼
        LOCAL DATABASE
              │
              ▼
        FATHUL BARI
              │
              ▼
           SEARCH
```

Target MVP:

```text
✓ 1 koleksi
✓ Hadis
✓ Arab
✓ Indonesia
✓ Search
✓ Fathul Bari
✓ Hadis ↔ Syarah
✓ Citation
```

Setelah stabil:

```text
Bukhari
 ↓
Muslim
 ↓
Kutub al-Sittah
 ↓
Musnad Ahmad
 ↓
Knowledge Graph
 ↓
AI
```

---

# 37. ARSITEKTUR TEKNOLOGI FINAL

```text
FRONTEND
Next.js
TypeScript
Tailwind
        │
        ▼
BACKEND
FastAPI
        │
 ┌──────┼─────────┐
 ▼      ▼         ▼
Postgres Redis   Worker
+pgvector
        │
        ▼
DATA LAYER
        │
 ┌──────┼─────────────┐
 ▼                    ▼
Ahmad Sanusi       Fathul Bari
Hadith API         OCR/PDF
        │                    │
        └────────┬───────────┘
                 ▼
         KNOWLEDGE GRAPH
                 │
                 ▼
              RAG
                 │
                 ▼
               LLM
                 │
                 ▼
        CITATION VALIDATOR
```

---

# 38. STRUKTUR PROJECT

```text
fathul-bari/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── ahmad_sanusi/
│   │   ├── ingestion/
│   │   ├── search/
│   │   ├── rag/
│   │   └── validation/
│   │
│   ├── migrations/
│   └── tests/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   └── lib/
│
├── data/
│   ├── raw/
│   ├── normalized/
│   ├── verified/
│   └── exports/
│
├── scripts/
│   ├── sync_hadith.py
│   ├── normalize_arabic.py
│   ├── match_sharh.py
│   └── validate_data.py
│
├── docker-compose.yml
└── README.md
```

---

# 39. LANGKAH IMPLEMENTASI PERTAMA

Urutan praktis:

```text
STEP 1
Buat akun Ahmad Sanusi

        ↓

STEP 2
Dapatkan API Key

        ↓

STEP 3
Buat FastAPI project

        ↓

STEP 4
Implementasi AhmadSanusiClient

        ↓

STEP 5
Test:
GET /v1/hadits/shahih_bukhari/1

        ↓

STEP 6
Buat PostgreSQL

        ↓

STEP 7
Import seluruh Shahih Bukhari

        ↓

STEP 8
Buat Hadith Reader

        ↓

STEP 9
Masukkan Fathul Bari

        ↓

STEP 10
Hubungkan Hadis ↔ Syarah

        ↓

STEP 11
Search

        ↓

STEP 12
RAG / AI
```

---

# 40. KEPUTUSAN ARSITEKTUR

### Sumber hadis

**Ahmad Sanusi Hadits API**

### Database

**PostgreSQL**

### Backend

**FastAPI**

### Frontend

**Next.js + TypeScript**

### Cache

**Redis**

### Vector Search

**pgvector**

### OCR

**Arabic OCR + Human Verification**

### Search

**PostgreSQL FTS → OpenSearch jika diperlukan**

### AI

**RAG + Citation Validator**

### Storage

**S3-compatible Object Storage**

---

# 41. HASIL AKHIR

Aplikasi akan memiliki alur:

```text
USER
 │
 ▼
"Hadis tentang niat"
 │
 ▼
SEARCH
 │
 ▼
AHMAD SANUSI DATA
 │
 ▼
SHAHIH BUKHARI #1
 │
 ├── Arabic
 ├── Indonesia
 ├── Source
 ├── Sanad
 │
 ▼
FATHUL BARI
 │
 ├── Syarah
 ├── Hadis pendukung
 ├── Ulama
 ├── Ayat
 │
 ▼
RELATED HADITH
 │
 ▼
AI RESEARCH
 │
 ▼
ANSWER
 │
 ▼
VERIFIED CITATIONS
```

---

# 42. PRINSIP AKHIR

> **Ahmad Sanusi API menyediakan "data hadis".**

> **Database lokal menyediakan "struktur dan kontrol".**

> **Fathul Bari menyediakan "syarah".**

> **Knowledge Graph menyediakan "hubungan".**

> **RAG menyediakan "pencarian pemahaman".**

> **Citation Engine menyediakan "akuntabilitas".**

Dengan pendekatan ini, aplikasi Anda dapat berkembang secara bertahap dari **aplikasi pembaca hadis + Fathul Bari** menjadi **platform riset hadis berbahasa Indonesia yang dapat ditelusuri sampai sumber aslinya**.
