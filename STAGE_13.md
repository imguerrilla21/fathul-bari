**Stage 13 — Data Ingestion & Corpus Building**. Ini adalah tahap yang sangat penting karena seluruh fitur sebelumnya akan bergantung pada kualitas korpus **Fathul Bari** yang masuk ke sistem.

Target akhirnya:

```text
PDF Fathul Bari
      ↓
File Validation
      ↓
OCR / Text Extraction
      ↓
Arabic Normalization
      ↓
Page Reconstruction
      ↓
Section / Chapter Detection
      ↓
Hadith Detection
      ↓
Hadith ↔ Sharh Matching
      ↓
Chunking
      ↓
Embedding
      ↓
Full-Text Index
      ↓
Knowledge Graph
      ↓
Review Queue
      ↓
VERIFIED CORPUS
```

# Stage 13 — Data Ingestion & Corpus Building

## 13.1 Prinsip utama

Untuk aplikasi kita, **jangan memasukkan PDF langsung ke vector database**.

Kita harus mempertahankan tiga lapisan:

```text
                 ORIGINAL SOURCE
                       │
                       ▼
                EXTRACTED TEXT
                       │
                       ▼
              NORMALIZED TEXT
                       │
                       ▼
              SEARCH / RAG INDEX
```

Dengan demikian jika suatu saat hasil OCR salah, kita masih bisa kembali ke sumber asli.

---

# 13.2 Corpus Architecture

Struktur data:

```text
Corpus
│
├── Work
│    └── Fathul Bari
│
├── Edition
│    └── Edition A
│
├── Volume
│    ├── Volume 01
│    ├── Volume 02
│    └── ...
│
├── Source Document
│    └── PDF
│
├── Page
│
├── Section
│
├── Hadith Reference
│
├── Text Block
│
├── Chunk
│
└── Embedding
```

---

# 13.3 Source Document

Buat tabel:

```sql
source_documents
```

Field utama:

```text
id
work_id
edition_id
volume_id
filename
object_key
mime_type
file_size
sha256
page_count
language
extraction_status
ocr_status
created_at
updated_at
```

Contoh:

```json
{
  "filename": "fathul_bari_vol_01.pdf",
  "volume": 1,
  "page_count": 520,
  "language": "ar",
  "sha256": "...",
  "ocr_status": "pending"
}
```

---

# 13.4 File Validation

Sebelum OCR:

```text
Upload PDF
    ↓
Check MIME
    ↓
Check file size
    ↓
Check PDF validity
    ↓
Calculate SHA-256
    ↓
Check duplicate
    ↓
Accept
```

Jika checksum sama:

```text
SHA256 A
   =
SHA256 B
```

maka jangan melakukan OCR ulang.

Status:

```text
DUPLICATE_SOURCE
```

---

# 13.5 Page Extraction

Setiap halaman harus menjadi entity tersendiri.

```text
source_document
      │
      ├── page 1
      ├── page 2
      ├── page 3
      └── ...
```

Tabel:

```sql
source_pages
```

Field:

```text
id
source_document_id
pdf_page_number
printed_page_number
image_object_key
raw_text
ocr_text
ocr_confidence
status
```

**PDF page number dan printed page number jangan pernah digabung.**

---

# 13.6 OCR Pipeline

Untuk halaman scan:

```text
PDF
 ↓
Render Page
 ↓
Image preprocessing
 ↓
Arabic OCR
 ↓
Raw OCR
 ↓
Text QA
 ↓
Normalized Arabic
```

Pipeline:

```text
PDF page
   ↓
300 DPI image
   ↓
deskew
   ↓
denoise
   ↓
crop margins
   ↓
OCR
```

Untuk PDF yang sudah memiliki text layer:

```text
PDF
 ↓
Text extraction
 ↓
QA
 ↓
OCR hanya jika diperlukan
```

Jadi kita tidak melakukan OCR secara membabi buta.

---

# 13.7 OCR Confidence

Simpan:

```text
ocr_confidence
```

Misalnya:

```text
0.98 → sangat baik
0.90 → baik
0.75 → perlu review
<0.75 → manual review
```

Tetapi jangan menganggap angka OCR sebagai kebenaran. Untuk teks Arab, layout kitab, harakat, footnote, dan kolom dapat menyebabkan confidence misleading.

---

# 13.8 Arabic Normalization

Ini bagian kritis.

Buat dua versi:

```text
raw_text
normalized_text
```

Contoh:

```text
RAW
│
├── mempertahankan teks sedekat mungkin dengan sumber
│
└── untuk citation / source viewer
```

Sedangkan:

```text
NORMALIZED
│
├── normalisasi Unicode
├── variasi alif
├── variasi ya
├── variasi hamzah
└── whitespace
```

Jangan mengganti raw source dengan normalized text.

---

# 13.9 Dual Representation

Kita akan memiliki:

```text
                    PAGE
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
      RAW TEXT            NORMALIZED TEXT
          │                     │
          │                     ├── Search
          │                     ├── Matching
          │                     └── Embedding
          │
          └── Citation
              Source Viewer
              Audit
```

Ini sangat penting untuk menjaga integritas sumber.

---

# 13.10 Layout Reconstruction

Fathul Bari bukan teks linear sederhana.

Satu halaman dapat memiliki:

```text
┌──────────────────────────────┐
│ Header                       │
│                              │
│ Main text                    │
│                              │
│ ─────────────                │
│ Footnote                     │
│                              │
│ Page number                  │
└──────────────────────────────┘
```

OCR harus membedakan:

```text
MAIN_TEXT
HEADER
FOOTNOTE
PAGE_NUMBER
MARGIN_NOTE
```

Jangan memasukkan semuanya sebagai satu string.

---

# 13.11 Text Blocks

Buat:

```sql
text_blocks
```

Schema:

```text
id
page_id
block_type
sequence
bbox
raw_text
normalized_text
confidence
```

`bbox`:

```json
{
  "x": 120,
  "y": 240,
  "width": 850,
  "height": 300
}
```

Dengan ini Source Viewer nanti dapat menyorot **teks yang benar-benar dikutip**.

---

# 13.12 Section Detection

Kita harus menemukan struktur:

```text
كتاب
  ↓
باب
  ↓
Hadith
  ↓
شرح
```

Misalnya:

```text
كتاب بدء الوحي
        │
        ▼
باب كيف كان بدء الوحي
        │
        ▼
حديث رقم 1
        │
        ▼
شرح الحافظ ابن حجر
```

Buat entity:

```text
books
chapters
sections
```

---

# 13.13 Section Hierarchy

Gunakan tree:

```text
Fathul Bari
│
├── Kitab
│   │
│   ├── Bab
│   │   │
│   │   ├── Hadith
│   │   │
│   │   └── Sharh
│   │
│   └── Bab
│
└── Kitab
```

Setiap section:

```text
parent_section_id
```

sehingga hierarchy tidak hilang.

---

# 13.14 Hadith Detection

Ini bagian yang sangat penting.

Kita tidak boleh hanya mencari:

```text
رقم 1
```

karena format kitab bisa berbeda.

Gunakan beberapa signal:

```text
Hadith number
Arabic matn
Chapter context
Narrator pattern
Collection metadata
Existing Hadith API
```

Pipeline:

```text
Fathul Bari text
      ↓
Candidate hadith reference
      ↓
Normalize number
      ↓
Search Ahmad Sanusi API
      ↓
Compare text
      ↓
Confidence
```

---

# 13.15 Ahmad Sanusi Hadits API Integration

Karena aplikasi kita memang menggunakan **Ahmad Sanusi Hadits API**, API tersebut kita tempatkan sebagai **hadith metadata/reference layer**, bukan menggantikan sumber Fathul Bari.

Arsitektur:

```text
                 AHMAD SANUSI API
                       │
                       ▼
                HADITH DATABASE
                       │
                       │ matching
                       ▼
                FATHUL BARI
                       │
                       ▼
                 SHARH SECTION
```

Dengan demikian:

```text
Hadith API
    =
identifikasi hadis

Fathul Bari PDF
    =
sumber syarah
```

Ini pemisahan yang sangat sehat secara data.

---

# 13.16 Hadith Matching

Gunakan:

```text
Exact reference
       +
Arabic similarity
       +
Chapter similarity
       +
Narrator similarity
```

Contoh score:

```text
reference_score      1.00
text_similarity      0.94
chapter_similarity   0.91
narrator_similarity  0.97
```

Kemudian:

```text
final_score = weighted combination
```

Tetapi threshold harus dikalibrasi dengan dataset nyata.

---

# 13.17 Matching Status

Setiap hubungan:

```text
CANDIDATE
AUTO_MATCHED
REVIEW_REQUIRED
VERIFIED
REJECTED
```

Pipeline:

```text
Candidate
   │
   ▼
Auto Matcher
   │
   ├── high confidence ──► REVIEW
   │
   ├── medium ────────────► REVIEW
   │
   └── low ───────────────► REJECT/CANDIDATE
```

**Jangan otomatis menjadikan high confidence sebagai VERIFIED.**

Verified tetap keputusan reviewer.

---

# 13.18 Chunking

Setelah section bersih:

```text
Section
  ↓
Paragraph
  ↓
Semantic chunk
```

Jangan chunk berdasarkan jumlah karakter semata.

Lebih baik:

```text
Hadith context
+
Sharh paragraph
+
Related explanation
```

Tetapi tetap menjaga batas halaman.

---

# 13.19 Chunk Metadata

Setiap chunk:

```json
{
  "id": "...",
  "section_id": "...",
  "page_id": "...",
  "volume": 1,
  "pdf_page": 45,
  "printed_page": 12,
  "chunk_index": 3,
  "text": "...",
  "language": "ar"
}
```

Metadata ini nantinya menjadi dasar citation RAG.

---

# 13.20 Jangan Kehilangkan Page Boundary

Misalnya chunk:

```text
Page 45
   ↓
Page 46
```

Sebaiknya:

```text
chunk A → page 45
chunk B → page 46
```

Jika memang diperlukan overlap:

```text
chunk A
primary_page = 45

chunk B
primary_page = 46
```

Jangan membuat citation ambigu.

---

# 13.21 Embedding Pipeline

Setelah chunk:

```text
Chunk
 ↓
Embedding Model
 ↓
Vector
 ↓
pgvector
```

Tabel:

```sql
document_chunks
```

dan:

```sql
chunk_embeddings
```

Atau embedding dapat berada langsung dalam `document_chunks`, tergantung desain database.

Metadata wajib tetap ada.

---

# 13.22 Hybrid Index

Kita gunakan tiga index:

```text
                    SEARCH
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      PostgreSQL    pgvector      Graph
      FTS/BM25      semantic      traversal
```

Kemudian:

```text
Hybrid Retriever
      ↓
Candidate results
      ↓
Reranker
      ↓
Evidence
```

---

# 13.23 Knowledge Graph Builder

Setelah matching:

```text
Hadith
   │
   ├── EXPLAINED_BY
   │
   ▼
Sharh Section
   │
   ├── LOCATED_IN
   ▼
Source Page
```

Kemudian:

```text
Sharh
   │
   └── BELONGS_TO
           ↓
         Chapter
```

Graph dibangun dari **verified relationships**, sedangkan candidate relationships masuk queue review.

---

# 13.24 Ingestion Job

Satu volume menjadi satu job:

```text
IMPORT_VOLUME
```

Contoh:

```json
{
  "job_id": "...",
  "source_document_id": "...",
  "volume": 1,
  "status": "running",
  "progress": 42
}
```

Stages:

```text
VALIDATE
EXTRACT
OCR
NORMALIZE
SEGMENT
DETECT_HADITH
MATCH
CHUNK
EMBED
INDEX
GRAPH
QA
```

---

# 13.25 Pipeline State Machine

```text
UPLOADED
   ↓
VALIDATED
   ↓
EXTRACTED
   ↓
OCR_COMPLETE
   ↓
NORMALIZED
   ↓
SEGMENTED
   ↓
HADITH_MAPPED
   ↓
CHUNKED
   ↓
EMBEDDED
   ↓
INDEXED
   ↓
GRAPH_BUILT
   ↓
QA_COMPLETE
```

Jika error:

```text
FAILED
```

dan job dapat di-resume dari checkpoint.

---

# 13.26 Idempotency

Ini sangat penting.

Jika worker mati pada:

```text
EMBEDDED
```

kita tidak boleh mengulang:

```text
OCR
Normalization
Chunking
```

dari awal.

Gunakan:

```text
document_id
page_id
content_hash
pipeline_version
```

Sebagai identity.

---

# 13.27 Pipeline Version

Setiap processing menyimpan:

```text
ocr_version
normalization_version
segmentation_version
matching_version
embedding_version
```

Contoh:

```json
{
  "ocr_version": "ocr-1.2",
  "normalization_version": "arabic-normalizer-1.1",
  "matching_version": "hadith-matcher-2.0",
  "embedding_version": "embed-1.0"
}
```

Jika algoritma berubah, kita bisa melakukan reprocessing secara terkontrol.

---

# 13.28 Data Quality Gate

Sebelum corpus masuk production:

```text
              QA GATE
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
 OCR Quality  Structure   Mapping
      │          │          │
      └──────────┼──────────┘
                 ▼
             PASS / FAIL
```

Contoh:

```text
OCR coverage             ≥ 98%
Pages extracted          = 100%
Duplicate pages          = 0
Broken pages             = 0
Valid metadata           ≥ 99%
```

Threshold tersebut adalah **target awal**, bukan angka universal.

---

# 13.29 Corpus Manifest

Setiap volume memiliki manifest:

```json
{
  "work": "Fathul Bari",
  "edition": "edition-001",
  "volume": 1,
  "source_sha256": "...",
  "pages": 520,
  "processed_pages": 520,
  "sections": 43,
  "hadith_candidates": 612,
  "verified_links": 584,
  "chunks": 4210,
  "embeddings": 4210,
  "pipeline_version": "13.0"
}
```

Manifest ini sangat berguna untuk reproducibility.

---

# 13.30 Admin Ingestion UI

Buat halaman:

```text
/admin/ingestion
```

UI:

```text
┌────────────────────────────────────────────────────────────┐
│ CORPUS INGESTION                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Work       [ Fathul Bari                 ]                 │
│ Edition    [ Edition 001                 ]                 │
│ Volume     [ 01                          ]                 │
│ File       [ fathul-bari-vol-01.pdf ] [Upload]            │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ PIPELINE                                                   │
│                                                            │
│ ✓ Validation                                               │
│ ✓ Extraction                                               │
│ ✓ OCR                                                      │
│ ✓ Normalization                                            │
│ ● Segmentation                                             │
│ ○ Hadith Mapping                                           │
│ ○ Chunking                                                 │
│ ○ Embedding                                                │
│ ○ Knowledge Graph                                          │
│                                                            │
│ Progress: ████████████░░░░░ 64%                            │
└────────────────────────────────────────────────────────────┘
```

---

# 13.31 Review Queue dari Ingestion

Setelah processing:

```text
/admin/review
```

Prioritas:

```text
┌─────────────────────────────────────────────┐
│ REVIEW QUEUE                                │
├─────────────────────────────────────────────┤
│ 🔴 OCR issue                    21           │
│ 🔴 Hadith mapping conflict      13           │
│ 🟠 Low confidence               84           │
│ 🟡 Missing page reference       17           │
│ 🟡 Possible duplicate           9           │
└─────────────────────────────────────────────┘
```

Reviewer dapat langsung membuka Source Viewer.

---

# 13.32 Source Viewer Integration

Workflow:

```text
Review Item
    ↓
Open
    ↓
Source Viewer
    ↓
PDF page
    +
OCR text
    +
Hadith API text
    +
Matching score
    +
Decision
```

Contoh:

```text
┌───────────────────┬─────────────────────────────┐
│ PDF               │ MATCHING                    │
│                   │                             │
│ [page image]      │ Bukhari #1571               │
│                   │                             │
│                   │ Similarity: 94.2%            │
│                   │                             │
│                   │ [VERIFY] [REJECT]            │
└───────────────────┴─────────────────────────────┘
```

---

# 13.33 Database additions

Stage 13 minimal membutuhkan:

```text
works
editions
volumes

source_documents
source_pages
text_blocks

sections
document_chunks

ingestion_jobs
ingestion_steps

hadith_candidates
hadith_sharh_links

corpus_versions
corpus_manifests
```

---

# 13.34 API Endpoints

### Upload

```http
POST /api/v1/admin/sources
```

### Start ingestion

```http
POST /api/v1/admin/ingestion
```

### Job status

```http
GET /api/v1/admin/ingestion/{job_id}
```

### Page

```http
GET /api/v1/sources/pages/{page_id}
```

### Sections

```http
GET /api/v1/sources/{volume_id}/sections
```

### Candidates

```http
GET /api/v1/matching/candidates
```

### Verify

```http
POST /api/v1/matching/{id}/verify
```

### Reject

```http
POST /api/v1/matching/{id}/reject
```

---

# 13.35 Contoh Pipeline Worker

Secara konseptual:

```python
def ingest_volume(source_document_id):

    validate_source(source_document_id)

    pages = extract_pages(source_document_id)

    for page in pages:
        if page_requires_ocr(page):
            run_ocr(page)

        normalize_page(page)

        detect_text_blocks(page)

    sections = detect_sections(source_document_id)

    hadith_candidates = detect_hadiths(sections)

    matches = match_with_hadith_api(
        hadith_candidates
    )

    chunks = create_semantic_chunks(
        source_document_id
    )

    generate_embeddings(chunks)

    build_search_index(chunks)

    build_verified_graph(matches)

    run_quality_checks(source_document_id)
```

