# Stage 35 — Hadith–Fathul Bari Alignment Engine

Stage 35 membangun **mesin alignment otomatis** yang menghubungkan setiap hadis dari **Ahmad Sanusi Hadits API** dengan passage syarah yang relevan di corpus *Fathul Bari*.

Targetnya:

```text
Hadis
  ↓
Identitas hadis
  ↓
Matn fingerprint
  ↓
Pencarian Fathul Bari
  ↓
Candidate passages
  ↓
Lexical + Semantic matching
  ↓
Context analysis
  ↓
Reranking
  ↓
Confidence
  ↓
Human verification
  ↓
Verified Hadith ↔ Sharh links
```

---

# 35.1 Tujuan Utama

Saat pengguna membuka:

```text
Hadis Bukhari #1571
```

sistem harus dapat menghasilkan:

```text
Hadis #1571

├── Fathul Bari Vol. X, p. XXX
│   └── Syarah utama
│
├── Fathul Bari Vol. X, p. XXX
│   └── Penjelasan tambahan
│
├── Fathul Bari Vol. X, p. XXX
│   └── Referensi silang
│
└── Fathul Bari Vol. X, p. XXX
    └── Pembahasan lafaz
```

Setiap hasil memiliki:

```text
confidence
match_type
source_page
verification_status
```

---

# 35.2 Prinsip Penting

Alignment **tidak boleh hanya berdasarkan nomor hadis**.

Karena:

* numbering edition dapat berbeda
* beberapa syarah mengulang pembahasan
* Ibn Hajar dapat membahas satu hadis di beberapa tempat
* hadis dapat dirujuk melalui potongan matn
* passage dapat membahas hadis tanpa menyebut nomor hadis

Karena itu engine menggunakan beberapa sinyal.

---

# 35.3 Multi-Signal Alignment

Gunakan:

```text
                     ┌─ Hadith Number
                     │
                     ├─ Kitab
                     │
                     ├─ Bab
Hadith ──────────────┼─ Matn
                     │
                     ├─ Narrator
                     │
                     ├─ Opening Phrase
                     │
                     ├─ Semantic Similarity
                     │
                     ├─ Lexical Similarity
                     │
                     └─ Local Context
```

---

# 35.4 Alignment Pipeline

```text
Hadith API
    │
    ▼
Hadith Normalizer
    │
    ▼
Hadith Identity Resolver
    │
    ▼
Candidate Generator
    │
    ├── Exact search
    ├── Fuzzy search
    ├── BM25
    └── Vector search
    │
    ▼
Candidate Pool
    │
    ▼
Feature Extraction
    │
    ▼
Reranker
    │
    ▼
Confidence Engine
    │
    ├── AUTO_VERIFY
    ├── REVIEW
    └── REJECT
    │
    ▼
Alignment Database
```

---

# 35.5 Hadith Identity

Tambahkan tabel:

```sql
CREATE TABLE hadith_identities (
    id UUID PRIMARY KEY,

    external_source VARCHAR(100),

    external_id TEXT,

    collection TEXT,

    hadith_number TEXT,

    kitab TEXT,

    bab TEXT,

    narrator TEXT,

    arabic_matn TEXT,

    normalized_matn TEXT,

    matn_fingerprint TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (
        external_source,
        external_id
    )
);
```

Contoh:

```json
{
  "external_source": "ahmad_sanusi",
  "external_id": "bukhari-1571",
  "collection": "Bukhari",
  "hadith_number": "1571",
  "kitab": "...",
  "bab": "...",
  "narrator": "...",
  "matn_fingerprint": "sha256..."
}
```

---

# 35.6 Jangan Mengubah External ID

ID dari API harus dipertahankan:

```text
external_id
```

Sistem internal memiliki:

```text
hadith_id
```

Jadi:

```text
Ahmad Sanusi ID
       ↓
Internal Hadith ID
```

Ini membuat sistem tidak bergantung pada satu provider.

---

# 35.7 Hadith Source Abstraction

Gunakan interface:

