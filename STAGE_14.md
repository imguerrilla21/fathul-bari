# Stage 14 — Corpus Processing Engine

## 14.1 Tujuan

Target Stage 14:

```text
PDF Fathul Bari
      │
      ▼
┌─────────────────────┐
│ Corpus Processor    │
└──────────┬──────────┘
           │
     ┌─────┼──────────┐
     ▼     ▼          ▼
   Pages  Sections   Text
     │     │          │
     └─────┼──────────┘
           ▼
    Hadith Detector
           │
           ▼
    Hadith Matcher
           │
           ▼
   Confidence Engine
           │
           ▼
    Review Candidates
           │
           ▼
   Human Verification
```

---

# 14.2 Prinsip penting

Mesin ini **tidak boleh mengklaim bahwa sebuah hadis pasti memiliki hubungan dengan suatu bagian syarah hanya berdasarkan AI**.

Kita membagi hasil menjadi:

```text
DISCOVERED
    ↓
CANDIDATE
    ↓
HIGH CONFIDENCE
    ↓
REVIEWED
    ↓
VERIFIED
```

Jadi:

> **AI menemukan kandidat; manusia menetapkan hubungan terverifikasi.**

---

# 14.3 Processor Architecture

```text
backend/
└── corpus_engine/
    ├── pipeline.py
    │
    ├── stages/
    │   ├── page_processor.py
    │   ├── text_processor.py
    │   ├── section_processor.py
    │   ├── hadith_detector.py
    │   ├── hadith_matcher.py
    │   ├── confidence.py
    │   └── quality.py
    │
    ├── adapters/
    │   ├── pdf.py
    │   ├── ocr.py
    │   └── ahmad_sanusi.py
    │
    └── repositories/
        ├── pages.py
        ├── sections.py
        ├── hadith.py
        └── matches.py
```

---

# 14.4 Processing Pipeline

Pipeline lengkap:

```text
SOURCE
  │
  ▼
PAGE PROCESSOR
  │
  ▼
TEXT PROCESSOR
  │
  ▼
LAYOUT PROCESSOR
  │
  ▼
SECTION DETECTOR
  │
  ▼
HADITH DETECTOR
  │
  ▼
HADITH MATCHER
  │
  ▼
CONFIDENCE ENGINE
  │
  ▼
QUALITY ENGINE
  │
  ▼
REVIEW QUEUE
```

---

# 14.5 Page Processor

Input:

```text
source_document_id
```

Output:

```text
source_pages
```

Pseudo-code:

```python
def process_page(page):

    if page.has_text_layer:
        text = extract_text(page)
    else:
        text = None

    if not text or text_quality(text) < OCR_THRESHOLD:
        text = run_ocr(page)

    save_raw_text(page, text)

    return page
```

---

# 14.6 Text Quality

Kita tidak boleh hanya:

```text
if text exists:
    accept
```

Gunakan beberapa signal:

```text
Arabic character ratio
Text length
Garbage character ratio
Repeated character ratio
Whitespace anomaly
OCR confidence
```

Contoh:

```python
quality = (
    arabic_ratio * 0.30 +
    length_score * 0.20 +
    ocr_score * 0.30 +
    noise_score * 0.20
)
```

Bobot ini **harus dikalibrasi menggunakan korpus nyata**, bukan dianggap angka final.

---

# 14.7 Arabic Text Processor

Pipeline:

```text
Raw Arabic
    │
    ├── Unicode normalization
    │
    ├── Remove OCR noise
    │
    ├── Normalize whitespace
    │
    ├── Normalize punctuation
    │
    └── Search representation
```

Tetapi simpan:

```text
raw_text
normalized_text
search_text
```

Tiga representasi.

---

# 14.8 Contoh

```text
RAW

قال الحافظ رحمه الله تعالى: إنما الأعمال بالنيات...


NORMALIZED

قال الحافظ رحمه الله تعالى إنما الأعمال بالنيات


SEARCH

قال الحافظ رحمه الله تعالى انما الاعمال بالنيات
```

`RAW` digunakan untuk sumber.

`NORMALIZED` untuk pemrosesan.

`SEARCH` untuk retrieval.

---

# 14.9 Section Detector

Section detector harus mendeteksi pola seperti:

```text
كتاب
باب
فصل
تنبيه
قوله
قال
```

Tetapi jangan hanya menggunakan regex.

Gunakan:

```text
Layout
+
Typography
+
Lexical pattern
+
Position
+
Existing metadata
```

Contoh:

```text
Large centered text
        +
"كتاب"
        ↓
KITAB
```

---

# 14.10 Section Tree

Output:

```json id="3axg0u"
{
  "type": "chapter",
  "title": "باب كيف كان بدء الوحي",
  "parent_id": "...",
  "page_start": 12,
  "page_end": 18
}
```

Kemudian:

```text
Kitab
 └── Bab
      ├── Hadith
      └── Sharh
```

---

# 14.11 Hadith Detector

Sekarang bagian terpenting.

Detector mencari:

```text
حديث
الحديث
رقم
قال
عن فلان
حدثنا
أخبرنا
```

