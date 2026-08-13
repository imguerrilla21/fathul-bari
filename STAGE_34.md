# Stage 34 — Scholarly Corpus Ingestion & Edition Management

Stage 34 adalah fondasi **corpus Fathul Bari**. Fokusnya sekarang bukan UI, melainkan bagaimana seluruh kitab dapat dimasukkan ke sistem secara **terstruktur, searchable, versioned, traceable, dan dapat diverifikasi terhadap scan asli**.

Target akhir:

```text
PDF / Scan
   ↓
Document Registry
   ↓
Page Extraction
   ↓
OCR
   ↓
Arabic Normalization
   ↓
Text Segmentation
   ↓
Volume / Page / Chapter Mapping
   ↓
Hadith Mapping
   ↓
Passage / Chunking
   ↓
Quality Control
   ↓
Edition Fingerprint
   ↓
Search Index
   ↓
Vector Index
   ↓
RAG
```

---

# 34.1 Prinsip Utama

Corpus Fathul Bari harus diperlakukan sebagai **scholarly source**, bukan sekadar kumpulan teks.

Setiap teks harus bisa menjawab:

> Dari edisi mana teks ini berasal?

> Volume berapa?

> Halaman berapa?

> Dari scan halaman mana?

> OCR engine apa yang digunakan?

> Apakah teks sudah diverifikasi manusia?

> Apakah ada perbedaan dengan edisi lain?

---

# 34.2 Source Hierarchy

Gunakan hierarchy:

```text
LEVEL 1
Original Scan

LEVEL 2
Page Image

LEVEL 3
OCR Text

LEVEL 4
Normalized Text

LEVEL 5
Structured Passage

LEVEL 6
Semantic Chunk

LEVEL 7
Embedding

LEVEL 8
AI Interpretation
```

**AI tidak boleh menjadi sumber primer.**

---

# 34.3 Corpus Object

Tambahkan entity:

```text
Corpus
 ├── Work
 ├── Edition
 ├── Volume
 ├── Page
 ├── Passage
 ├── Chunk
 ├── OCR
 └── Fingerprint
```

Contoh:

```text
Corpus
└── Fath al-Bari
    └── Edition X
        ├── Volume 1
        │   ├── Page 1
        │   ├── Page 2
        │   └── ...
        ├── Volume 2
        └── ...
```

---

# 34.4 Work