```text
HadithProvider
```

dengan implementasi:

```text
AhmadSanusiProvider
BukhariProvider
MuslimProvider
LocalCorpusProvider
```

Sehingga architecture:

```text
Hadith Service
      │
      ▼
HadithProvider
      │
 ┌────┼────┐
 ▼    ▼    ▼
AS    Local Other
```

---

# 35.8 Hadith Normalization

Buat service:

```text
HadithNormalizer
```

Input:

```text
Arabic matn
```

Output:

```json
{
  "display": "...",
  "normalized": "...",
  "tokens": [],
  "fingerprint": "...",
  "opening_phrase": "...",
  "closing_phrase": "..."
}
```

---

# 35.9 Normalization Rules

Search representation dapat melakukan:

```text
Unicode normalization
Whitespace normalization
Tatweel removal
Diacritic normalization
Alef normalization
Punctuation normalization
```

Tetapi:

> **display text tidak boleh diubah.**

---

# 35.10 Matn Fingerprint

```text
normalized_matn
       ↓
SHA256
       ↓
matn_fingerprint
```

Contoh:

```text
sha256:
91c4e7...
```

Fingerprint digunakan untuk:

* duplicate detection
* cross-source matching
* edition alignment

---

# 35.11 Partial Fingerprint

Selain full matn, buat:

```text
opening_fingerprint
core_fingerprint
closing_fingerprint
```

Karena syarah sering mengutip hanya bagian awal hadis.

---

# 35.12 Hadith Token Signature

Buat signature:

```json
{
  "tokens": [
    "إنما",
    "الأعمال",
    "بالنيات"
  ]
}
```

Kemudian gunakan untuk lexical similarity.

---

# 35.13 Candidate Generator

Candidate generator menghasilkan maksimal:

```text
Top 50 passages
```

misalnya:

```text
Hadith
   ↓
BM25
   ↓
Top 20

Vector Search
   ↓
Top 20

Exact phrase
   ↓
Top 10

Context matching
   ↓
Combined Top 50
```

---

# 35.14 Candidate Sources

Ada empat jalur:

```text
1. Exact
2. Lexical
3. Semantic
4. Structural
```

---

# 35.15 Exact Matching

Cari:

```text
full normalized matn
```

Jika ditemukan:

```text
MATCH_TYPE = EXACT_MATN
```

Ini sinyal terkuat.

---

# 35.16 Phrase Matching

Ambil beberapa n-gram penting:

```text
5-token
8-token
12-token
```

Cari di corpus.

Contoh:

```text
"إنما الأعمال بالنيات"
```

---

# 35.17 Fuzzy Matching

Gunakan:

```text
Levenshtein
Jaccard
token overlap
character similarity
```

untuk menangani OCR error.

---

# 35.18 OCR-Aware Matching

Karena corpus berasal dari OCR:

```text
الحافظ
```

mungkin terbaca:

```text
الحاظف
```

Engine harus mampu mengenali kemungkinan kesalahan OCR.

---

# 35.19 Semantic Search

Embedding hadis:

```text
Hadith
 ↓
Embedding
```

lalu:

```text
Vector Search
```

terhadap:

```text
Fathul Bari chunks
```

---

# 35.20 Structural Matching

Ini sangat penting.

Jika metadata hadis:

```text
Kitab al-Iman
Bab X
```

dan passage Fathul Bari berada di:

```text
Kitab al-Iman
Bab X
```

berikan bonus.

---

# 35.21 Structural Signals

Gunakan:

```text
collection_match
kitab_match
bab_match
hadith_number_match
volume_context
```

---

# 35.22 Narrator Matching

Jika hadis memiliki:

```text
رواه أبو هريرة
```

dan passage menyebut:

```text
عن أبي هريرة
```

berikan signal tambahan.

Jangan jadikan narrator sebagai bukti tunggal.

---

# 35.23 Candidate Object

