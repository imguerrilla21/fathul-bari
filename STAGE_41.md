# Stage 41 — Multimodal Source Intelligence

Stage 41 membangun lapisan **pemahaman sumber asli** di atas RAG Stage 40.

Tujuannya:

> **AI tidak hanya membaca hasil OCR, tetapi memahami hubungan antara teks, halaman scan, posisi teks, heading, footnote, margin, dan struktur visual kitab.**

Ini sangat penting untuk aplikasi *Syarah Fathul Bari*, karena OCR Arab tidak selalu cukup akurat dan struktur halaman kitab klasik sering kompleks.

---

# 41.1 Arsitektur

```text
                 SCANNED BOOK
                      │
                      ▼
              ┌───────────────┐
              │ Image Ingestor │
              └───────┬───────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        OCR         Layout       Image
       Engine       Analysis     Archive
          │           │           │
          └───────────┼───────────┘
                      ▼
              PAGE INTELLIGENCE
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
       Blocks       Regions      Relations
          │           │            │
          └───────────┼────────────┘
                      ▼
              SOURCE REPRESENTATION
                      │
             ┌────────┴────────┐
             ▼                 ▼
        Text Retrieval    Visual Retrieval
             │                 │
             └────────┬────────┘
                      ▼
                MULTIMODAL RAG
                      │
                      ▼
                  AI ANSWER
                      │
                      ▼
              SOURCE CITATION
```

---

# 41.2 Masalah yang Diselesaikan

Stage 41 menangani kasus seperti:

### Kasus 1 — OCR salah

Scan:

```text
النية
```

OCR:

```text
البيه
```

Visual verification dapat mendeteksi kemungkinan kesalahan.

---

### Kasus 2 — Footnote bercampur

```text
MAIN TEXT
──────────────
قال ابن حجر ...

FOOTNOTE
──────────────
انظر ...
```

OCR sederhana dapat menggabungkan keduanya.

Stage 41 harus memisahkan:

```text
MAIN_TEXT
FOOTNOTE
```

---

### Kasus 3 — Margin

Kitab klasik sering memiliki:

```text
┌──────────────────────────────┐
│ margin       MAIN TEXT       │
│ note         MAIN TEXT       │
│              MAIN TEXT       │
└──────────────────────────────┘
```

Margin tidak boleh otomatis dianggap sebagai bagian dari paragraf utama.

---

# 41.3 Page Object Model

Setiap halaman menjadi objek:

```json
{
  "page_id": "PG-000184",
  "document_id": "FB-001",
  "volume": 1,
  "page_number": 184,
  "image_uri": "...",
  "width": 2480,
  "height": 3508
}
```

---

# 41.4 Page Regions

Tambahkan region:

```json
{
  "region_id": "R-184-01",
  "type": "MAIN_TEXT",
  "bbox": [
    420,
    350,
    2070,
    3150
  ]
}
```

Format:

```text
x
y
width
height
```

atau:

```text
x1
y1
x2
y2
```

Pilih satu standar global.

Saya merekomendasikan:

```text
x1, y1, x2, y2
```

---

# 41.5 Region Types

Gunakan enum:

```text
MAIN_TEXT
HEADER
FOOTER
FOOTNOTE
MARGIN
PAGE_NUMBER
CHAPTER_TITLE
HADITH
QURAN_VERSE
POETRY
QUOTE
EDITOR_NOTE
STAMP
ILLUSTRATION
UNKNOWN
```

---

# 41.6 Layout Detection

Pipeline:

```text
Page Image
    ↓
Deskew
    ↓
Denoise
    ↓
Layout Detection
    ↓
Text Region Detection
    ↓
Reading Order
    ↓
OCR
```

Jangan:

```text
Image → OCR → selesai
```

---

# 41.7 OCR Layer

OCR harus menyimpan:

```text
raw OCR
normalized OCR
corrected OCR
```

Contoh:

```json
{
  "raw": "الحمد لله رب العلمين",
  "normalized": "الحمد لله رب العالمين",
  "corrected": "الحمد لله رب العالمين"
}
```

**Raw OCR tidak boleh dihapus.**

---

# 41.8 OCR Provenance

Setiap token sebaiknya mempunyai provenance:

```json
{
  "text": "العالمين",
  "confidence": 0.91,
  "bbox": [850, 712, 1100, 790],
  "source": "OCR"
}
```

---

# 41.9 Token-Level Confidence

Contoh:

```text
الحمد       0.98
لله         0.99
رب          0.97
العالمين    0.61
```

Sistem dapat menandai:

```text
⚠ LOW OCR CONFIDENCE
```

---

# 41.10 Visual Verification

Jika confidence:

```text
< 0.75
```

buat status:

```text
NEEDS_REVIEW
```

Tetapi threshold harus configurable.

---

# 41.11 Human OCR Review

UI:

```text
┌───────────────────────────────────────┐
│ PAGE 184                              │
│                                       │
│     [ SCANNED PAGE ]                  │
│                                       │
├───────────────────────────────────────┤
│ OCR                                   │
│ الحمد لله رب العلمين                   │
│                     ↑                 │
│                [0.61 confidence]      │
├───────────────────────────────────────┤
│ Correction                            │
│ الحمد لله رب العالمين                  │
│                                       │
│ [Save Correction]                     │
└───────────────────────────────────────┘
```

---

# 41.12 OCR Correction Policy

Jangan mengganti:

```text
raw OCR
```

dengan:

```text
corrected OCR
```

Simpan tiga lapisan:

```text
RAW
NORMALIZED
EDITORIAL CORRECTION
```

---

# 41.13 Correction Provenance

```json
{
  "original": "العلمين",
  "corrected": "العالمين",
  "method": "HUMAN",
  "reviewer_id": "USR-123",
  "reason": "visual verification",
  "timestamp": "..."
}
```

---

# 41.14 Correction Methods

```text
OCR_AUTO
NORMALIZATION
DICTIONARY
AI_SUGGESTION
HUMAN_REVIEW
SOURCE_COMPARISON
```

AI suggestion **tidak otomatis menjadi authoritative text**.

---

# 41.15 Page Segmentation

Setiap halaman:

```text
PAGE
 ├── HEADER
 ├── TITLE
 ├── MAIN COLUMN
 │    ├── PARAGRAPH
 │    ├── HADITH
 │    └── COMMENTARY
 ├── MARGIN
 └── FOOTNOTE
```

---

# 41.16 Reading Order

Reading order disimpan eksplisit:

```json
{
  "region_id": "R-1",
  "reading_order": 1
}
```

Contoh:

```text
R1 → R2 → R3 → R4
```

---

# 41.17 Arabic RTL

Database menyimpan:

```text
direction = RTL
language = ar
script = Arabic
```

UI harus mendukung:

```css
direction: rtl;
text-align: right;
```

---

# 41.18 Arabic Text Normalization

Normalisasi dapat menangani:

```text
أ
إ
آ
ٱ
```

dan variasi Unicode lainnya.

Tetapi:

> **Normalized search text tidak boleh menggantikan diplomatic transcription.**

---

# 41.19 Dua Representasi

Simpan:

```text
DISPLAY TEXT
SEARCH TEXT
```

Contoh:

```json
{
  "display_text": "ٱلْحَمْدُ لِلَّهِ",
  "search_text": "الحمد لله"
}
```

---

# 41.20 Page Image Storage

Struktur:

```text
storage/
└── books/
    └── fathul-bari/
        └── volume-01/
            ├── page-001.webp
            ├── page-002.webp
            └── ...
```

Gunakan object storage untuk produksi.

---

# 41.21 Image Derivatives

Jangan hanya menyimpan satu ukuran.

Buat:

```text
thumbnail
preview
full
tile
```

Contoh:

```text
page-184-thumb.webp
page-184-preview.webp
page-184-full.webp
```

---

# 41.22 Deep Zoom

Untuk halaman kitab, gunakan tiled image.

```text
FULL PAGE
    ↓
TILES
    ↓
ZOOM
```

Sehingga pengguna dapat memperbesar teks Arab tanpa mengunduh gambar penuh berkali-kali.

---

# 41.23 Source Viewer

UI:

```text
┌────────────────────────────────────────────┐
│ Fath al-Bari — Vol. 1 — p.184             │
├───────────────────┬────────────────────────┤
│                   │                        │
│   SCANNED PAGE    │ OCR / TEXT             │
│                   │                        │
│    [ZOOM]         │ الحمد لله ...          │
│                   │                        │
│                   │ [Jump to region]       │
└───────────────────┴────────────────────────┘
```

---

# 41.24 Synchronized Viewer

Ketika user memilih teks:

```text
قال ابن حجر
```

scanner otomatis:

```text
→ halaman
→ region
→ bbox
```

disorot.

Sebaliknya, klik scan:

```text
→ text block
```

disorot.

---

# 41.25 Bounding Box Highlight

```json
{
  "region_id": "R-184-07",
  "bbox": [650, 1100, 2100, 1430]
}
```

Frontend menggambar:

```text
┌──────────────────────┐
│ highlighted text     │
└──────────────────────┘
```

---

# 41.26 Citation Upgrade

Stage 40 citation:

```text
Fathul Bari, Vol. 1, p.184
```

Stage 41:

```text
Fathul Bari
Vol. 1
p.184
Region R-184-07
```

Dengan:

```text
[View Scan]
```

---

# 41.27 Citation Object

```json
{
  "source_id": "FB001",
  "volume": 1,
  "page": 184,
  "region_id": "R-184-07",
  "passage_id": "P88421"
}
```

---

# 41.28 Multimodal Evidence

Evidence sekarang dapat berupa:

```text
TEXT
IMAGE
TEXT + IMAGE
```

Contoh:

```json
{
  "type": "TEXT_IMAGE",
  "passage_id": "P88421",
  "page_id": "PG184",
  "region_id": "R184-07"
}
```

---

# 41.29 Visual Evidence Score

Tambahkan:

```text
visual_match_score
```

Misalnya:

```text
text_match       0.93
layout_match     0.98
ocr_confidence   0.61
source_quality   0.99
```

Sistem dapat menandai passage:

```text
HIGH RELEVANCE
BUT
LOW OCR CONFIDENCE
```

---

# 41.30 Multimodal Retrieval

Stage 40:

```text
Query
 ↓
Text Retrieval
```

Stage 41:

```text
Query
 ↓
Text Retrieval
 +
Page/Region Retrieval
 ↓
Fusion
```

---

# 41.31 Visual Query

Pertanyaan:

> "Apa yang tertulis di catatan pinggir halaman ini?"

Sistem:

```text
Selected page
 ↓
MARGIN regions
 ↓
OCR
 ↓
Answer
```

---

# 41.32 Page-Aware Retrieval

Jika user sedang melihat:

```text
Vol 1 — p.184
```

prioritas:

```text
current page
± nearby pages
same chapter
global corpus
```

---

# 41.33 Region-Aware Retrieval

Jika query berkaitan dengan:

```text
footnote
```

retrieval hanya memprioritaskan:

```text
FOOTNOTE
```

---

# 41.34 Document Structure Graph

Tambahkan hubungan:

```text
Document
 └── Volume
      └── Page
           ├── Region
           │    └── Passage
           │         └── Token
           └── Image
```

---

# 41.35 Database