```sql
CREATE TABLE scholarly_works (
    id UUID PRIMARY KEY,

    title_ar TEXT NOT NULL,
    title_id TEXT,

    author TEXT NOT NULL,

    work_type VARCHAR(50),

    description TEXT,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Contoh:

```json
{
  "title_ar": "فتح الباري شرح صحيح البخاري",
  "author": "أحمد بن علي بن حجر العسقلاني",
  "work_type": "SHARH"
}
```

---

# 34.5 Edition

Satu kitab dapat memiliki banyak edisi.

```sql
CREATE TABLE scholarly_editions (
    id UUID PRIMARY KEY,

    work_id UUID NOT NULL,

    publisher TEXT,

    editor TEXT,

    edition_number TEXT,

    publication_year INTEGER,

    publication_place TEXT,

    isbn TEXT,

    total_volumes INTEGER,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.6 Mengapa Edition Penting?

Misalnya:

```text
Fathul Bari Edition A
Page 48
```

tidak boleh diasumsikan identik dengan:

```text
Fathul Bari Edition B
Page 48
```

Nomor halaman dapat berbeda.

Karena itu citation harus:

```text
Edition
+
Volume
+
Page
+
Passage
```

---

# 34.7 Edition Fingerprint

Setiap edisi diberi fingerprint:

```text
edition_fingerprint
```

Contoh konsep:

```text
SHA256(
    title
    + publisher
    + editor
    + publication_year
    + volume_count
)
```

Tujuannya untuk:

* identifikasi
* deduplication
* reproducibility

---

# 34.8 Volume Registry

```sql
CREATE TABLE scholarly_volumes (
    id UUID PRIMARY KEY,

    edition_id UUID NOT NULL,

    volume_number INTEGER NOT NULL,

    label TEXT,

    page_count INTEGER,

    file_id UUID,

    checksum TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.9 Source File Registry

Jangan menyimpan metadata file hanya di filesystem.

```sql
CREATE TABLE source_files (
    id UUID PRIMARY KEY,

    filename TEXT NOT NULL,

    mime_type TEXT,

    file_size BIGINT,

    checksum_sha256 TEXT,

    storage_path TEXT,

    storage_provider TEXT,

    uploaded_by UUID,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Contoh:

```text
fathul-bari-vol-01.pdf
SHA256:
a91f...83cd
```

---

# 34.10 Immutable Source

Setelah source resmi masuk:

```text
DO NOT MODIFY
```

Jika file salah:

```text
Old Source
    ↓
Retire
    ↓
New Source
```

bukan overwrite.

---

# 34.11 Source Status

```text
UPLOADED
PROCESSING
OCR_READY
STRUCTURED
VERIFIED
PUBLISHED
RETIRED
REJECTED
```

---

# 34.12 Ingestion Pipeline

Pipeline utama:

```text
UPLOAD
  ↓
VALIDATE
  ↓
HASH
  ↓
REGISTER
  ↓
PAGE SPLIT
  ↓
OCR
  ↓
OCR QUALITY
  ↓
NORMALIZE
  ↓
SEGMENT
  ↓
STRUCTURE
  ↓
MAP HADITH
  ↓
CHUNK
  ↓
INDEX
  ↓
VERIFY
  ↓
PUBLISH
```

---

# 34.13 Ingestion Job

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY,

    source_file_id UUID,

    job_type VARCHAR(50),

    status VARCHAR(30),

    progress INTEGER DEFAULT 0,

    total_units INTEGER,

    processed_units INTEGER DEFAULT 0,

    error_count INTEGER DEFAULT 0,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    metadata JSONB DEFAULT '{}'
);
```

---

# 34.14 Job Types

```text
VALIDATE_FILE
EXTRACT_PAGES
OCR
NORMALIZE
SEGMENT
MAP_STRUCTURE
MAP_HADITH
GENERATE_CHUNKS
GENERATE_EMBEDDINGS
INDEX_SEARCH
QUALITY_CHECK
```

---

# 34.15 Queue Architecture

Jangan menjalankan seluruh pipeline dalam HTTP request.

Gunakan:

```text
API
 ↓
Job Queue
 ↓
Worker
 ↓
Database / Object Storage
```

Contoh:

```text
Redis
+
BullMQ
```

atau equivalent queue infrastructure.

---

# 34.16 Worker Architecture

```text
workers/
├── file-validator
├── pdf-extractor
├── ocr-worker
├── normalizer
├── segmenter
├── hadith-mapper
├── chunker
├── embedding-worker
├── search-indexer
└── quality-worker
```

---

# 34.17 Page Extraction

PDF:

```text
Volume 1
  ↓
Page 1
Page 2
Page 3
...
Page N
```

Setiap page memiliki ID permanen.

```sql
CREATE TABLE source_pages (
    id UUID PRIMARY KEY,

    volume_id UUID NOT NULL,

    page_number INTEGER,

    printed_page_number TEXT,

    image_path TEXT,

    image_checksum TEXT,

    width INTEGER,

    height INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.18 Printed Page vs PDF Page

Ini sangat penting.

PDF:

```text
PDF page 53
```

bisa saja:

```text
Printed page 48
```

Simpan keduanya.

```json
{
  "pdf_page": 53,
  "printed_page": "48"
}
```

---

# 34.19 Page Fingerprint

Setiap halaman:

```text
SHA256(page_image)
```

sehingga halaman dapat diverifikasi.

---

# 34.20 OCR Layer

OCR object:

```sql
CREATE TABLE page_ocr (
    id UUID PRIMARY KEY,

    page_id UUID NOT NULL,

    engine TEXT,

    engine_version TEXT,

    language TEXT,

    raw_text TEXT,

    confidence NUMERIC,

    processing_time_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.21 Jangan Hapus Raw OCR

Simpan:

```text
RAW OCR
```

dan:

```text
NORMALIZED OCR
```

secara terpisah.

```text
raw_text
     ↓
normalized_text
```

---

# 34.22 Arabic OCR Normalization

Normalisasi harus konservatif.

Contoh:

```text
أ
إ
آ
ٱ
```

tidak boleh sembarangan diubah dalam **display text**.

Buat dua versi:

```text
display_text
search_text
```

---

# 34.23 Display Text

Mempertahankan bentuk sedekat mungkin dengan sumber.

```text
قال ابن حجر رحمه الله...
```

---

# 34.24 Search Text

Boleh dinormalisasi untuk retrieval:

```text
قال ابن حجر رحمه الله
```

dengan normalisasi:

* tatweel
* whitespace
* harakat tertentu
* variasi alif
* punctuation

Tetapi jangan mengganti source text.

---

# 34.25 Arabic Normalization Pipeline

```text
RAW
 ↓
Unicode normalization
 ↓
Whitespace normalization
 ↓
Search normalization
 ↓
Tokenization
```

Simpan semua tahap bila diperlukan untuk audit.

---

# 34.26 OCR Error Detection

OCR Arab sangat rawan:

```text
ب ↔ ت ↔ ث
ج ↔ ح ↔ خ
د ↔ ذ
ر ↔ ز
س ↔ ش
ص ↔ ض
ط ↔ ظ
ع ↔ غ
ف ↔ ق
```

Jangan otomatis menganggap hasil OCR benar.

---

# 34.27 OCR Quality Score

Contoh:

```text
OCR Confidence
████████░░ 82%
```

Namun confidence OCR **bukan confidence kebenaran ilmiah**.

Gunakan label:

```text
OCR Confidence
```

bukan:

```text
Text Accuracy
```

---

# 34.28 Page Quality

```text
OCR QUALITY

Character confidence     91%
Language detection       Arabic
Text completeness        96%
Layout confidence         88%

Status: REVIEW RECOMMENDED
```

---

# 34.29 Human OCR Review

Reviewer dapat membuka:

```text
SCAN
   │
   ├── OCR
   │
   └── Corrected Text
```

UI:

```text
┌─────────────────────┬─────────────────────┐
│ SCAN                │ OCR                 │
│                     │                     │
│ [page image]        │ قال ابن حجر...      │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

---

# 34.30 Correction Tracking

Jangan overwrite OCR.

```sql
CREATE TABLE ocr_corrections (
    id UUID PRIMARY KEY,

    page_id UUID,

    original_text TEXT,

    corrected_text TEXT,

    start_offset INTEGER,

    end_offset INTEGER,

    corrected_by UUID,

    reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.31 Segmentation

Setelah OCR:

```text
Page
 ↓
Paragraph
 ↓
Section
 ↓
Commentary
 ↓
Quotation
```

---

# 34.32 Passage Object

```sql
CREATE TABLE source_passages (
    id UUID PRIMARY KEY,

    page_id UUID NOT NULL,

    parent_id UUID,

    passage_type VARCHAR(40),

    sequence_number INTEGER,

    display_text TEXT,

    search_text TEXT,

    start_offset INTEGER,

    end_offset INTEGER,

    verification_status VARCHAR(30),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.33 Passage Types

```text
BODY
HEADER
SUBHEADER
HADITH_QUOTE
QURAN_QUOTE
POETRY
SCHOLAR_QUOTE
FOOTNOTE
MARGIN
EDITOR_NOTE
```

---

# 34.34 Structural Mapping

Fathul Bari harus dipetakan:

```text
Book
 ↓
Kitab
 ↓
Bab
 ↓
Hadith
 ↓
Sharh
```

Contoh:

```text
Kitab al-Iman
    ↓
Bab ...
    ↓
Bukhari #...
    ↓
Fathul Bari commentary
```

---

# 34.35 Hadith Mapping

Buat entity:

```sql
CREATE TABLE hadith_source_mappings (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL,

    passage_id UUID NOT NULL,

    mapping_type VARCHAR(40),

    confidence NUMERIC,

    verified BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.36 Mapping Types

```text
PRIMARY_COMMENTARY
QUOTED_HADITH
PARALLEL_REFERENCE
CROSS_REFERENCE
RELATED_DISCUSSION
```

---

# 34.37 Mapping Strategy

Jangan hanya menggunakan nomor hadis.

Gunakan kombinasi:

```text
Hadith number
+
Kitab
+
Bab
+
Matn fingerprint
+
Arabic similarity
+
Local context
```

---

# 34.38 Hadith Fingerprint

Buat:

```text
matn_fingerprint
```

berdasarkan normalized matn.

Contoh:

```text
SHA256(normalized_matn)
```

Ini membantu mengidentifikasi hadis meskipun numbering berbeda.

---

# 34.39 Passage Fingerprint

```text
passage_fingerprint
```

berdasarkan:

```text
edition
volume
page
normalized_text
```

---

# 34.40 Duplicate Detection

Jika source sama diupload dua kali:

```text
File A
SHA256 = X

File B
SHA256 = X
```

hasil:

```text
DUPLICATE
```

Jangan melakukan OCR ulang.

---

# 34.41 Near Duplicate

Jika:

```text
File A ≠ File B
```

tetapi:

```text
99.8% similar
```

tandai:

```text
POSSIBLE_DUPLICATE
```

---

# 34.42 Edition Difference

Jika dua edisi memiliki passage yang mirip:

```text
Edition A:
قال ابن حجر...

Edition B:
قال الحافظ ابن حجر...
```

jangan collapse menjadi satu source.

Simpan:

```text
Variant A
Variant B
```

---

# 34.43 Textual Variant Model

```sql
CREATE TABLE textual_variants (
    id UUID PRIMARY KEY,

    passage_a UUID,

    passage_b UUID,

    variant_type VARCHAR(40),

    difference TEXT,

    verified BOOLEAN DEFAULT FALSE
);
```

---

# 34.44 Variant Types

```text
WORD_ADDED
WORD_REMOVED
WORD_CHANGED
ORDER_CHANGED
ORTHOGRAPHIC
PUNCTUATION
UNKNOWN
```

---

# 34.45 Semantic Chunking

Jangan chunk berdasarkan:

```text
1000 characters
```

semata.

Lebih baik:

```text
Paragraph
+
semantic boundary
+
hadith context
```

---

# 34.46 Chunk Object

```sql
CREATE TABLE source_chunks (
    id UUID PRIMARY KEY,

    passage_id UUID NOT NULL,

    chunk_index INTEGER,

    text TEXT,

    token_count INTEGER,

    chunk_type VARCHAR(40),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.47 Chunk Metadata

```json
{
  "work": "Fath al-Bari",
  "edition": "edition-x",
  "volume": 1,
  "page": 48,
  "hadith_id": "H001",
  "kitab": "...",
  "bab": "...",
  "passage_type": "BODY"
}
```

---

# 34.48 RAG Metadata

Metadata harus ikut embedding.

```text
work
edition
volume
page
hadith
kitab
bab
author
passage_type
verification_status
```

Ini memungkinkan:

> "Cari hanya Fathul Bari volume 3."

---

# 34.49 Vector Index

Pipeline:

```text
Chunk
 ↓
Embedding
 ↓
Vector DB
```

Simpan:

```text
embedding_model
embedding_version
chunk_id
```

---

# 34.50 Embedding Version

Jika model diganti:

```text
Embedding v1
```

menjadi:

```text
Embedding v2
```

jangan overwrite tanpa versioning.

---

# 34.51 Search Index

Gunakan hybrid search:

```text
BM25
+
Vector Search
+
Metadata Filter
```

Formula konseptual:

```text
Final Score =
0.40 lexical
+
0.40 semantic
+
0.10 metadata
+
0.10 source quality
```

Bobot dapat dikonfigurasi melalui evaluation.

---

# 34.52 Exact Search

Untuk hadis dan kitab, exact search sangat penting.

Query:

```text
إنما الأعمال بالنيات
```

harus dapat menemukan exact passage walaupun semantic search gagal.

---

# 34.53 Search Result

```text
Fathul Bari
Vol. 1
p. 48

... إنما الأعمال بالنيات ...

✓ Verified
Source: Edition X
```

---

# 34.54 Source Quality Score

Buat:

```text
source_quality_score
```

berdasarkan:

```text
scan available
OCR quality
human verified
edition metadata complete
page mapping complete
```

Bukan berdasarkan "AI confidence".

---

# 34.55 Corpus Quality Dashboard

Admin:

```text
FATHUL BARI CORPUS

Volumes                 13
Pages                7,842
Passages             42,891
Hadith mappings       3,102
Verified pages        87%
OCR reviewed          79%
Indexed              100%

Problems:
⚠ 42 pages low OCR
⚠ 17 unmapped passages
⚠ 9 duplicate candidates
```

---

# 34.56 Ingestion Dashboard

```text
┌──────────────────────────────────────────────┐
│ INGESTION JOB #104                          │
├──────────────────────────────────────────────┤
│ File: Fathul-Bari-v01.pdf                   │
│                                              │
│ Validate          ✓                         │
│ Page extraction   ✓                         │
│ OCR               █████████░ 91%            │
│ Normalize         ███████░░░ 72%            │
│ Segment           ███░░░░░░░ 34%            │
│ Mapping           ░░░░░░░░░░ 0%             │
└──────────────────────────────────────────────┘
```

---

# 34.57 Error Queue

Jika OCR gagal:

```text
ERROR QUEUE
```

contoh:

```text
Page 183
OCR failed

Reason:
low image quality

[Retry]
[Manual OCR]
[Mark Unusable]
```

---

# 34.58 Dead Letter Queue

Job yang gagal berulang kali:

```text
Worker
 ↓
Retry 1
 ↓
Retry 2
 ↓
Retry 3
 ↓
Dead Letter Queue
```

Jangan terus retry tanpa batas.

---

# 34.59 Ingestion Audit Trail

Setiap transformasi:

```text
UPLOAD
 ↓
OCR
 ↓
NORMALIZE
 ↓
CORRECT
 ↓
SEGMENT
 ↓
MAP
```

harus masuk audit trail.

```sql
CREATE TABLE corpus_audit_events (
    id UUID PRIMARY KEY,

    source_id UUID,

    event_type VARCHAR(50),

    actor_type VARCHAR(30),

    actor_id UUID,

    old_value JSONB,

    new_value JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 34.60 Actor Types

```text
SYSTEM
WORKER
AI
HUMAN
ADMIN
```

---

# 34.61 AI-Corrected Text

Jika AI mengusulkan koreksi OCR:

```text
AI SUGGESTION
```

bukan:

```text
VERIFIED TEXT
```

Workflow:

```text
AI Suggestion
      ↓
Human Review
      ↓
Accept / Reject
      ↓
Verified Correction
```

---

# 34.62 Human Review Queue

```text
REVIEW QUEUE

[ ] Page 182
[ ] Page 183
[ ] Page 214
[ ] Page 301
```

Prioritaskan:

```text
low OCR confidence
high retrieval frequency
important hadith
AI citation dependency
```

---

# 34.63 Active Learning

Corpus dapat memperbaiki dirinya secara terkontrol.

Contoh:

```text
AI sering salah membaca:
"الحافظ"

Human corrections:
20 occurrences

↓
Create OCR correction pattern

↓
Apply candidate suggestions
```

Tetap membutuhkan human approval.

---

# 34.64 Corpus Release

Corpus jangan langsung dianggap production.

Gunakan:

```text
DRAFT
 ↓
QA
 ↓
REVIEW
 ↓
RELEASE CANDIDATE
 ↓
PUBLISHED
```

---

# 34.65 Corpus Version

Contoh:

```text
Fathul Bari Corpus v1.0
```

Kemudian:

```text
v1.1
```

jika:

* OCR diperbaiki
* mapping diperbaiki
* metadata ditambahkan

---

# 34.66 Reproducibility

Setiap RAG answer dapat mengatakan:

```text
Corpus:
Fathul Bari Corpus v1.2

Edition:
Edition X

Indexed:
2026-08-13
```

Ini sangat penting untuk penelitian.

---

# 34.67 Corpus Manifest

Buat file:

```text
corpus-manifest.json
```

contoh:

```json
{
  "corpus": "fath-al-bari",
  "version": "1.0.0",
  "work": "فتح الباري شرح صحيح البخاري",
  "author": "ابن حجر العسقلاني",
  "volumes": 13,
  "pages": 7842,
  "generated_at": "2026-08-13",
  "pipeline_version": "34.0"
}
```

---

# 34.68 Data Lineage

Diagram:

```text
SOURCE PDF
    │
    ▼
SOURCE FILE
    │
    ▼
PAGE
    │
    ▼
OCR
    │
    ▼
NORMALIZED TEXT
    │
    ▼
PASSAGE
    │
    ▼
CHUNK
    │
    ├────► SEARCH INDEX
    │
    └────► VECTOR INDEX
               │
               ▼
              RAG
               │
               ▼
             CLAIM
               │
               ▼
            EVIDENCE
```

---

# 34.69 Critical Rule

**Jangan pernah menyimpan hanya embedding.**

Harus selalu:

```text
Embedding
   ↓
Chunk
   ↓
Passage
   ↓
Page
   ↓
Scan
```

Dengan demikian setiap jawaban AI dapat kembali ke sumber visual.

---

# 34.70 RAG Citation Chain

Saat AI menghasilkan:

```text
Ibn Hajar explains X.
```

backend harus mampu menghasilkan:

```json
{
  "claim": "Ibn Hajar explains X",

  "evidence": {
    "chunk_id": "C123"
  },

  "source": {
    "work": "Fath al-Bari",
    "edition": "E01",
    "volume": 1,
    "page": 48,
    "passage_id": "P889"
  },

  "scan": {
    "page_id": "PG998"
  }
}
```

---

# 34.71 Source Viewer Integration

Klik citation:

```text
AI Answer
    ↓
Evidence
    ↓
Passage
    ↓
Page
    ↓
Scan
```

Source Viewer Stage 33 langsung membuka halaman terkait.

---

# 34.72 API Ingestion

Tambahkan:

```http
POST /api/v1/corpus/works
POST /api/v1/corpus/editions
POST /api/v1/corpus/volumes
POST /api/v1/corpus/files
POST /api/v1/corpus/ingest
GET  /api/v1/corpus/jobs/{id}
GET  /api/v1/corpus/pages/{id}
GET  /api/v1/corpus/passages/{id}
```

---

# 34.73 Ingest Request

```json
{
  "file_id": "FILE-001",
  "work_id": "WORK-FB",
  "edition_id": "ED-001",

  "options": {
    "ocr": true,
    "normalize": true,
    "segment": true,
    "map_hadith": true,
    "generate_embeddings": true
  }
}
```

---

# 34.74 Ingestion Result

```json
{
  "job_id": "JOB-001",
  "status": "PROCESSING",

  "pipeline": {
    "pages": 620,
    "ocr": 620,
    "segments": 3421,
    "chunks": 5812
  }
}
```

---

# 34.75 Database Relationship

```text
scholarly_works
       │
       ▼
scholarly_editions
       │
       ▼
scholarly_volumes
       │
       ▼
source_pages
       │
       ├── page_ocr
       │
       └── source_passages
                │
                ▼
          source_chunks
                │
          ┌─────┴─────┐
          ▼           ▼
      search index  vector index
```

---

# 34.76 Storage Architecture

Pisahkan:

```text
PostgreSQL
    ↓
Metadata

Object Storage
    ↓
PDF
Images
OCR artifacts

Search Engine
    ↓
BM25

Vector DB
    ↓
Embeddings
```

---

# 34.77 Object Storage Structure

```text
corpus/
└── fathul-bari/
    └── edition-001/
        ├── original/
        ├── pages/
        ├── thumbnails/
        ├── ocr/
        └── exports/
```

---

# 34.78 Thumbnail Generation

Untuk Source Viewer:

```text
Original scan
    ↓
Thumbnail
    ↓
Preview
```

Jangan mengirim PDF besar untuk setiap navigasi page.

---

# 34.79 Page Image API

```http
GET /api/v1/source-pages/{id}/image
GET /api/v1/source-pages/{id}/thumbnail
```

---

# 34.80 Security

Source files dapat memiliki pembatasan akses.

Gunakan:

```text
signed URLs
short expiration
authorization check
```

Jangan memberikan public bucket secara default.

---

# 34.81 Copyright / Provenance Metadata

Setiap source:

```json
{
  "source_type": "DIGITAL_SCAN",
  "rights_status": "UNKNOWN",
  "provenance": "...",
  "access_url": "...",
  "license": "..."
}
```

Jangan menganggap semua PDF kitab bebas digunakan hanya karena tersedia online.

---

# 34.82 Corpus Validation Rules

Pipeline harus menolak:

```text
volume_number = null
page_number = null
empty OCR
duplicate checksum
invalid PDF
```

dan memberi warning untuk:

```text
low OCR confidence
missing printed page number
unmapped hadith
```

---

# 34.83 Automated QA

Setelah ingestion:

```text
✓ Volume continuity
✓ Page continuity
✓ Duplicate detection
✓ Empty page detection
✓ OCR confidence
✓ Arabic language detection
✓ Passage segmentation
✓ Hadith mapping
✓ Metadata completeness
```

---

# 34.84 QA Report

```text
CORPUS QA REPORT

Pages:
7,842

Passed:
7,716

Warnings:
117

Failed:
9

Critical:
0
```

---

# 34.85 Release Gate

Corpus hanya dapat dipublish jika:

```text
Critical errors = 0

AND

Failed pages < threshold

AND

Metadata completeness > threshold
```

Contoh:

```text
Metadata ≥ 98%
OCR usable ≥ 99%
Critical = 0
```

---

# 34.86 Admin Corpus Browser

```text
Corpus
├── Works
├── Editions
├── Volumes
├── Pages
├── OCR
├── Passages
├── Hadith Mapping
├── Variants
├── Jobs
├── QA
└── Releases
```

---

# 34.87 Page Review Screen

```text
┌──────────────────────────────────────────────────┐
│ Volume 1 / Page 48                               │
├──────────────────────┬───────────────────────────┤
│ SCAN                 │ OCR                       │
│                      │                           │
│ [IMAGE]              │ النص ...                 │
│                      │                           │
├──────────────────────┴───────────────────────────┤
│ OCR Confidence: 91%                              │
│ Mapping: Hadith #1                                │
│ Status: REVIEWED                                  │
├──────────────────────────────────────────────────┤
│ [Accept] [Correct] [Reject] [Previous] [Next]   │
└──────────────────────────────────────────────────┘
```

---

# 34.88 Hadith Mapping Review

```text
Fathul Bari Passage

Suggested:
Bukhari #1

Similarity:
96.4%

Evidence:
Kitab al-Bada' al-Wahy
Bab ...
Matn fingerprint match

[Accept]
[Reject]
[Search Manually]
```

---

# 34.89 Manual Mapping

Jika AI gagal:

```text
[Search Hadith]

Query:
إنما الأعمال بالنيات

Results:
Bukhari #1
Muslim #1907
...
```

Reviewer memilih:

```text
[Map]
```

---

# 34.90 Mapping Confidence

Gunakan:

```text
AUTO_MATCH
REVIEW_REQUIRED
HUMAN_VERIFIED
REJECTED
```

bukan sekadar angka.

---

# 34.91 Corpus-to-Knowledge Graph

Setelah corpus valid:

```text
Fathul Bari Passage
        │
        ├── discusses → Hadith
        ├── quotes → Quran
        ├── cites → Scholar
        ├── references → Book
        └── discusses → Concept
```

Dengan demikian Stage 9 Knowledge Graph mendapatkan source evidence yang jauh lebih kuat.

---

# 34.92 Corpus-to-RAG

```text
Verified Passage
       ↓
Chunk
       ↓
Embedding
       ↓
Vector Search
       ↓
Reranking
       ↓
Evidence Selection
       ↓
AI
```

**Bukan:**

```text
PDF → AI
```

---

# 34.93 Corpus-to-Review Dashboard

Review Dashboard Stage sebelumnya sekarang mendapat:

```text
Hadith
↓
Fathul Bari passage
↓
Page
↓
Scan
↓
OCR confidence
↓
Human verification
```

Jadi reviewer dapat memeriksa sumber tanpa berpindah aplikasi.

---

# 34.94 Performance Strategy

Untuk corpus besar:

```text
Never:
PDF → OCR → RAG at request time
```

Gunakan preprocessing:

```text
Offline ingestion
       ↓
Precomputed artifacts
       ↓
Fast runtime retrieval
```

---

# 34.95 Caching

Cache:

```text
page metadata
passage
search results
embedding
source image
```

Tetapi jangan cache data yang memiliki permission berbeda tanpa key authorization.

---

# 34.96 Observability

Tambahkan metrics:

```text
ingestion_jobs_total
ocr_pages_total
ocr_failures_total
mapping_success_total
mapping_review_total
embedding_jobs_total
indexing_failures_total
```

---

# 34.97 Monitoring Dashboard

```text
Corpus Pipeline

OCR throughput:
120 pages/min

Failed OCR:
0.8%

Mapping:
94.2%

Embedding:
98.7%

Index:
100%
```

---

# 34.98 Testing Strategy

### Unit Test

```text
Arabic normalization
fingerprinting
page numbering
chunking
metadata validation
```

### Integration Test

```text
PDF
→ OCR
→ Passage
→ Chunk
→ Index
```

### Golden Test

Gunakan sejumlah halaman yang telah diverifikasi manusia.

```text
Expected OCR
vs
Generated OCR
```

---

# 34.99 Golden Corpus

Buat subset:

```text
tests/corpus/golden/
```

Misalnya:

```text
volume-01-page-001
volume-01-page-048
volume-02-page-100
...
```

Setiap release pipeline harus melewati golden corpus.

---

# 34.100 Definition of Done

Stage 34 dianggap selesai jika:

```text
[ ] Work registry
[ ] Edition registry
[ ] Volume registry
[ ] Source file registry
[ ] SHA256 checksums
[ ] Page extraction
[ ] Page numbering
[ ] Scan storage
[ ] OCR pipeline
[ ] Raw OCR preservation
[ ] Arabic normalization
[ ] Passage segmentation
[ ] Hadith mapping
[ ] Hadith fingerprint
[ ] Passage fingerprint
[ ] Duplicate detection
[ ] Edition comparison
[ ] Textual variants
[ ] Semantic chunking
[ ] Search indexing
[ ] Vector indexing
[ ] Ingestion queue
[ ] Worker architecture
[ ] Retry system
[ ] Dead-letter queue
[ ] OCR review
[ ] Human correction
[ ] QA dashboard
[ ] Corpus release versioning
[ ] Manifest
[ ] Audit trail
[ ] Data lineage
[ ] Source provenance
[ ] Permission system
[ ] Source viewer integration
[ ] RAG integration
[ ] Knowledge graph integration
[ ] Golden corpus tests
```

---

# Arsitektur Setelah Stage 34

Sekarang sistem kita menjadi jauh lebih kokoh:

```text
                         ┌───────────────────────┐
                         │   RESEARCH WORKSPACE  │
                         │      STAGE 33         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │       AI / RAG LAYER            │
                    │                                 │
                    │ Retrieval → Rerank → Evidence  │
                    │ → Reasoning → Citation         │
                    └───────────────┬────────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
             Vector DB         Search Index      Knowledge Graph
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                    ┌────────────────────────────────┐
                    │      STRUCTURED CORPUS         │
                    │          STAGE 34               │
                    │                                 │
                    │ Passage → Page → Volume        │
                    │ → Edition → Work               │
                    └───────────────┬────────────────┘
                                    │
                                    ▼
                    ┌────────────────────────────────┐
                    │       SOURCE INGESTION          │
                    │                                 │
                    │ PDF → Scan → OCR → Normalize   │
                    │ → Segment → Map → Verify       │
                    └───────────────┬────────────────┘
                                    │
                                    ▼
                    ┌────────────────────────────────┐
                    │       PRIMARY SOURCES           │
                    │                                 │
                    │ Fathul Bari                    │
                    │ Hadith Corpus                  │
                    │ Ahmad Sanusi Hadits API        │
                    │ Other verified sources          │
                    └────────────────────────────────┘
```

## Titik penting setelah Stage 34

Dengan arsitektur ini, aplikasi tidak lagi sekadar **"chatbot yang tahu Fathul Bari"**.

Ia mulai menjadi:

> **Scholarly Hadith Research Platform dengan source-level provenance.**

Artinya, ketika AI menghasilkan sebuah penjelasan, jalurnya dapat ditelusuri:

```text
AI Answer
   ↓
Claim
   ↓
Evidence
   ↓
Fathul Bari Passage
   ↓
Page
   ↓
Volume
   ↓
Edition
   ↓
Original Scan
```

Dan jalur sebaliknya juga tersedia:

```text
Scan
 ↓
OCR
 ↓
Passage
 ↓
Hadith
 ↓
Knowledge Graph
 ↓
RAG
 ↓
Research Claim
```