```json
{
  "hadith_id": "H1571",
  "passage_id": "P88421",

  "signals": {
    "exact_matn": 1.0,
    "lexical": 0.94,
    "semantic": 0.91,
    "kitab": 1.0,
    "bab": 0.95,
    "narrator": 0.80
  }
}
```

---

# 35.24 Feature Score

Model awal:

```text
score =
0.30 × exact_matn
+
0.20 × lexical
+
0.20 × semantic
+
0.10 × kitab
+
0.08 × bab
+
0.05 × narrator
+
0.07 × context
```

**Ini starting point**, bukan angka final.

Bobot nantinya harus ditentukan berdasarkan evaluation dataset.

---

# 35.25 Confidence Bands

```text
0.95 – 1.00
AUTO VERIFIED CANDIDATE

0.85 – 0.949
HIGH CONFIDENCE

0.70 – 0.849
REVIEW

0.50 – 0.699
LOW CONFIDENCE

< 0.50
REJECT
```

Jangan menyebut `AUTO VERIFIED` sebagai verified ilmiah jika belum ada human verification. Lebih aman:

```text
AUTO_ACCEPT_CANDIDATE
```

---

# 35.26 Alignment Status

```text
CANDIDATE
REVIEW_REQUIRED
HUMAN_VERIFIED
REJECTED
SUPERSEDED
```

---

# 35.27 Alignment Types

```text
PRIMARY_SHARH
DIRECT_QUOTATION
PARTIAL_QUOTATION
EXPLANATORY
CROSS_REFERENCE
REPEATED_DISCUSSION
RELATED_TOPIC
```

---

# 35.28 Database Alignment

```sql
CREATE TABLE hadith_sharh_alignments (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL,

    passage_id UUID NOT NULL,

    alignment_type VARCHAR(50),

    score NUMERIC(6,5),

    confidence_band VARCHAR(30),

    status VARCHAR(30),

    matched_features JSONB,

    explanation JSONB,

    verified_by UUID,

    verified_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (
        hadith_id,
        passage_id
    )
);
```

---

# 35.29 Explanation Object

Simpan **mengapa** engine memilih passage.

```json
{
  "reasons": [
    "Exact matn fragment found",
    "Same kitab",
    "Same bab",
    "High semantic similarity"
  ]
}
```

Ini sangat berguna saat reviewer menolak hasil.

---

# 35.30 Alignment Evidence

Tambahkan:

```sql
CREATE TABLE alignment_evidence (
    id UUID PRIMARY KEY,

    alignment_id UUID NOT NULL,

    evidence_type VARCHAR(40),

    source_text TEXT,

    matched_text TEXT,

    score NUMERIC(6,5),

    metadata JSONB DEFAULT '{}'
);
```

Contoh:

```text
Evidence:
EXACT_PHRASE

Matched:
"إنما الأعمال بالنيات"
```

---

# 35.31 Candidate Ranking

UI:

```text
Hadis Bukhari #1571

Candidates

1. Vol. 1 p. 48
   Score 0.987
   Exact matn
   Same kitab
   Same bab

2. Vol. 1 p. 49
   Score 0.923
   Semantic match
   Related passage

3. Vol. 2 p. 311
   Score 0.811
   Cross-reference
```

---

# 35.32 Reviewer Workflow

```text
Candidate
   ↓
Open
   ↓
Compare Hadith
   ↓
Compare Fathul Bari
   ↓
Open Scan
   ↓
Accept / Reject
```

---

# 35.33 Alignment Review UI

```text
┌─────────────────────────────────────────────┐
│ HADITH #1571                                │
├──────────────────────┬──────────────────────┤
│ HADITH                │ FATHUL BARI         │
│                      │                      │
│ Arabic Matn          │ Passage              │
│                      │                      │
│ [Hadith text]        │ [Sharh text]         │
│                      │                      │
├──────────────────────┴──────────────────────┤
│ Score: 0.962                                │
│ Match: EXACT + SEMANTIC + STRUCTURAL       │
│                                             │
│ [VERIFY] [REJECT] [RELATED] [OPEN SOURCE]  │
└─────────────────────────────────────────────┘
```