```sql
CREATE TABLE source_pages (
    id UUID PRIMARY KEY,

    document_id UUID NOT NULL,

    volume_number INTEGER,

    page_number INTEGER,

    image_uri TEXT NOT NULL,

    width INTEGER,

    height INTEGER,

    checksum TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 41.36 Page Regions

```sql
CREATE TABLE page_regions (
    id UUID PRIMARY KEY,

    page_id UUID NOT NULL,

    region_type VARCHAR(40),

    x1 INTEGER NOT NULL,
    y1 INTEGER NOT NULL,
    x2 INTEGER NOT NULL,
    y2 INTEGER NOT NULL,

    reading_order INTEGER,

    confidence NUMERIC,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 41.37 OCR Blocks

```sql
CREATE TABLE ocr_blocks (
    id UUID PRIMARY KEY,

    region_id UUID NOT NULL,

    raw_text TEXT,

    normalized_text TEXT,

    corrected_text TEXT,

    ocr_confidence NUMERIC,

    ocr_engine VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 41.38 OCR Tokens

Jika membutuhkan granularitas tinggi:

```sql
CREATE TABLE ocr_tokens (
    id UUID PRIMARY KEY,

    block_id UUID NOT NULL,

    token_index INTEGER,

    text TEXT,

    confidence NUMERIC,

    x1 INTEGER,
    y1 INTEGER,
    x2 INTEGER,
    y2 INTEGER
);
```

Untuk corpus besar, tabel token dapat menjadi sangat besar. Gunakan hanya jika memang diperlukan untuk review tingkat token.

---

# 41.39 Source Corrections

```sql
CREATE TABLE source_corrections (
    id UUID PRIMARY KEY,

    block_id UUID,

    original_text TEXT,

    corrected_text TEXT,

    method VARCHAR(50),

    reviewer_id UUID,

    reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 41.40 Visual Audit Trail

Setiap perubahan:

```text
Original Scan
      ↓
OCR
      ↓
Normalization
      ↓
AI Suggestion
      ↓
Human Correction
      ↓
Published Text
```

Semua harus dapat dilacak.

---

# 41.41 AI OCR Correction

AI boleh memberikan:

```text
Suggestion:
العلمين → العالمين
```

Tetapi status:

```text
PENDING_REVIEW
```

Bukan:

```text
VERIFIED
```

---

# 41.42 Human Verification

Reviewer:

```text
[ Accept ]
[ Reject ]
[ Edit ]
```

Audit:

```json
{
  "action": "ACCEPT_CORRECTION",
  "actor": "USR-123",
  "before": "...",
  "after": "..."
}
```

---

# 41.43 Source Integrity

Setiap scan memiliki checksum:

```text
SHA-256
```

Contoh:

```text
sha256:
9e1f...a71c
```

Tujuannya memastikan:

> File sumber tidak berubah tanpa terdeteksi.

---

# 41.44 Immutable Original

Original scan:

```text
IMMUTABLE
```

Jangan pernah overwrite.

Correction berada di layer:

```text
derived data
```

---

# 41.45 Edition Identity

Page harus terkait:

```text
Edition
Volume
Page
```

Bukan hanya:

```text
page_number = 184
```

Karena edisi berbeda bisa mempunyai pagination berbeda.

---

# 41.46 Source Identity

```json
{
  "edition_id": "FB-ED-001",
  "volume": 1,
  "printed_page": 184,
  "scan_page": 193
}
```

Ini penting.

---

# 41.47 Printed vs Scan Page

Bedakan:

```text
printed_page
```

dan:

```text
scan_sequence
```

Misalnya:

```text
Printed: 184
Scan: 193
```

UI harus dapat menampilkan keduanya.

---

# 41.48 Source Viewer URL

Jangan membuat citation:

```text
?page=184
```

saja.

Gunakan:

```text
/source/{edition}/{volume}/{page}/{region}
```

Contoh konseptual:

```text
/source/FB-ED-001/1/184/R184-07
```

---

# 41.49 Multimodal RAG Context

Context Stage 41:

```text
SOURCE #1

Text:
قال ابن حجر ...

Metadata:
Fath al-Bari
Vol 1
p.184

Visual:
page image
region bbox

OCR confidence:
0.91

Verification:
HUMAN VERIFIED
```

---

# 41.50 Model Input

Jika model multimodal tersedia:

```text
TEXT
+
CROPPED REGION IMAGE
```

Jika model text-only:

```text
normalized text
+
metadata
+
OCR confidence
```

Jadi sistem tetap kompatibel dengan kedua jenis model.

---

# 41.51 Visual Crop

Jangan selalu mengirim satu halaman penuh.

Lebih efisien:

```text
PAGE
 ↓
REGION
 ↓
CROP
 ↓
MODEL
```

---

# 41.52 Crop Padding

Tambahkan padding:

```text
5–10%
```

agar model tidak kehilangan konteks visual di sekitar region.

Nilainya configurable.

---

# 41.53 Multimodal Prompt

```text
Anda adalah asisten penelitian Fathul Bari.

SOURCE IMAGE berikut adalah halaman kitab asli.
TEXT berikut adalah OCR dari region tersebut.

Jangan menganggap OCR selalu benar.
Jika OCR dan gambar berbeda:
prioritaskan pemeriksaan visual sumber.

Jangan membuat klaim yang tidak didukung sumber.
```

---

# 41.54 OCR Conflict

Jika:

```text
OCR:
البيه

IMAGE:
النية
```

AI menandai:

```text
OCR_CONFLICT
```

dan tidak diam-diam mengubah source authoritative.

---

# 41.55 Conflict Resolution

Prioritas:

```text
Human Verified
        ↓
Original Image
        ↓
Verified Transcription
        ↓
Corrected OCR
        ↓
Raw OCR
        ↓
AI Guess
```

**AI Guess tidak boleh menjadi sumber primer.**

---

# 41.56 Visual Source Confidence

Status:

```text
VERIFIED
PROBABLE
UNCERTAIN
OCR_CONFLICT
NEEDS_REVIEW
```

---

# 41.57 Review Dashboard Upgrade

Stage 6/41 dashboard:

```text
┌────────────────────────────────────────────┐
│ SOURCE REVIEW                              │
├──────────────────────┬─────────────────────┤
│                      │                     │
│   SCANNED PAGE       │ OCR                 │
│                      │                     │
│   [Region]           │ النص ...            │
│                      │                     │
├──────────────────────┴─────────────────────┤
│ OCR confidence: 71%                        │
│ Source status: NEEDS_REVIEW                │
│                                            │
│ [Verify] [Correct] [Reject]                │
└────────────────────────────────────────────┘
```

---

# 41.58 Search Result Upgrade

Hasil pencarian:

```text
Fath al-Bari
Vol. 1 — p.184

"قال ابن حجر..."

Relevance: 94%
OCR: 91%
Source: VERIFIED

[Read Text]
[View Scan]
[Open Region]
```

---

# 41.59 AI Answer Upgrade

Jawaban:

> Ibn Hajar menjelaskan bahwa ...

Di bawahnya:

```text
Sources

① Fath al-Bari, Vol. 1, p.184
   Region R184-07

   [View original scan]
```

---

# 41.60 Citation Click

Ketika diklik:

```text
AI ANSWER
   ↓
Citation
   ↓
Passage
   ↓
Region
   ↓
Page
   ↓
Original Scan
```

Ini membuat setiap jawaban dapat diverifikasi manusia.

---

# 41.61 Multimodal Knowledge Graph

Knowledge Graph Stage 9 juga diperluas:

```text
Hadith
 │
 ├── Commentary
 │
 ├── Passage
 │
 ├── Page
 │
 ├── Region
 │
 └── Image
```

Relationship:

```text
PASSAGE_APPEARS_ON_PAGE
REGION_CONTAINS_PASSAGE
PAGE_BELONGS_TO_VOLUME
VOLUME_BELONGS_TO_EDITION
```

---

# 41.62 New Graph Relations

```text
OCR_DERIVED_FROM
CORRECTED_FROM
VERIFIED_AGAINST
VISUALLY_LOCATED_AT
NEXT_REGION
PREVIOUS_REGION
```

---

# 41.63 Multimodal Provenance

Contoh:

```text
Claim
 ↓
Passage P88421
 ↓
OCR Block B88421
 ↓
Region R184-07
 ↓
Page PG184
 ↓
Scan SHA256
```

Ini adalah **provenance chain**.

---

# 41.64 API

Tambahkan endpoint:

```http
GET /api/v1/source/pages/{page_id}

GET /api/v1/source/pages/{page_id}/regions

GET /api/v1/source/regions/{region_id}

GET /api/v1/source/regions/{region_id}/image

GET /api/v1/source/regions/{region_id}/ocr

POST /api/v1/source/corrections

POST /api/v1/source/verify
```

---

# 41.65 Multimodal Search API

```http
POST /api/v1/rag/multimodal-search
```

Request:

```json
{
  "query": "Apa yang tertulis dalam catatan pinggir?",
  "page_id": "PG-184",
  "region_type": "MARGIN"
}
```

Response:

```json
{
  "results": [
    {
      "region_id": "R184-12",
      "score": 0.92,
      "ocr_confidence": 0.88,
      "verification": "VERIFIED"
    }
  ]
}
```

---

# 41.66 Ingestion Pipeline

Stage 41 ingestion:

```text
PDF
 ↓
PDF Metadata
 ↓
Page Extraction
 ↓
Image Quality Check
 ↓
Deskew
 ↓
Layout Detection
 ↓
Region Segmentation
 ↓
OCR
 ↓
Normalization
 ↓
Passage Reconstruction
 ↓
Embedding
 ↓
Index
 ↓
Verification
```

---

# 41.67 Quality Gates

Sebelum halaman masuk production:

```text
[ ] Image readable
[ ] Correct edition
[ ] Correct volume
[ ] Page number detected
[ ] Layout detected
[ ] OCR generated
[ ] Reading order generated
[ ] OCR confidence calculated
[ ] Passage linked
[ ] Hash stored
```

---

# 41.68 Page Quality Score

Contoh:

```text
image_quality       0.96
layout_quality      0.93
ocr_quality         0.88
metadata_quality    0.99
```

Gabungkan menjadi:

```text
page_quality_score
```

Tetapi jangan menjadikan satu angka sebagai pengganti komponen detail.

---

# 41.69 Low Quality Page Queue

Jika:

```text
page_quality < threshold
```

masuk:

```text
REVIEW_QUEUE
```

Dashboard:

```text
184 pages need review
```

---

# 41.70 Priority Review

Prioritaskan halaman yang:

```text
frequently retrieved
+
low OCR confidence
```

Contoh:

```text
Page 184
retrieved 1,820 times
OCR confidence 62%
```

→ **HIGH PRIORITY**

Ini jauh lebih efisien daripada memeriksa seluruh corpus secara manual terlebih dahulu.

---

# 41.71 Active Learning

Sistem belajar dari koreksi reviewer:

```text
Reviewer corrections
        ↓
Error patterns
        ↓
OCR improvement
        ↓
Retraining / rule updates
        ↓
New ingestion
```

Tetap simpan historical versions.

---

# 41.72 Common OCR Error Dictionary

Buat:

```sql
CREATE TABLE ocr_error_patterns (
    id UUID PRIMARY KEY,

    incorrect TEXT,

    likely_correct TEXT,

    language VARCHAR(10),

    frequency INTEGER DEFAULT 1,

    verified_count INTEGER DEFAULT 0
);
```

---

# 41.73 Arabic-Specific Layer

Tambahkan pemeriksaan:

```text
Arabic Unicode
Harakat
Tatweel
Ligatures
Alef variants
Ya/Alif Maqsura
Ta Marbuta
Hamza
```

Namun hati-hati:

> Normalisasi pencarian ≠ perubahan teks sumber.

---

# 41.74 Hadith Boundary Detection

Salah satu fitur paling penting.

Deteksi:

```text
قال رسول الله ﷺ
...
```

sebagai kemungkinan:

```text
HADITH_BLOCK
```

kemudian:

```text
COMMENTARY_BLOCK
```

---

# 41.75 Hadith / Sharh Boundary

Struktur:

```text
[HADITH]

حدثنا ...
قال رسول الله ﷺ ...

[SHARH]

قال ابن حجر:
...
```

RAG dapat menggunakan boundary ini agar tidak mencampurkan:

```text
Prophetic text
```

dengan:

```text
Ibn Hajar commentary
```

---

# 41.76 Source Role

Setiap block diberi:

```text
PROPHETIC_TEXT
COMMENTARY
QUOTATION
EDITORIAL
FOOTNOTE
MARGIN
```

Ini sangat penting untuk aplikasi hadis.

---

# 41.77 AI Citation Policy

AI harus membedakan:

```text
"Rasulullah ﷺ bersabda..."
```

dengan:

```text
"Ibn Hajar menjelaskan..."
```

Citation harus menunjuk source yang tepat.

---

# 41.78 False Attribution Prevention

Jika passage:

```text
Ibn Hajar quotes al-Khattabi
```

AI tidak boleh menyatakan:

> Ibn Hajar mengatakan X

jika sebenarnya:

> al-Khattabi mengatakan X dan Ibn Hajar hanya mengutipnya.

Metadata:

```text
speaker
quoted_author
commentator
```

harus dipertahankan jika dapat dideteksi.

---

# 41.79 Multimodal Evidence Object

```json
{
  "passage_id": "P88421",
  "page_id": "PG184",
  "region_id": "R184-07",

  "text": "...",

  "image": {
    "uri": "...",
    "bbox": [650,1100,2100,1430]
  },

  "ocr_confidence": 0.91,

  "verification": "HUMAN_VERIFIED",

  "source_role": "COMMENTARY"
}
```

---

# 41.80 Stage 41 Testing

Tambahkan test:

```text
OCR Test
Layout Test
Reading Order Test
RTL Test
Region Test
Citation Test
Image Integrity Test
Visual/Text Sync Test
Hadith Boundary Test
Source Attribution Test
```

---

# 41.81 Critical Test

Test:

```text
Click citation
 ↓
Open page
 ↓
Highlight region
 ↓
Show OCR
 ↓
Show source image
```

Harus menghasilkan **region yang sama**.

---

# 41.82 Regression Test

Contoh:

```text
Expected:
P88421
Page:
184
Region:
R184-07
```

Jika OCR pipeline baru menghasilkan:

```text
Page 185
```

→ regression failure.

---

# 41.83 Stage 41 Folder

```text
src/
├── multimodal/
│   ├── ingestion/
│   ├── image/
│   ├── layout/
│   ├── ocr/
│   ├── normalization/
│   ├── correction/
│   ├── verification/
│   ├── region/
│   ├── reading-order/
│   ├── source-viewer/
│   ├── visual-retrieval/
│   ├── multimodal-rag/
│   └── provenance/
│
├── source/
│   ├── pages/
│   ├── regions/
│   ├── blocks/
│   ├── tokens/
│   └── corrections/
│
└── tests/
    ├── ocr/
    ├── layout/
    ├── source/
    └── multimodal/
```

---

# 41.84 Definition of Done

```text
[ ] Page Image Archive
[ ] Immutable Source
[ ] SHA-256 Integrity
[ ] Page Metadata
[ ] Region Detection
[ ] Reading Order
[ ] OCR Layer
[ ] Raw OCR
[ ] Normalized OCR
[ ] Corrected OCR
[ ] OCR Confidence
[ ] Token Bounding Box
[ ] Arabic RTL
[ ] Arabic Normalization
[ ] Main Text Detection
[ ] Footnote Detection
[ ] Margin Detection
[ ] Hadith Boundary Detection
[ ] Commentary Boundary Detection
[ ] Source Role Classification
[ ] Human Verification
[ ] Correction Audit Trail
[ ] Source Viewer
[ ] Deep Zoom
[ ] Text ↔ Image Synchronization
[ ] Region Citation
[ ] Visual Evidence
[ ] Multimodal Retrieval
[ ] Multimodal Context
[ ] Knowledge Graph Integration
[ ] Provenance Chain
[ ] Low Quality Queue
[ ] Active Learning
[ ] API
[ ] Tests
```

---

# 41.85 Hasil Akhir Stage 41

Setelah Stage 41, aplikasi bukan lagi sekadar:

```text
Hadis
 ↓
OCR
 ↓
AI
```

tetapi:

```text
                    HADITH
                       │
                       ▼
                 FATHUL BARI
                       │
                       ▼
                     VOLUME
                       │
                       ▼
                     PAGE
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          IMAGE                LAYOUT
             │                   │
             └─────────┬─────────┘
                       ▼
                    REGION
                       │
                       ▼
                      OCR
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        RAW TEXT            CORRECTION
             │                   │
             └─────────┬─────────┘
                       ▼
                    PASSAGE
                       │
                       ▼
                HYBRID RETRIEVAL
                  [Stage 40]
                       │
                       ▼
                    EVIDENCE
                       │
                       ▼
                  MULTIMODAL RAG
                       │
                       ▼
                     AI
                       │
                       ▼
                  CITATION
                       │
                       ▼
              ORIGINAL PAGE REGION
```

### Prinsip utama Stage 41

**Scan adalah sumber visual. OCR adalah derived data. AI adalah interpreter. Reviewer adalah verifier.**

Dengan struktur ini, ketika AI menjawab sebuah pertanyaan syarah, pengguna dapat menelusuri rantainya sampai ke **potongan halaman kitab asli**, bukan hanya mempercayai teks yang dihasilkan AI.

---