Tetapi pattern tersebut hanya menghasilkan **candidate**, bukan keputusan final.

---

# 14.12 Hadith Reference Extraction

Contoh:

```text
قوله: وقد تقدم حديث رقم 123
```

Detector menghasilkan:

```json id="l1o7xc"
{
  "reference_type": "hadith_number",
  "number": 123,
  "confidence": 0.98
}
```

---

# 14.13 Narrator Extraction

Misalnya:

```text
عن أبي هريرة رضي الله عنه
```

Output:

```json id="42c2jc"
{
  "narrator": "أبو هريرة",
  "confidence": 0.94
}
```

Ini menjadi signal matching.

---

# 14.14 Hadith Candidate

Tabel:

```sql id="09ll67"
hadith_candidates
```

Field:

```text
id
source_page_id
section_id
reference_text
reference_number
matn_text
narrator
detector_confidence
status
```

Status:

```text
DETECTED
MATCHED
REVIEW
VERIFIED
REJECTED
```

---

# 14.15 Matching Engine

Sekarang candidate dibandingkan dengan database Hadis dari Ahmad Sanusi.

```text
Fathul Bari Candidate
        │
        ▼
Candidate Retrieval
        │
        ▼
Top 20 Hadith
        │
        ▼
Similarity Scoring
        │
        ▼
Top 5
        │
        ▼
Confidence
```

---

# 14.16 Candidate Retrieval

Gunakan beberapa strategi.

### Strategy 1 — Hadith Number

```text
رقم 1571
```

langsung mencari:

```text
hadith_number = 1571
```

### Strategy 2 — Exact phrase

Cari frasa panjang yang khas.

### Strategy 3 — Arabic BM25

Full-text search.

### Strategy 4 — Semantic similarity

Embedding.

---

# 14.17 Hybrid Matcher

```text
                CANDIDATE
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Number        BM25        Embedding
       │            │            │
       └────────────┼────────────┘
                    ▼
                 Reranker
                    │
                    ▼
              Final Ranking
```

---

# 14.18 Match Score

Simpan komponen secara terpisah:

```json id="x5x1ls"
{
  "reference_score": 1.0,
  "lexical_score": 0.91,
  "semantic_score": 0.94,
  "narrator_score": 0.98,
  "chapter_score": 0.88,
  "final_score": 0.94
}
```

Jangan hanya menyimpan:

```text
confidence = 0.94
```

karena reviewer perlu tahu **mengapa** kandidat tersebut muncul.

---

# 14.19 Confidence Bands

Gunakan tiga zona awal:

```text
0.90 – 1.00
HIGH

0.70 – 0.89
MEDIUM

< 0.70
LOW
```

Tetapi:

> **HIGH bukan berarti VERIFIED.**

HIGH berarti:

> "Kandidat sangat layak diperiksa."

---

# 14.20 Review Queue

Ranking review:

```text
Priority =
confidence
+
source_quality
+
reference_strength
+
impact
```

Contoh:

```text
🔴 High confidence + important
🟠 Medium confidence
🟡 Low confidence
```

---

# 14.21 Reviewer Screen

```text
┌────────────────────────────────────────────────────────────┐
│ HADITH MATCH REVIEW                                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ FATHUL BARI                                               │
│ Vol 1 · PDF p.45                                          │
│                                                            │
│ "إنما الأعمال بالنيات..."                                 │
│                                                            │
├──────────────────────────┬─────────────────────────────────┤
│ CANDIDATE                │ AHMAD SANUSI                   │
│                          │                                 │
│ Detected #1              │ Bukhari #1                     │
│                          │                                 │
│ Similarity 96%           │ Arabic Matn                    │
│ Narrator 99%             │ ...                             │
│ Reference 100%           │                                 │
├──────────────────────────┴─────────────────────────────────┤
│                                                         │
│ [ VERIFY ]    [ REJECT ]    [ NEED REVIEW ]             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

# 14.22 Verification Decision

Saat reviewer menekan `VERIFY`:

```text
Candidate
   ↓
Verified Link
   ↓
Audit Event
   ↓
Knowledge Graph
   ↓
RAG Index
```

Saat `REJECT`:

```text
Candidate
   ↓
Rejected
   ↓
Audit Event
```

Tidak masuk verified graph.

---

# 14.23 Reviewer Reason

Untuk reject, wajib ada reason.

```text
Wrong hadith number
Wrong matn
Wrong narrator
False detection
OCR error
Duplicate
Other
```

Contoh:

```json id="2lduhj"
{
  "decision": "REJECT",
  "reason": "WRONG_HADITH",
  "note": "Reference points to another hadith."
}
```

---

# 14.24 Human-in-the-loop

Keseluruhan pipeline:

```text
             MACHINE
                │
                ▼
          FIND CANDIDATE
                │
                ▼
          RANK CANDIDATE
                │
                ▼
             HUMAN
                │
        ┌───────┴───────┐
        ▼               ▼
      VERIFY          REJECT
        │               │
        ▼               ▼
      GRAPH           AUDIT
        │
        ▼
       RAG