---

# 35.34 Human Verification

Jika reviewer menekan:

```text
VERIFY
```

maka:

```text
status = HUMAN_VERIFIED
```

dan:

```text
verified_by
verified_at
```

diisi.

---

# 35.35 Reject

Jika:

```text
REJECT
```

simpan alasan:

```text
wrong hadith
wrong passage
OCR error
same topic only
duplicate
```

---

# 35.36 Human Label Dataset

Setiap review menghasilkan training/evaluation data:

```json
{
  "hadith": "H1571",
  "passage": "P88421",
  "label": 1
}
```

atau:

```json
{
  "hadith": "H1571",
  "passage": "P88122",
  "label": 0
}
```

Ini akan menjadi **gold alignment dataset**.

---

# 35.37 Active Learning

Setelah terkumpul:

```text
5,000 verified alignments
```

kita dapat melatih reranker khusus domain.

Pipeline:

```text
Initial Rules
       ↓
Human Review
       ↓
Gold Dataset
       ↓
Reranker Training
       ↓
Better Candidate Ranking
       ↓
More Human Review
```

---

# 35.38 Reranker Architecture

Tahap awal:

```text
BM25
+
Vector similarity
+
Rules
```

Tahap berikutnya:

```text
Cross Encoder / Reranker
```

Input:

```text
[Hadith] [Passage]
```

Output:

```text
relevance score
```

---

# 35.39 Jangan Langsung Fine-Tune LLM

Untuk Stage 35:

**tidak perlu langsung fine-tune LLM.**

Mulai dengan:

```text
retrieval
+
features
+
reranking
```

lebih mudah diaudit.

---

# 35.40 Alignment Graph

Setelah verified:

```text
Hadith
   │
   │ EXPLAINED_BY
   ▼
Fathul Bari Passage
   │
   ▼
Page
   │
   ▼
Volume
   │
   ▼
Edition
```

Ini masuk langsung ke Knowledge Graph Stage 9.

---

# 35.41 Graph Edge

```json
{
  "source": "hadith:H1571",
  "relation": "EXPLAINED_BY",
  "target": "passage:P88421",

  "confidence": 0.962,

  "verification": "HUMAN_VERIFIED"
}
```

---

# 35.42 Cross-References

Misalnya:

```text
Hadith #1571
   ↓
Fathul Bari p. 48
   ↓
mentions Hadith #1572
```

Graph:

```text
H1571
 ├── EXPLAINED_BY → P88421
 └── REFERENCES → H1572
```

---

# 35.43 Multiple Sharh Passages

Satu hadis dapat memiliki:

```text
PRIMARY_SHARH
+
SECONDARY_SHARH
+
CROSS_REFERENCE
```

Jangan membatasi:

```text
1 Hadith = 1 Passage
```

Model data harus:

```text
1 Hadith
    ↓
N Passages
```

---

# 35.44 Passage Importance

Tambahkan:

```text
relevance_role
```

nilai:

```text
PRIMARY
SECONDARY
SUPPLEMENTARY
CROSS_REFERENCE
```

---

# 35.45 Passage Ordering

Saat ditampilkan:

```text
PRIMARY
↓
SECONDARY
↓
SUPPLEMENTARY
↓
CROSS_REFERENCE
```

Kemudian berdasarkan:

```text
page order
```

---

# 35.46 Repeated Commentary

Ibn Hajar dapat membahas tema serupa di beberapa tempat.

Engine harus membedakan:

```text
same exact commentary
```

dengan:

```text
related commentary
```

Jangan otomatis menggabungkan keduanya.

---

# 35.47 Hadith Topic vs Hadith Commentary

Ini adalah distinction penting.

Contoh:

```text
Hadith:
Tentang niat
```

Passage:

```text
membahas keutamaan niat
```

Belum tentu:

```text
syarah langsung hadis tersebut.
```

Maka:

```text
RELATED_TOPIC
```

bukan:

```text
PRIMARY_SHARH
```

---

# 35.48 Direct Evidence