Dalam production, setiap fungsi tersebut sebaiknya menjadi **job/checkpoint terpisah**, bukan satu transaksi besar.

---

# 13.36 Folder Structure

Backend:

```text
backend/
└── app/
    ├── ingestion/
    │   ├── validator.py
    │   ├── extractor.py
    │   ├── ocr.py
    │   ├── normalizer.py
    │   ├── layout.py
    │   ├── section_detector.py
    │   ├── hadith_detector.py
    │   ├── matcher.py
    │   ├── chunker.py
    │   ├── embedder.py
    │   ├── indexer.py
    │   ├── graph_builder.py
    │   └── qa.py
    │
    ├── workers/
    │   ├── ingestion_worker.py
    │   ├── ocr_worker.py
    │   ├── embedding_worker.py
    │   └── graph_worker.py
    │
    └── models/
        ├── source.py
        ├── page.py
        ├── section.py
        ├── chunk.py
        └── ingestion_job.py
```

Frontend:

```text
frontend/
└── app/
    ├── admin/
    │   └── ingestion/
    ├── sources/
    ├── review/
    └── reader/
```

---

# 13.37 Hal yang tidak boleh dilakukan

Ada beberapa anti-pattern yang harus kita hindari.

### ❌ Jangan:

```text
PDF → OCR → LLM → database
```

### ❌ Jangan:

```text
PDF → chunk → embedding
```

tanpa menyimpan page/section provenance.

### ❌ Jangan:

```text
AI menentukan bahwa hadis X pasti berada pada syarah Y
```

tanpa review.

### ❌ Jangan:

```text
normalized text menggantikan raw text
```

### ❌ Jangan:

```text
vector database menjadi source of truth
```

Source of truth tetap:

```text
Original source
+
verified relational metadata
```

---

# 13.38 Target akhir Stage 13

Kita ingin sampai pada kondisi:

```text
Fathul Bari Volume 1
        │
        ▼
     100% pages
        │
        ▼
 OCR / Text Extraction
        │
        ▼
 Arabic Normalization
        │
        ▼
 Sections
        │
        ▼
 Hadith References
        │
        ▼
 Ahmad Sanusi Mapping
        │
        ▼
 Review Queue
        │
        ▼
 Verified Links
        │
        ├───────────────┐
        ▼               ▼
    Knowledge Graph    RAG Index
        │               │
        └───────┬───────┘
                ▼
         Fathul Bari AI
```

---

# 13.39 Definition of Done

Stage 13 selesai apabila:

```text
[ ] Source document dapat di-upload
[ ] SHA-256 tersimpan
[ ] Duplicate detection bekerja
[ ] PDF pages terdaftar
[ ] PDF/printed page dipisahkan
[ ] Text extraction bekerja
[ ] OCR fallback bekerja
[ ] Raw text tersimpan
[ ] Normalized text tersimpan
[ ] Text blocks tersimpan
[ ] Section hierarchy terbentuk
[ ] Hadith references terdeteksi
[ ] Ahmad Sanusi API terintegrasi
[ ] Hadith matching bekerja
[ ] Matching confidence tersimpan
[ ] Candidate queue tersedia
[ ] Verified links masuk graph
[ ] Semantic chunks terbentuk
[ ] Embedding dibuat
[ ] Full-text index dibuat
[ ] Vector index dibuat
[ ] Ingestion job resumable
[ ] Pipeline version tersimpan
[ ] Corpus manifest dibuat
[ ] QA report dibuat
```

## Posisi kita sekarang

```text
STAGE 01  Foundation                    ✓
STAGE 02  Ahmad Sanusi API              ✓
STAGE 03  Data Model                    ✓
STAGE 04  Matching Engine               ✓
STAGE 05  Review Dashboard              ✓
STAGE 06  Source + Audit                ✓
STAGE 07  RAG Assistant                 ✓
STAGE 08  Hybrid Search                 ✓
STAGE 09  Knowledge Graph               ✓
STAGE 10  Research Workspace            ✓
STAGE 11  Analytics + Quality Control   ✓
STAGE 12  Production Hardening          ✓
STAGE 13  Corpus Ingestion              ← KITA DI SINI
```