```

Ini adalah prinsip utama aplikasi kita.

---

# 14.25 Automatic Cross-reference

Jika Fathul Bari menyebut:

```text
كما تقدم في حديث رقم 1571
```

maka:

```text
Sharh A
   │
   └── REFERENCES
          │
          ▼
      Bukhari #1571
```

Tetapi jika hanya:

```text
كما تقدم
```

maka dibuat:

```text
AMBIGUOUS_REFERENCE
```

dan masuk review.

---

# 14.26 Cross-reference Graph

Contoh:

```text
Bukhari #1
    │
    ▼
Sharh §1
    │
    ├──── REFERENCES ────► Bukhari #2
    │
    └──── REFERENCES ────► Sharh §15
```

Ini membuat Knowledge Graph jauh lebih kaya.

---

# 14.27 Chunk Context Builder

Setelah section terdeteksi:

```text
Hadith
  +
Chapter
  +
Sharh paragraph
  +
Page
```

menjadi contextual chunk.

Contoh:

```json id="0ym1gq"
{
  "chunk_type": "sharh",
  "hadith_id": "...",
  "chapter_id": "...",
  "section_id": "...",
  "page_id": "...",
  "text": "...",
  "context": {
    "book": "...",
    "chapter": "...",
    "hadith_number": 1
  }
}
```

---

# 14.28 RAG-ready Corpus

Hasil akhirnya:

```text
┌────────────────────────────────────────────┐
│ CHUNK                                      │
├────────────────────────────────────────────┤
│ Work: Fathul Bari                          │
│ Volume: 1                                  │
│ Chapter: Beginning of Revelation           │
│ Hadith: Bukhari #1                         │
│ Page: 45                                   │
│ Section: §001                              │
│                                            │
│ Arabic text...                             │
│                                            │
│ embedding: [...]                           │
└────────────────────────────────────────────┘
```

Ini jauh lebih baik daripada hanya:

```text
embedding = [...]
```

---

# 14.29 Quality Report

Setiap volume menghasilkan:

```text
FATHUL BARI VOL 1
──────────────────────────────

Pages
520 / 520

OCR
508 good
12 review

Sections
43 detected

Hadith candidates
612

Matched
587

High confidence
523

Medium
49

Low
15

Verified
0
```

Perhatikan:

> **Verified = 0** sampai reviewer benar-benar memverifikasi.

---

# 14.30 Batch Processing

Jangan langsung memproses 13 volume.

Urutan yang lebih aman:

```text
Pilot
 ↓
Volume 1
 ↓
QA
 ↓
Fix pipeline
 ↓
Volume 2
 ↓
QA
 ↓
Volume 3
 ↓
...
```

Setelah pipeline stabil:

```text
Volume 4–13
```

dapat diproses secara batch.

---

# 14.31 Pilot Volume

Saya sangat menyarankan membuat:

```text
CORPUS PILOT
```

dengan:

```text
50–100 halaman
```

terlebih dahulu.

Tujuan:

```text
OCR validation
Section detection
Hadith matching
Chunking
Embedding
Citation
Source viewer
```

Baru kemudian full volume.

---

# 14.32 Golden Corpus

Buat subset yang diverifikasi manual:

```text
Golden Corpus
```

Misalnya:

```text
100 Hadith
100 Sharh sections
100 source pages
```

Kemudian pipeline diuji terhadap corpus ini setiap kali ada perubahan kode.

```text
Code change
    ↓
Golden Corpus
    ↓
Evaluation
    ↓
Pass?
 ┌──┴──┐
No    Yes
│      │
Stop  Deploy
```

---

# 14.33 Definition of Done — Stage 14

```text
[ ] Page processor
[ ] Text quality detector
[ ] Arabic normalization
[ ] Layout reconstruction
[ ] Section detector
[ ] Hadith detector
[ ] Narrator extraction
[ ] Hadith candidate table
[ ] Ahmad Sanusi adapter
[ ] Hybrid matching
[ ] Match scoring
[ ] Confidence engine
[ ] Review queue
[ ] Verify / Reject workflow
[ ] Cross-reference detector
[ ] Chunk builder
[ ] Embedding pipeline
[ ] Graph builder
[ ] Quality report
[ ] Batch processing
[ ] Golden corpus
[ ] Pipeline regression test
```

---

# Arsitektur setelah Stage 14

```text
                    FATHUL BARI PDF
                           │
                           ▼
                  ┌─────────────────┐
                  │ INGESTION       │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │ OCR / EXTRACTION│
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │ NORMALIZATION   │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │ SECTION DETECTOR │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │ HADITH DETECTOR │
                  └────────┬────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
       Ahmad Sanusi API          Fathul Bari
                │                     │
                └──────────┬──────────┘
                           ▼
                  ┌─────────────────┐
                  │ HYBRID MATCHER  │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │ REVIEW QUEUE    │
                  └────────┬────────┘
                           ▼
                     HUMAN VERIFY
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
          KNOWLEDGE GRAPH          RAG INDEX
                │                     │
                └──────────┬──────────┘
                           ▼
                   SYARAH AI ASSISTANT
```