Kategori terkuat:

```text
قال ابن حجر:
```

diikuti:

```text
matn / lafaz hadis
```

atau konteks langsung.

---

# 35.49 Context Window

Saat candidate ditemukan:

```text
passage
```

ambil:

```text
±2 paragraphs
```

atau:

```text
±1 page context
```

untuk analisis.

Karena kadang:

```text
hadith quote
```

berada pada paragraph sebelumnya.

---

# 35.50 Local Context Model

```text
Previous Passage
       ↓
Target Passage
       ↓
Next Passage
```

Semua diberikan ke reranker.

---

# 35.51 Alignment API

Tambahkan:

```http
POST /api/v1/alignment/hadith/{hadithId}

GET /api/v1/alignment/hadith/{hadithId}

POST /api/v1/alignment/{alignmentId}/verify

POST /api/v1/alignment/{alignmentId}/reject

GET /api/v1/alignment/review-queue
```

---

# 35.52 Run Alignment

```http
POST /api/v1/alignment/hadith/H1571
```

Response:

```json
{
  "hadith_id": "H1571",
  "status": "COMPLETED",

  "candidates": [
    {
      "passage_id": "P88421",
      "score": 0.962,
      "status": "REVIEW_REQUIRED"
    }
  ]
}
```

---

# 35.53 Batch Alignment

Untuk seluruh Bukhari:

```http
POST /api/v1/alignment/batch
```

```json
{
  "collection": "Bukhari",
  "from": 1,
  "to": 7563
}
```

---

# 35.54 Batch Architecture

Jangan:

```text
HTTP request
 ↓
7,000 hadis
```

Gunakan:

```text
Batch Request
 ↓
Alignment Job
 ↓
Queue
 ↓
Workers
```

---

# 35.55 Alignment Worker

```text
workers/
└── alignment-worker/
    ├── candidate-generator
    ├── feature-extractor
    ├── reranker
    ├── confidence-engine
    └── persistence
```

---

# 35.56 Alignment Job

```sql
CREATE TABLE alignment_jobs (
    id UUID PRIMARY KEY,

    collection TEXT,

    total_hadiths INTEGER,

    processed_hadiths INTEGER DEFAULT 0,

    candidates_generated INTEGER DEFAULT 0,

    verified_count INTEGER DEFAULT 0,

    review_count INTEGER DEFAULT 0,

    rejected_count INTEGER DEFAULT 0,

    status VARCHAR(30),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    completed_at TIMESTAMPTZ
);
```

---

# 35.57 Performance

Gunakan precomputed:

```text
Hadith embeddings
Passage embeddings
Matn fingerprints
BM25 index
Kitab metadata index
Bab metadata index
```

Sehingga alignment tidak perlu menghitung ulang.

---

# 35.58 Search Optimization

Buat index:

```sql
CREATE INDEX idx_hadith_fingerprint
ON hadith_identities(matn_fingerprint);

CREATE INDEX idx_passage_page
ON source_passages(page_id);

CREATE INDEX idx_alignment_hadith
ON hadith_sharh_alignments(hadith_id);

CREATE INDEX idx_alignment_status
ON hadith_sharh_alignments(status);
```

---

# 35.59 Alignment Cache

Jika:

```text
Hadith H1571
```

sudah diproses:

```text
return cached candidates
```

kecuali:

```text
corpus version changed
embedding version changed
algorithm version changed
```

---

# 35.60 Algorithm Versioning

Simpan:

```text
alignment_algorithm_version
```

Contoh:

```text
alignment-v1
```

kemudian:

```text
alignment-v2
```

Ini memungkinkan membandingkan hasil.

---

# 35.61 Corpus Version Dependency

Alignment harus menyimpan:

```json
{
  "corpus_version": "1.2.0",
  "embedding_version": "bge-v2",
  "algorithm_version": "alignment-v1"
}
```

Jika corpus berubah, alignment lama tidak otomatis dianggap invalid tanpa evaluasi.

---

# 35.62 Alignment Confidence Calibration

