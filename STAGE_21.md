# Stage 21 — Fathul Bari Corpus Ingestion & Source Viewer

Stage 21 sekarang kita bangun sebagai **fondasi corpus Fathul Bari**. Fokusnya bukan AI terlebih dahulu, tetapi memastikan teks syarah yang masuk ke sistem mempunyai **provenance, nomor volume, halaman sumber, posisi teks, dan hash** sehingga nanti setiap jawaban RAG bisa ditelusuri kembali ke sumber aslinya.

> **Target Stage 21:** PDF/scan → halaman → teks → struktur kitab/bab → chunks → embedding-ready → source viewer → audit-ready.

---

# 21.1 Arsitektur

```text
                 PDF FATHUL BARI
                        │
                        ▼
              ┌───────────────────┐
              │ Document Registry │
              └─────────┬─────────┘
                        │
                        ▼
                Page Extraction
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
         Text Layer            OCR Layer
              │                   │
              └─────────┬─────────┘
                        ▼
                Arabic Normalizer
                        │
                        ▼
                Structure Parser
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
        Kitab          Bab          Hadith Ref
          │             │              │
          └─────────────┼──────────────┘
                        ▼
                  Chunk Builder
                        │
                        ▼
               PostgreSQL + pgvector
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Matching Engine        Source Viewer
             │                     │
             └──────────┬──────────┘
                        ▼
                   RAG Assistant
```

---

# 21.2 Prinsip Utama

Kita harus membedakan tiga hal:

```text
Original Source
     ↓
Extracted Text
     ↓
Normalized/Search Text
```

Jangan hanya menyimpan:

```text
text
```

Tetapi:

```text
original_text
extracted_text
normalized_text
```

Karena:

* `original_text` = evidence yang diekstrak
* `extracted_text` = hasil ekstraksi/OCR
* `normalized_text` = untuk search/matching

---

# 21.3 Document Registry

Tambahkan tabel:

```sql
CREATE TABLE source_documents (
    id UUID PRIMARY KEY,

    title TEXT NOT NULL,
    author TEXT,

    language VARCHAR(20) DEFAULT 'ar',

    edition TEXT,
    publisher TEXT,
    publication_year INTEGER,

    source_type VARCHAR(30) NOT NULL,

    file_name TEXT,
    file_hash VARCHAR(64),

    page_count INTEGER,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Contoh:

```json
{
  "title": "فتح الباري شرح صحيح البخاري",
  "author": "أحمد بن علي بن حجر العسقلاني",
  "language": "ar",
  "source_type": "PDF"
}
```

---

# 21.4 Kenapa File Hash Penting?

Misalnya Anda mempunyai:

```text
fathul-bari-vol01.pdf
```

Hash:

```text
SHA256:
abc123...
```

Kemudian seseorang mengganti PDF dengan edisi lain tetapi namanya sama.

Hash berubah:

```text
abc123...
      ↓
987xyz...
```

Sistem dapat mengetahui bahwa sumber berbeda.

---

# 21.5 Source Edition

Sebaiknya edisi juga menjadi entity tersendiri.

```text
source_documents
        │
        └── edition
```

Karena:

```text
Fathul Bari
Edition A
Volume 1
Page 45
```

belum tentu sama dengan:

```text
Fathul Bari
Edition B
Volume 1
Page 45
```

Oleh karena itu citation harus menyimpan:

```text
edition
volume
page
```

---

# 21.6 Volume

Tambahkan:

```sql
CREATE TABLE source_volumes (
    id UUID PRIMARY KEY,

    document_id UUID NOT NULL
        REFERENCES source_documents(id),

    volume_number INTEGER NOT NULL,

    title TEXT,

    page_count INTEGER,

    metadata JSONB DEFAULT '{}',

    UNIQUE(document_id, volume_number)
);
```

Struktur:

```text
Fathul Bari
 ├── Volume 1
 ├── Volume 2
 ├── Volume 3
 ├── ...
 └── Volume N
