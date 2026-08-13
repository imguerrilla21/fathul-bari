# Stage 20 — Hadith ↔ Fathul Bari Matching Engine

Stage 20 adalah tahap penting: kita mulai menghubungkan **hadis dari Ahmad Sanusi Hadits API** dengan **teks syarah Fathul Bari**.

Targetnya:

```text
Hadis Bukhari #1
        │
        ▼
┌─────────────────────────┐
│ Matching Engine          │
├─────────────────────────┤
│ Exact matching           │
│ Arabic normalization     │
│ Lexical similarity       │
│ Semantic similarity      │
│ Hadith number/reference  │
│ Context similarity       │
└────────────┬────────────┘
             ▼
     Candidate Matches
             │
             ▼
       Confidence Score
             │
       ┌─────┴─────┐
       ▼           ▼
    HIGH/MEDIUM   LOW
       │           │
       ▼           ▼
   Review Queue   Reject
```

Tujuan Stage 20 **bukan membuat AI langsung menyatakan "ini pasti syarah hadis X"**. Sistem hanya menghasilkan **candidate match** yang kemudian dapat diverifikasi manusia.

---

# 20.1 Prinsip Matching

Kita menggunakan beberapa sinyal sekaligus:

```text
Final Score
=
Exact Reference
+
Hadith Number
+
Lexical Similarity
+
Semantic Similarity
+
Section Context
```

Contoh:

```text
Hadis:
إنما الأعمال بالنيات

Fathul Bari:
قوله إنما الأعمال بالنيات...

                 ↓

Exact phrase       = 1.00
Lexical similarity = 0.96
Semantic similarity= 0.94
Reference signal   = 1.00

                 ↓

Final confidence   = 0.97
```

---

# 20.2 Jangan Mengandalkan Embedding Saja

Ini penting untuk aplikasi penelitian hadis.

Misalnya:

```text
Hadis A
إنما الأعمال بالنيات

Hadis B
الأعمال بالنيات وإنما لكل امرئ ما نوى
```

Embedding mungkin menganggap keduanya sangat mirip.

Tetapi kita harus membedakan:

```text
similarity
```

dengan:

```text
identity
```

Karena itu matching menggunakan **multi-signal architecture**.

---

# 20.3 Candidate Generation

Jangan membandingkan:

```text
10.000 hadis × 100.000 chunks
```

secara brute force.

Gunakan candidate generation.

```text
                Fathul Bari Chunk
                       │
                       ▼
              Candidate Retrieval
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Lexical       Vector       Reference
       Search        Search       Search
          │            │            │
          └────────────┼────────────┘
                       ▼
                  Top Candidates
```

Misalnya:

```text
100.000 chunks
      ↓
top 100 lexical
      +
top 100 semantic
      +
explicit references
      ↓
union
      ↓
~150 candidates
```

Barulah reranking dilakukan.

---

# 20.4 Matching Pipeline

```text
Hadith
  │
  ▼
Normalize
  │
  ▼
Extract anchors
  │
  ├── hadith number
  ├── narrator
  ├── opening phrase
  ├── distinctive phrase
  └── collection
  │
  ▼
Candidate retrieval
  │
  ▼
Feature calculation
  │
  ▼
Scoring
  │
  ▼
Confidence calibration
  │
  ▼
Candidate Match
```

---

# 20.5 Data Model

Tambahkan tabel:

```text
hadith_matches
```

Schema:

```sql
CREATE TABLE hadith_matches (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL
        REFERENCES hadiths(id),

    sharh_chunk_id UUID NOT NULL
        REFERENCES sharh_chunks(id),

    match_type VARCHAR(50) NOT NULL,

    lexical_score NUMERIC(6,5),
    semantic_score NUMERIC(6,5),
    reference_score NUMERIC(6,5),
    context_score NUMERIC(6,5),

    confidence_score NUMERIC(6,5),

    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',

    matcher_version VARCHAR(50) NOT NULL,

    explanation JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(hadith_id, sharh_chunk_id)
);
```

---

# 20.6 Match Status

```text
PENDING
VERIFIED
REJECTED
NEEDS_REVIEW
```

Flow:

```text
Candidate
    │
    ▼
PENDING
    │
    ├── reviewer → VERIFY
    │
    ├── reviewer → REJECT
    │
    └── system → NEEDS_REVIEW
```

---

# 20.7 Match Type

```text
EXACT_REFERENCE
EXACT_TEXT
LEXICAL
SEMANTIC
HYBRID
MANUAL
```

Contoh:

```json
{
  "match_type": "HYBRID"
}
```

---

# 20.8 Evidence Explanation

Setiap candidate harus menjelaskan **mengapa** ia dianggap cocok.

Misalnya:

```json
{
  "signals": [
    {
      "type": "EXACT_PHRASE",
      "value": "إنما الأعمال بالنيات",
      "score": 1.0
    },
    {
      "type": "HADITH_REFERENCE",
      "value": "حديث رقم 1",
      "score": 1.0
    },
    {
      "type": "SEMANTIC",
      "score": 0.94
    }
  ]
}
```

Ini jauh lebih baik daripada hanya:

```json
{
  "confidence": 0.96
}
```

---

# 20.9 Arabic Normalization Engine

Buat:

```text
app/nlp/arabic_normalizer.py
```

Pipeline:

```text
Raw Arabic
    ↓
Unicode NFC
    ↓
Remove Tatweel
    ↓
Remove diacritics
    ↓
Normalize Alef variants
    ↓
Normalize Ya
    ↓
Normalize Ta Marbuta
    ↓
Whitespace normalization
```

Contoh:

```python
import re
import unicodedata

ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

def normalize_arabic(text: str) -> str:
    text = unicodedata.normalize("NFC", text)

    text = text.replace("ـ", "")

    text = ARABIC_DIACRITICS.sub("", text)

    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")
    text = text.replace("ى", "ي")

    text = re.sub(r"\s+", " ", text)

    return text.strip()
```

**Catatan:** fungsi ini untuk pencarian/matching. Teks asli tidak boleh ditimpa.

---

# 20.10 Exact Phrase Matcher

Cari frasa pembuka hadis:

```text
إنما الأعمال بالنيات
```

dalam chunk:

```text
قال الحافظ رحمه الله: قوله إنما الأعمال بالنيات...
```

Jika ditemukan:

```text
exact_phrase_score = 1.0
```

Tetapi jangan langsung:

```text
confidence = 1.0
```

karena frasa bisa disebut dalam konteks lain.

---

# 20.11 Hadith Anchor Extraction

Buat:

```text
app/matching/anchors.py
```

Anchor:

```text
Hadith number
Collection
Narrator
Opening phrase
Distinctive n-grams
Known reference
```

Contoh:

```json
{
  "collection": "bukhari",
  "number": "1",
  "opening": "إنما الأعمال بالنيات",
  "narrators": [
    "عمر بن الخطاب"
  ]
}
```

---

# 20.12 Reference Detector

Fathul Bari sering memiliki pola referensi yang dapat membantu.

Sistem mencari pola seperti:

```text
حديث رقم ...
الحديث ...
رواه البخاري
أخرجه البخاري
```

Tetapi hasil parser diberi status:

```text
SYSTEM_DETECTED
```

bukan otomatis dianggap fakta final.

---

# 20.13 Lexical Similarity

Gunakan token-level similarity.

Contoh:

```text
Hadith:
إنما الأعمال بالنيات وإنما لكل امرئ ما نوى

Chunk:
قوله إنما الأعمال بالنيات وإنما لكل امرئ ما نوى
```

Overlap tinggi.

Kita dapat menggunakan:

```text
Jaccard
Dice
token overlap
character n-gram similarity
```

Untuk Arabic, character n-gram sering berguna karena menangani variasi morfologi dan tokenisasi dengan lebih toleran.

---

# 20.14 Semantic Similarity

Setelah Stage 19/ingestion memiliki embedding:

```text
Hadith embedding
        │
        ▼
Vector search
        │
        ▼
Fathul Bari embeddings
```

Menghasilkan:

```text
semantic_score
```

Misalnya:

```text
0.91
```

---

# 20.15 Hybrid Score

Versi awal:

```text
score =
    0.30 × lexical
  + 0.35 × semantic
  + 0.20 × reference
  + 0.15 × context
```

Tetapi angka ini **bukan nilai final secara ilmiah**.

Nantinya kita kalibrasi menggunakan dataset hasil review manusia.

---

# 20.16 Confidence Bands

Gunakan:

```text
0.90 – 1.00
HIGH

0.75 – 0.89
MEDIUM

0.50 – 0.74
LOW

< 0.50
VERY_LOW
```

Contoh:

```text
0.96 → HIGH
0.84 → MEDIUM
0.61 → LOW
```

---

# 20.17 Tetapi Confidence ≠ Truth

UI harus mengatakan:

```text
Confidence: 0.96
```

bukan:

```text
Kebenaran: 96%
```

Lebih tepat:

> "Sistem memperkirakan tingkat kecocokan sebesar 96% berdasarkan sinyal yang tersedia."

---

# 20.18 Matcher Service

Struktur:

```text
app/matching/
├── __init__.py
├── anchors.py
├── lexical.py
├── semantic.py
├── reference.py
├── scorer.py
├── candidate_generator.py
└── service.py
```

---

# 20.19 Candidate Generator

Pseudo-code:

```python
async def generate_candidates(hadith):

    lexical = await lexical_search(
        hadith.normalized_text,
        limit=100,
    )

    semantic = await vector_search(
        hadith.embedding,
        limit=100,
    )

    references = await reference_search(
        hadith.external_id,
    )

    return merge_unique(
        lexical,
        semantic,
        references,
    )
```

---

# 20.20 Scoring

```python
def calculate_score(features):

    return (
        0.30 * features.lexical +
        0.35 * features.semantic +
        0.20 * features.reference +
        0.15 * features.context
    )
```

Kemudian:

```python
confidence = calibrate(raw_score)
```

---

# 20.21 Matcher Version

Setiap match menyimpan:

```text
matcher_version = "20.1.0"
```

Kenapa?

Karena suatu hari kita mengubah:

```text
weight
normalizer
embedding model
reranker
```

maka hasil lama tetap dapat dilacak.

---

# 20.22 Batch Matching

Endpoint:

```http
POST /api/v1/matching/run
```

Request:

```json
{
  "collection": "bukhari",
  "from_hadith": 1,
  "to_hadith": 100
}
```

Response:

```json
{
  "job_id": "...",
  "status": "QUEUED"
}
```

---

# 20.23 Jangan Menjalankan Matching di HTTP

Salah:

```text
POST /matching/run
      ↓
match 5.000 hadis
      ↓
HTTP menunggu
```

Benar:

```text
POST /matching/run
      ↓
job_id
      ↓
Redis
      ↓
Worker
      ↓
Matching
```

---

# 20.24 Review Queue

Setelah matching:

```text
HIGH
   ↓
candidate

MEDIUM
   ↓
review

LOW
   ↓
review/reject
```

Namun untuk penelitian yang sangat sensitif, bahkan `HIGH` tetap sebaiknya dapat diverifikasi manusia.

---

# 20.25 Review Dashboard

Kita akan mengubah dashboard Stage sebelumnya menjadi:

```text
┌─────────────────────────────────────────────┐
│ MATCH REVIEW                                │
├─────────────────────────────────────────────┤
│                                             │
│ HADIS                                       │
│ صحيح البخاري #1                             │
│                                             │
│ إنما الأعمال بالنيات...                     │
│                                             │
├─────────────────────────────────────────────┤
│ FATHUL BARI                                 │
│                                             │
│ Volume 1 · Page XX                          │
│                                             │
│ قوله إنما الأعمال بالنيات...                │
│                                             │
├─────────────────────────────────────────────┤
│ SIGNALS                                     │
│                                             │
│ Exact phrase        1.00                    │
│ Lexical             0.96                    │
│ Semantic            0.94                    │
│ Reference           1.00                    │
│                                             │
│ Confidence          0.96  HIGH              │
│                                             │
│ [ VERIFY ]             [ REJECT ]           │
└─────────────────────────────────────────────┘
```

---

# 20.26 Explainable Matching

Saat reviewer menekan:

```text
Why this match?
```

sistem menampilkan:

```text
✓ Hadith number matches
✓ Opening phrase matches
✓ 87% token overlap
✓ Semantic similarity: 0.94
✓ Same collection context

⚠ No explicit reference detected
```

Ini akan sangat membantu reviewer.

---

# 20.27 Audit Trail

Jika:

```text
Reviewer A
```

menekan:

```text
VERIFY
```

simpan:

```json
{
  "action": "VERIFY_MATCH",
  "entity": "hadith_match",
  "entity_id": "...",
  "previous_status": "PENDING",
  "new_status": "VERIFIED",
  "reviewer_id": "...",
  "timestamp": "..."
}
```

---

# 20.28 Manual Override

Reviewer dapat mengoreksi sistem:

```text
[ Verify ]

[ Reject ]

[ Correct Source ]

[ Mark As Related ]

[ Duplicate ]

[ Not Enough Evidence ]
```

Status tambahan:

```text
RELATED
DUPLICATE
INSUFFICIENT_EVIDENCE
```

---

# 20.29 Related ≠ Exact Match

Ini penting.

Misalnya Fathul Bari membahas:

```text
Hadis A
```

dan juga mengutip:

```text
Hadis B
```

yang berkaitan.

Jangan memaksa:

```text
Hadis B = Hadis A
```

Simpan hubungan:

```text
RELATED
```

---

# 20.30 Knowledge Graph Preparation

Hasil Stage 20 nantinya menjadi edge:

```text
Hadith
   │
   │ EXPLAINED_BY
   ▼
SharhChunk
```

atau:

```text
Hadith A
   │
   │ RELATED_TO
   ▼
Hadith B
```

atau:

```text
Hadith
   │
   │ MENTIONED_IN
   ▼
Fathul Bari Section
```

Ini menjadi input langsung untuk Knowledge Graph Stage berikutnya.

---

# 20.31 Data Flow Lengkap

```text
             AHMAD SANUSI
                   │
                   ▼
              HADITH API
                   │
                   ▼
             INGESTION
                   │
                   ▼
              NORMALIZER
                   │
                   ▼
              POSTGRESQL
                   │
                   ▼
           ┌───────┴────────┐
           │                │
           ▼                ▼
      Lexical Search    Vector Search
           │                │
           └───────┬────────┘
                   ▼
            Candidate Set
                   │
                   ▼
               Scoring
                   │
                   ▼
             Confidence
                   │
                   ▼
            Review Queue
                   │
             ┌─────┴─────┐
             ▼           ▼
          VERIFY       REJECT
             │
             ▼
       Verified Match
             │
             ▼
       Knowledge Graph
```

---

# 20.32 API Endpoints Stage 20

### Candidate generation

```http
POST /api/v1/matching/run
```

### Job status

```http
GET /api/v1/matching/jobs/{job_id}
```

### List candidates

```http
GET /api/v1/matching/candidates
```

### Candidate detail

```http
GET /api/v1/matching/{match_id}
```

### Verify

```http
POST /api/v1/matching/{match_id}/verify
```

### Reject

```http
POST /api/v1/matching/{match_id}/reject
```

### Explain

```http
GET /api/v1/matching/{match_id}/explanation
```

---

# 20.33 Contoh Response Candidate

```json
{
  "id": "match_123",
  "hadith": {
    "collection": "bukhari",
    "number": "1",
    "text": "إنما الأعمال بالنيات..."
  },
  "sharh": {
    "volume": 1,
    "page": 45,
    "text": "قوله إنما الأعمال بالنيات..."
  },
  "scores": {
    "lexical": 0.96,
    "semantic": 0.94,
    "reference": 1.0,
    "context": 0.91,
    "confidence": 0.96
  },
  "status": "PENDING",
  "matcher_version": "20.1.0"
}
```

---

# 20.34 Testing

Kita wajib membuat **golden matching set**.

Contoh:

```text
100 hadis
+
gold-standard Fathul Bari references
```

Kemudian ukur:

```text
Precision
Recall
F1
MRR
Recall@5
Recall@10
```

Contoh:

```text
Recall@5 = 94%
Precision@1 = 91%
```

Baru kemudian bobot matcher dapat diperbaiki.

---

# 20.35 Golden Dataset

Struktur:

```json
{
  "hadith_external_id": "bukhari:1",
  "expected_sharh_chunks": [
    "fb:vol1:page45"
  ]
}
```

Dataset ini **tidak boleh dihasilkan hanya oleh LLM**.

Sumber ideal:

```text
manual expert verification
```

---

# 20.36 Target Stage 20

Pada akhir tahap ini:

```text
┌─────────────────────────────────────────────┐
│ Hadith #1                                   │
│                                             │
│ إنما الأعمال بالنيات...                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
             MATCH ENGINE
                   │
        ┌──────────┼───────────┐
        ▼          ▼           ▼
     Lexical    Semantic    Reference
        │          │           │
        └──────────┼───────────┘
                   ▼
             Candidate #1
                   │
             Confidence 96%
                   │
                   ▼
             REVIEW QUEUE
                   │
            ┌──────┴──────┐
            ▼             ▼
         VERIFY         REJECT
```

---

# 20.37 Definition of Done

```text
[ ] hadith_matches table
[ ] Arabic normalizer
[ ] anchor extraction
[ ] lexical matcher
[ ] semantic matcher
[ ] reference matcher
[ ] candidate generator
[ ] hybrid scorer
[ ] confidence bands
[ ] matcher versioning
[ ] matching worker
[ ] matching API
[ ] review API
[ ] explanation API
[ ] audit integration
[ ] golden dataset
[ ] evaluation metrics
```

---