Jangan menganggap:

```text
0.90 = 90% benar
```

sebelum calibration.

Gunakan dataset human verified.

Kemudian ukur:

```text
Precision
Recall
F1
Precision@K
Recall@K
MRR
nDCG
```

---

# 35.63 Target Metrics

Untuk tahap awal:

```text
Recall@10 ≥ 95%
```

lebih penting daripada:

```text
Precision@1
```

Karena kita ingin **tidak melewatkan syarah yang relevan**.

Kemudian reranker meningkatkan precision.

---

# 35.64 Evaluation Dataset

Buat:

```text
alignment-gold.jsonl
```

format:

```json
{
  "hadith_id": "H1571",
  "positive_passages": [
    "P88421"
  ],
  "negative_passages": [
    "P88122",
    "P77211"
  ]
}
```

---

# 35.65 Evaluation Pipeline

```text
Gold Dataset
     ↓
Candidate Generator
     ↓
Recall@10
     ↓
Reranker
     ↓
MRR
     ↓
Precision@1
```

---

# 35.66 Failure Analysis

Dashboard:

```text
ALIGNMENT FAILURES

OCR error                 32%
Number mismatch           21%
Missing metadata          18%
Related-topic confusion   15%
Low semantic similarity   10%
Other                      4%
```

Ini membantu menentukan prioritas engineering berikutnya.

---

# 35.67 Reviewer Prioritization

Review queue sebaiknya tidak random.

Urutkan:

```text
high-impact hadith
+
low confidence
+
high retrieval frequency
+
large disagreement
```

---

# 35.68 Impact Score

Contoh:

```text
impact =
usage_frequency
×
importance
×
uncertainty
```

Jadi reviewer memeriksa alignment paling penting terlebih dahulu.

---

# 35.69 User-Facing Hadith Page

Setelah alignment tersedia:

```text
┌───────────────────────────────────────────┐
│ HADIS BUKHARI #1571                       │
├───────────────────────────────────────────┤
│ Arabic Matn                               │
│                                           │
│ Terjemahan                                │
│                                           │
├───────────────────────────────────────────┤
│ SYARAH FATHUL BARI                        │
│                                           │
│ ★ Pembahasan Utama                        │
│ Vol. 3 • p. 218                           │
│                                           │
│ [Baca Syarah] [Lihat Scan]               │
│                                           │
│ ───────────────────────────────────────── │
│ Pembahasan Terkait                        │
│ Vol. 3 • p. 219                           │
│                                           │
└───────────────────────────────────────────┘
```

---

# 35.70 AI Assistant Integration

Sekarang RAG bisa melakukan:

```text
User:
"Jelaskan syarah Ibn Hajar terhadap hadis ini."
```

Pipeline:

```text
Hadith ID
 ↓
Verified Alignments
 ↓
Primary passages
 ↓
Secondary passages
 ↓
RAG
 ↓
Answer
```

Ini jauh lebih aman daripada:

```text
semantic search seluruh kitab
```

---

# 35.71 Citation Generation

AI harus mengutip:

```text
[Fathul Bari, Vol. X, p. XXX]
```

dan citation internal:

```json
{
  "passage_id": "P88421",
  "page_id": "PG998"
}
```

Klik citation:

```text
→ Source Viewer
```

---

# 35.72 Anti-Hallucination Rule

Jika tidak ada verified alignment:

```text
Jangan mengatakan:

"Ibn Hajar menjelaskan..."

Gunakan:

"Belum ditemukan passage Fathul Bari yang telah diverifikasi untuk hadis ini."
```

---

# 35.73 Evidence Threshold

Untuk claim kuat:

```text
HUMAN_VERIFIED
```

Untuk draft:

```text
HIGH_CONFIDENCE
```

AI harus membedakan keduanya.

---

# 35.74 Audit Trail

Setiap alignment:

```text
Created
 ↓
Candidate generated
 ↓
Score calculated
 ↓
AI recommendation
 ↓
Human review
 ↓
Verified / Rejected
```