```

---

# 21.7 Source Pages

Ini adalah entity penting untuk Source Viewer.

```sql
CREATE TABLE source_pages (
    id UUID PRIMARY KEY,

    volume_id UUID NOT NULL
        REFERENCES source_volumes(id),

    page_number INTEGER NOT NULL,

    pdf_page_number INTEGER,

    printed_page_number INTEGER,

    image_path TEXT,

    extracted_text TEXT,

    ocr_text TEXT,

    normalized_text TEXT,

    extraction_method VARCHAR(30),

    content_hash VARCHAR(64),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(volume_id, page_number)
);
```

---

# 21.8 Dua Nomor Halaman

Kita harus membedakan:

```text
PDF page
```

dan:

```text
Printed page
```

Misalnya:

```text
PDF page = 67
Printed page = 45
```

Citation sebaiknya:

```text
Fathul Bari
Vol. 1
p. 45
PDF page 67
```

Dengan demikian user bisa langsung membuka halaman PDF yang benar.

---

# 21.9 Extraction Method

Simpan:

```text
TEXT_LAYER
OCR
MANUAL
HYBRID
```

Contoh:

```json
{
  "extraction_method": "HYBRID"
}
```

---

# 21.10 OCR Quality

Untuk halaman OCR, simpan:

```sql
ALTER TABLE source_pages
ADD COLUMN ocr_confidence NUMERIC(6,5);
```

Contoh:

```text
0.98
```

atau:

```text
0.61
```

Halaman dengan confidence rendah dapat masuk:

```text
OCR_REVIEW_QUEUE
```

---

# 21.11 Structure Detection

Kita perlu mendeteksi:

```text
كتاب
باب
فصل
حديث
قوله
...
```

Contoh:

```text
كتاب بدء الوحي
        │
        ▼
باب كيف كان بدء الوحي
        │
        ▼
Hadith 1
        │
        ▼
قوله إنما الأعمال بالنيات
```

---

# 21.12 Structural Nodes

Daripada hanya menyimpan `kitab_name`, kita buat struktur:

```sql
CREATE TABLE source_sections (
    id UUID PRIMARY KEY,

    volume_id UUID NOT NULL
        REFERENCES source_volumes(id),

    parent_id UUID REFERENCES source_sections(id),

    section_type VARCHAR(30) NOT NULL,

    title_ar TEXT,

    title_normalized TEXT,

    start_page INTEGER,
    end_page INTEGER,

    start_offset INTEGER,
    end_offset INTEGER,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

`section_type`:

```text
KITAB
BAB
FASL
SUBSECTION
SHARH
OTHER
```

---

# 21.13 Hierarchy

Contoh:

```text
Volume 1
│
├── كتاب بدء الوحي
│   │
│   ├── باب كيف كان بدء الوحي
│   │
│   ├── باب ...
│   │
│   └── باب ...
│
└── كتاب الإيمان
    │
    ├── باب ...
    └── باب ...
```

`parent_id` membuat struktur tersebut mudah dinavigasi.

---

# 21.14 Sharh Chunk

Sekarang entity utama RAG:

```sql
CREATE TABLE sharh_chunks (
    id UUID PRIMARY KEY,

    volume_id UUID NOT NULL
        REFERENCES source_volumes(id),

    section_id UUID REFERENCES source_sections(id),

    page_id UUID REFERENCES source_pages(id),

    chunk_index INTEGER NOT NULL,

    original_text TEXT NOT NULL,

    normalized_text TEXT,

    start_offset INTEGER,
    end_offset INTEGER,

    token_count INTEGER,

    content_hash VARCHAR(64),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(volume_id, chunk_index)
);
```

---

# 21.15 Kenapa Chunk Tidak Boleh Lepas dari Page?

Jangan hanya:

```text
chunk_id
text
```

Harus:

```text
chunk
 ↓
page
 ↓
volume
 ↓
document
```

Sehingga:

```text
AI Answer
 ↓
Evidence
 ↓
Chunk
 ↓
Page
 ↓
PDF
```

---

# 21.16 Chunking Strategy

Untuk Fathul Bari, jangan menggunakan fixed character chunk saja.

Contoh buruk:

```text
every 1,000 characters
```

Karena bisa memotong:

```text
شرح مسألة
```

di tengah pembahasan.

Lebih baik:

```text
section-aware chunking
```

dengan batas:

```text
Kitab
 ↓
Bab
 ↓
Paragraph
 ↓
Sentence
 ↓
Token limit
```

---

# 21.17 Recommended Chunk

Target awal:

```text
600–1,000 Arabic tokens
```

overlap:

```text
80–150 tokens
```

Tetapi chunk harus dihentikan lebih awal jika menemukan boundary semantik.

---

# 21.18 Chunk Boundary

Prioritas:

```text
1. Section boundary
2. Paragraph boundary
3. Sentence boundary
4. Token boundary
```

Jangan:

```text
token boundary
```

menjadi prioritas pertama.

---

# 21.19 Hadith Reference Extraction

Dari syarah:

```text
قوله إنما الأعمال بالنيات
```

sistem mencoba menemukan:

```text
hadith anchor
```

Kemudian:

```text
sharh_chunk
      │
      ▼
hadith_reference
      │
      ▼
Bukhari #1
```

---

# 21.20 Table `sharh_hadith_references`

```sql
CREATE TABLE sharh_hadith_references (
    id UUID PRIMARY KEY,

    sharh_chunk_id UUID NOT NULL
        REFERENCES sharh_chunks(id),

    hadith_id UUID REFERENCES hadiths(id),

    reference_text TEXT,

    reference_type VARCHAR(30),

    confidence NUMERIC(6,5),

    detection_method VARCHAR(30),

    verified BOOLEAN DEFAULT FALSE,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 21.21 Detection Method

```text
EXACT
PATTERN
LEXICAL
SEMANTIC
MANUAL
```

Contoh:

```json
{
  "detection_method": "PATTERN",
  "confidence": 0.91
}
```

---

# 21.22 Embedding

Setelah chunk stabil:

```text
Sharh Chunk
    ↓
Embedding Model
    ↓
Vector
```

Tambahkan:

```sql
ALTER TABLE sharh_chunks
ADD COLUMN embedding vector(1536);
```

**Catatan:** dimensi harus disesuaikan dengan embedding model yang benar-benar dipilih. Jangan mengunci `1536` jika model final menggunakan dimensi berbeda.

Untuk implementasi production, dimensi embedding sebaiknya didefinisikan melalui migration khusus setelah model diputuskan.

---

# 21.23 Vector Index

Dengan pgvector:

```sql
CREATE INDEX sharh_chunks_embedding_idx
ON sharh_chunks
USING hnsw (embedding vector_cosine_ops);
```

Ini memungkinkan:

```text
semantic search
```

langsung di PostgreSQL.

---

# 21.24 Full Text Search

Kita juga membutuhkan lexical search.

Untuk Arabic, kita dapat menyimpan:

```text
normalized_text
```

dan membangun index pencarian yang sesuai.

Untuk tahap awal:

```text
PostgreSQL FTS
+
pgvector
```

sehingga RAG nanti menggunakan:

```text
Hybrid Retrieval
```

bukan embedding saja.

---

# 21.25 Hybrid Search

```text
Query
 │
 ├───────────────┐
 ▼               ▼
Lexical        Vector
Search         Search
 │               │
 └───────┬───────┘
         ▼
      Reranker
         │
         ▼
   Top Evidence
```

Ini sangat penting untuk teks Arab klasik.

---

# 21.26 Source Viewer

Frontend baru:

```text
/research/source/{documentId}/volume/{volume}/page/{page}
```

UI:

```text
┌─────────────────────────────────────────────┐
│ فتح الباري                                  │
│ Volume 1 · Page 45                          │
├───────────────────────┬─────────────────────┤
│                       │                     │
│     PDF PAGE          │ EXTRACTED TEXT     │
│                       │                     │
│     [IMAGE]           │ قوله إنما...       │
│                       │                     │
│                       │                     │
├───────────────────────┴─────────────────────┤
│ Source: Fathul Bari · Vol 1 · p.45          │
│ Extraction: TEXT_LAYER                      │
└─────────────────────────────────────────────┘
```

---

# 21.27 Evidence Highlight

Jika AI menggunakan:

```text
قوله إنما الأعمال بالنيات
```

Source Viewer dapat membuka:

```text
Page 45
```

dan menyorot bagian:

```text
██████████████████████████
قوله إنما الأعمال بالنيات
██████████████████████████
```

---

# 21.28 Citation Object

Kita buat format standar:

```json
{
  "document_id": "...",
  "volume": 1,
  "printed_page": 45,
  "pdf_page": 67,
  "chunk_id": "...",
  "text_hash": "...",
  "source_type": "FATH_AL_BARI"
}
```

Ini nantinya menjadi format citation universal untuk RAG.

---

# 21.29 Citation ID

Setiap evidence diberi:

```text
FB-V1-P45-C003
```

Format:

```text
FB = Fathul Bari
V1 = Volume 1
P45 = Printed Page 45
C003 = Chunk 3
```

Contoh:

```text
[FB-V1-P45-C003]
```

Ini jauh lebih mudah diaudit.

---

# 21.30 Immutable Evidence

Setelah chunk diverifikasi:

```text
original_text
content_hash
source_document
page
```

jangan diubah tanpa versioning.

Jika OCR diperbaiki:

```text
Version 1
    ↓
Version 2
```

bukan overwrite tanpa jejak.

---

# 21.31 Corpus Ingestion Pipeline

Implementasikan:

```text
app/corpus/
├── document_registry.py
├── pdf_reader.py
├── page_extractor.py
├── ocr.py
├── structure_parser.py
├── chunker.py
├── reference_extractor.py
├── embedding.py
└── ingestion.py
```

---

# 21.32 PDF Reader

Interface:

```python
class PDFReader:

    def get_page_count(self, path):
        ...

    def extract_page_text(self, page_number):
        ...

    def render_page(self, page_number):
        ...
```

Jangan mengikat seluruh sistem langsung ke library PDF tertentu.

---

# 21.33 OCR Adapter

```python
class OCRProvider:

    async def recognize(self, image):
        raise NotImplementedError
```

Implementasi dapat diganti:

```text
OCRProvider
   │
   ├── Tesseract
   ├── Cloud OCR
   └── Custom Arabic OCR
```

---

# 21.34 OCR Decision

Pipeline:

```text
PDF page
   │
   ▼
Has text layer?
   │
 ┌─┴─┐
Yes  No
 │    │
 ▼    ▼
Text  OCR
 │    │
 └─┬──┘
   ▼
Quality Check
   │
   ▼
Final Extraction
```

Jika text layer sangat buruk:

```text
TEXT_LAYER
    ↓
quality < threshold
    ↓
OCR fallback
```

---

# 21.35 Quality Check

Indikator:

```text
Arabic character ratio
garbled character ratio
line coherence
word count
OCR confidence
```

Contoh:

```text
Arabic ratio = 92%
garbled = 1%
```

→ good.

---

# 21.36 Source Viewer Security

Jangan expose filesystem langsung.

Jangan:

```text
/file:///mnt/data/fathul-bari.pdf
```

Gunakan endpoint:

```http
GET /api/v1/source/pages/{page_id}
```

dan:

```http
GET /api/v1/source/pages/{page_id}/image
```

---

# 21.37 Source API

Endpoint:

```http
GET /api/v1/sources
```

```http
GET /api/v1/sources/{id}
```

```http
GET /api/v1/sources/{id}/volumes
```

```http
GET /api/v1/volumes/{id}/pages
```

```http
GET /api/v1/pages/{id}
```

```http
GET /api/v1/pages/{id}/chunks
```

---

# 21.38 Search Source

```http
GET /api/v1/source/search?q=إنما الأعمال
```

Response:

```json
{
  "results": [
    {
      "chunk_id": "...",
      "volume": 1,
      "page": 45,
      "snippet": "قوله إنما الأعمال بالنيات...",
      "score": 0.97
    }
  ]
}
```

---

# 21.39 Import Job

Sama seperti Stage 19:

```text
POST /api/v1/sources/import
```

Response:

```json
{
  "job_id": "..."
}
```

Progress:

```http
GET /api/v1/sources/import/jobs/{job_id}
```

---

# 21.40 Progress Dashboard

```text
Fathul Bari Corpus Import

Volume 1

Pages:
██████████████████░░ 91%

Extracted: 520
OCR:       74
Failed:    2

Chunks:
████████████████░░░░ 83%

Embeddings:
██████████░░░░░░░░░░ 52%
```

---

# 21.41 Audit Trail

Setiap import menyimpan:

```text
document
file hash
import job
extraction method
OCR provider
parser version
chunker version
embedding model
timestamp
```

Contoh:

```json
{
  "pipeline_version": "21.1.0",
  "parser_version": "21.1.0",
  "chunker_version": "21.1.0",
  "embedding_model": "pending"
}
```

---

# 21.42 Pipeline Versioning

Sangat penting karena nanti kita akan mengubah:

```text
OCR
normalizer
chunker
embedding
```

Jika hasil berbeda, kita dapat mengetahui pipeline mana yang menghasilkan evidence tersebut.

---

# 21.43 Corpus State Machine

Dokumen:

```text
REGISTERED
    ↓
UPLOADING
    ↓
EXTRACTING
    ↓
OCR_PROCESSING
    ↓
STRUCTURING
    ↓
CHUNKING
    ↓
INDEXING
    ↓
READY
```

Error:

```text
FAILED
```

---

# 21.44 Page State

```text
PENDING
EXTRACTED
OCR_REQUIRED
OCR_COMPLETE
VERIFIED
FAILED
```

---

# 21.45 Human Review

Halaman dengan OCR rendah:

```text
OCR confidence: 0.54
```

masuk:

```text
Source Review Queue
```

Reviewer dapat melihat:

```text
PDF Image
    │
    ├── Original OCR
    └── Corrected Text
```

---

# 21.46 Yang Tidak Kita Lakukan di Stage 21

Jangan dulu:

```text
❌ Generate syarah AI
❌ Membuat kesimpulan fikih otomatis
❌ Menganggap OCR sebagai kebenaran
❌ Menyatakan match 100%
❌ Menghapus teks lama
❌ Mengandalkan embedding saja
```

Stage ini adalah **data integrity stage**.

---

# 21.47 Hubungan dengan Stage 20

Setelah Stage 21:

```text
                    HADITH
                       │
                       ▼
                Matching Engine
                       │
                       │
                       ▼
                 ┌───────────┐
                 │ MATCH     │
                 └─────┬─────┘
                       │
                       ▼
               FATHUL BARI
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
            Volume    Page     Chunk
              │        │        │
              └────────┼────────┘
                       ▼
                   Evidence
```

---

# 21.48 Hubungan dengan RAG

Sekarang RAG dapat bekerja:

```text
User Question
      │
      ▼
Query Understanding
      │
      ▼
Hadith Retrieval
      │
      ▼
Fathul Bari Retrieval
      │
      ▼
Hybrid Ranking
      │
      ▼
Evidence
      │
      ▼
LLM
      │
      ▼
Answer
      │
      ▼
Citations
```

Jawaban tidak lagi:

> "Menurut AI..."

Tetapi:

> **Menurut syarah Fathul Bari, ...**

dengan:

```text
[FB-V1-P45-C003]
```

yang bisa diklik ke Source Viewer.

---

# 21.49 Data Model Lengkap Sampai Stage 21

```text
sources
  │
  └── collections
       │
       └── books
            │
            └── hadiths
                 │
                 ├── hadith_variants
                 ├── hadith_references
                 └── hadith_matches
                              │
                              ▼
                       sharh_chunks
                              │
                       ┌──────┴──────┐
                       ▼             ▼
                 source_pages   source_sections
                       │             │
                       └──────┬──────┘
                              ▼
                       source_volumes
                              │
                              ▼
                       source_documents
```

---

# 21.50 Definition of Done

Stage 21 selesai apabila:

```text
[ ] source_documents
[ ] source_volumes
[ ] source_pages
[ ] source_sections
[ ] sharh_chunks
[ ] sharh_hadith_references

[ ] PDF reader abstraction
[ ] OCR abstraction
[ ] Arabic normalization
[ ] structure detection
[ ] section-aware chunking
[ ] content hashing
[ ] page provenance
[ ] citation object
[ ] source API
[ ] source search
[ ] import job
[ ] extraction status
[ ] OCR quality tracking
[ ] Source Viewer
[ ] evidence highlighting
[ ] pipeline versioning
```

---

# 21.51 Target UI Setelah Stage 21

```text
┌────────────────────────────────────────────────────┐
│ FATHUL BARI RESEARCH                               │
├────────────────────────────────────────────────────┤
│ Search: إنما الأعمال بالنيات                       │
├────────────────────────────────────────────────────┤
│                                                    │
│ Hadith                                             │
│ ────────────────────────────────────────────────── │
│ Sahih al-Bukhari · #1                             │
│                                                    │
│ Match: 96%                                         │
│                                                    │
│ Fathul Bari                                        │
│ Volume 1 · Page 45                                 │
│                                                    │
│ "قوله إنما الأعمال بالنيات..."                     │
│                                                    │
│ [Open Source] [Review Match]                       │
│                                                    │
└────────────────────────────────────────────────────┘
```

Klik **Open Source**:

```text
┌──────────────────────┬─────────────────────────────┐
│                      │                             │
│      PDF PAGE        │ Extracted Arabic            │
│                      │                             │
│      Page 45         │ قوله إنما الأعمال...       │
│                      │                             │
│                      │                             │
└──────────────────────┴─────────────────────────────┘

Fathul Bari
Vol. 1 · p.45 · PDF p.67
Hash: 8e72...
```

---

# Stage 22 — RAG Evidence Engine

Dengan Stage 19–21, kita sudah mempunyai tiga lapisan penting:

```text
Stage 19
AHMAD SANUSI
      ↓
HADITH DATABASE

Stage 20
HADITH
      ↓
MATCHING
      ↓
FATHUL BARI RELATION

Stage 21
FATHUL BARI
      ↓
CORPUS
      ↓
PAGE / CHUNK / EVIDENCE
```