---

# 35.75 Audit Example

```json
{
  "event": "ALIGNMENT_VERIFIED",
  "hadith_id": "H1571",
  "passage_id": "P88421",
  "actor_type": "HUMAN",
  "algorithm_version": "alignment-v1",
  "previous_status": "REVIEW_REQUIRED",
  "new_status": "HUMAN_VERIFIED"
}
```

---

# 35.76 Security Rule

User biasa:

```text
READ
```

Reviewer:

```text
READ
VERIFY
REJECT
```

Admin:

```text
READ
VERIFY
REJECT
REPROCESS
OVERRIDE
```

AI:

```text
CREATE_CANDIDATE
```

AI **tidak boleh**:

```text
HUMAN_VERIFY
```

---

# 35.77 Knowledge Graph Integration

Tambahkan edge:

```text
HADITH
  │
  ├── EXPLAINED_BY
  │
  ▼
FATHUL_BARI_PASSAGE
```

Properties:

```json
{
  "confidence": 0.962,
  "status": "HUMAN_VERIFIED",
  "alignment_type": "PRIMARY_SHARH"
}
```

---

# 35.78 Final Architecture Stage 35

```text
                    ┌──────────────────────┐
                    │ Ahmad Sanusi API     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Hadith Normalizer    │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         Exact Search      BM25 Search     Vector Search
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Candidate Generator  │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Feature Extraction   │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Reranker             │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Confidence Engine    │
                    └──────────┬───────────┘
                               │
                  ┌────────────┼─────────────┐
                  ▼            ▼             ▼
               ACCEPT        REVIEW        REJECT
                  │            │
                  │            ▼
                  │      Human Reviewer
                  │            │
                  └────────────┤
                               ▼
                    ┌──────────────────────┐
                    │ Alignment Database   │
                    └──────────┬───────────┘
                               │
               ┌───────────────┼────────────────┐
               ▼               ▼                ▼
          Knowledge Graph     RAG          Hadith Page
                                               │
                                               ▼
                                         Source Viewer
```

---

# 35.79 Definition of Done

Stage 35 selesai apabila:

```text
[ ] Hadith provider abstraction
[ ] Ahmad Sanusi integration
[ ] Hadith identity resolver
[ ] Arabic normalizer
[ ] Matn fingerprint
[ ] Partial fingerprint
[ ] Exact matching
[ ] Phrase matching
[ ] Fuzzy matching
[ ] BM25 retrieval
[ ] Vector retrieval
[ ] Structural matching
[ ] Narrator matching
[ ] Candidate generator
[ ] Feature extraction
[ ] Reranker
[ ] Confidence engine
[ ] Alignment database
[ ] Alignment evidence
[ ] Alignment explanation
[ ] Human review
[ ] Verify / Reject
[ ] Audit trail
[ ] Batch alignment
[ ] Alignment worker
[ ] Algorithm versioning
[ ] Corpus version dependency
[ ] Gold dataset
[ ] Recall@K evaluation
[ ] Knowledge Graph edge
[ ] RAG integration
[ ] Citation integration
[ ] Source Viewer integration
[ ] Anti-hallucination rule
```

---

# Posisi Sistem Setelah Stage 35

Sekarang alurnya sudah berubah dari:

```text
Hadis → Search → AI
```

menjadi:

```text
                         HADITH
                           │
                           ▼
                  Hadith Identity
                           │
                           ▼
                  Alignment Engine
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Exact          BM25         Vector
             └─────────────┼─────────────┘
                           ▼
                       Reranker
                           │
                           ▼
                    Confidence
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                 Human          RAG
                Verify            │
                    │             │
                    └──────┬──────┘
                           ▼
                    Fathul Bari
                      Evidence
                           │
                  ┌────────┼────────┐
                  ▼        ▼        ▼
                Scan      Graph     AI
```

**Ini merupakan salah satu komponen terpenting aplikasi Anda**, karena mulai membangun hubungan formal antara **hadis → syarah → halaman sumber → bukti scan**.
