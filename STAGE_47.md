# Stage 47 — Knowledge Publication & Scholarly Content Pipeline

Karena **Stage 46 (Advanced Arabic Text Intelligence) tidak diperlukan**, kita langsung melompat ke **Stage 47**.

Pada titik ini fondasi aplikasi sudah sangat lengkap:

```text
Hadits API
   ↓
Source Ingestion
   ↓
Fathul Bari
   ↓
Review Dashboard
   ↓
Source Viewer
   ↓
RAG/Syarah AI
   ↓
Knowledge Graph
   ↓
Citation & Attribution
   ↓
Research Workspace
   ↓
Evaluation & Reliability
```

Stage 47 sebaiknya berfokus pada **mengubah hasil penelitian yang sudah tervalidasi menjadi konten ilmiah yang dapat dipublikasikan**, tanpa kehilangan keterlacakan ke sumber asli.

---

# 47.1 Tujuan

Membangun **Scholarly Publishing Pipeline**:

```text
Research Project
      ↓
Validated Evidence
      ↓
Claims
      ↓
Reviewed Content
      ↓
Editorial Review
      ↓
Publication
      ↓
Versioned Article
      ↓
Public Reader / API
```

Hasil akhirnya dapat berupa:

* artikel syarah
* kajian hadis
* ringkasan Fathul Bari
* ensiklopedia hadis
* thematic research
* halaman ulama
* halaman hadis
* comparative study
* materi untuk konten Almaktaba

---

# 47.2 Prinsip Utama

Yang sangat penting:

> **AI boleh membantu menulis, tetapi tidak menjadi sumber kebenaran.**

Pipeline:

```text
SOURCE
  ↓
EVIDENCE
  ↓
CLAIM
  ↓
REVIEW
  ↓
WRITING
  ↓
CITATION VALIDATION
  ↓
PUBLICATION
```

Bukan:

```text
AI
 ↓
Generate
 ↓
Publish
```

---

# 47.3 Content Entity

Tambahkan entitas utama:

```sql
CREATE TABLE publications (
    id UUID PRIMARY KEY,

    project_id UUID,

    title TEXT NOT NULL,

    slug TEXT UNIQUE NOT NULL,

    content_type VARCHAR(50),

    status VARCHAR(30) DEFAULT 'DRAFT',

    language VARCHAR(10) DEFAULT 'id',

    created_by UUID,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 47.4 Publication Status

```text
DRAFT
      ↓
EDITORIAL_REVIEW
      ↓
FACT_CHECK
      ↓
CITATION_CHECK
      ↓
APPROVED
      ↓
PUBLISHED
      ↓
ARCHIVED
```

Tidak boleh:

```text
DRAFT → PUBLISHED
```

untuk mode scholarly tanpa melewati validation.

---

# 47.5 Content Types

```text
HADITH_COMMENTARY
FATHUL_BARI_SUMMARY
SCHOLAR_PROFILE
HADITH_TOPIC
COMPARATIVE_STUDY
RESEARCH_ARTICLE
FAQ
GLOSSARY
TIMELINE
```

---

# 47.6 Publication Version

Setiap artikel memiliki versi.

```sql
CREATE TABLE publication_versions (
    id UUID PRIMARY KEY,

    publication_id UUID NOT NULL,

    version_number INTEGER NOT NULL,

    content TEXT,

    content_hash TEXT,

    created_by UUID,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    change_summary TEXT
);
```

Contoh:

```text
Artikel v1
Artikel v2
Artikel v3
```

---

# 47.7 Kenapa Versioning Penting?

Misalnya artikel:

> "Makna niat menurut Ibn Hajar"

versi pertama:

```text
v1
```

Kemudian ditemukan manuskrip/edisi sumber yang lebih baik.

Jangan overwrite.

```text
v1 → v2 → v3
```

Sehingga pembaca dan auditor dapat mengetahui perubahan.

---

# 47.8 Content Blocks

Jangan menyimpan artikel hanya sebagai satu string panjang.

Gunakan block structure:

```text
Publication
│
├── Introduction
├── Hadith
├── Translation
├── Syarah
├── Scholarly Opinions
├── Analysis
├── Conclusion
└── References
```

---

# 47.9 Block Schema

```sql
CREATE TABLE publication_blocks (
    id UUID PRIMARY KEY,

    publication_version_id UUID NOT NULL,

    block_order INTEGER,

    block_type VARCHAR(50),

    content TEXT,

    metadata JSONB
);
```

---

# 47.10 Block Types

```text
HEADING
PARAGRAPH
QUOTE
HADITH
QURAN_VERSE
SYARAH
SCHOLAR_OPINION
TABLE
TIMELINE
CALLOUT
FOOTNOTE
REFERENCE
```

---

# 47.11 Evidence Binding

Setiap block dapat dikaitkan dengan evidence.

```text
Block
  │
  ├── Source P001
  ├── Source P002
  └── Hadith H001
```

Database:

```sql
CREATE TABLE publication_evidence (
    publication_block_id UUID,

    evidence_type VARCHAR(50),

    evidence_id UUID,

    relation VARCHAR(50)
);
```

---

# 47.12 Evidence Relations

```text
SUPPORTED_BY
QUOTED_FROM
DERIVED_FROM
COMPARES_WITH
CONTRASTS_WITH
MENTIONS
```

---

# 47.13 Claim Binding

Artikel juga harus terhubung dengan claim.

```text
Paragraph
   ↓
Claim C001
   ↓
Evidence P001
```

Dengan demikian sistem dapat memeriksa:

> Apakah paragraf ini memiliki dasar sumber?

---

# 47.14 Publication Graph

Knowledge Graph diperluas:

```text
Publication
    │
    ├── contains → Claim
    ├── cites → Source
    ├── discusses → Hadith
    ├── discusses → Scholar
    ├── derives_from → Research Project
    └── reviewed_by → Reviewer
```

---

# 47.15 AI Writing Assistant

AI mendapatkan mode baru:

```text
WRITE
REWRITE
SUMMARIZE
EXPAND
SIMPLIFY
COMPARE
TRANSLATE
CITATION_ASSIST
```

Tetapi AI harus bekerja **berdasarkan evidence project**.

---

# 47.16 Generate Draft

Contoh:

```text
User:
Buat draft pembahasan mengenai makna niat
berdasarkan evidence yang sudah diverifikasi.
```

AI:

```text
Evidence
   ↓
Claims
   ↓
Outline
   ↓
Draft
```

---

# 47.17 AI Must Not Invent Sources

Prompt internal:

```text
Gunakan hanya evidence yang tersedia.

Jangan:
- membuat kitab
- membuat nomor halaman
- membuat kutipan
- membuat nama ulama
- membuat sanad
- membuat pendapat yang tidak terdapat dalam evidence

Jika evidence tidak cukup:
tandai [EVIDENCE_REQUIRED].
```

---

# 47.18 Evidence Required Marker

Jika AI tidak memiliki dasar:

```text
[EVIDENCE_REQUIRED]
```

Contoh:

> Ibn Hajar menyatakan bahwa ... **[EVIDENCE_REQUIRED]**

Editor kemudian dapat mencari sumber.

---

# 47.19 Automatic Citation Insertion

AI dapat menyarankan:

```text
Menurut Ibn Hajar ... [C001]
```

Tetapi citation belum otomatis dianggap valid.

Pipeline:

```text
AI Suggestion
      ↓
Citation Validator
      ↓
Human Review
      ↓
Approved
```

---

# 47.20 Citation Style

Sediakan:

```text
FOOTNOTE
ENDNOTE
INLINE
NUMBERED
ACADEMIC
SIMPLE
```

Contoh:

```text
Ibn Hajar menjelaskan bahwa... [1]

[1] Ibn Hajar al-'Asqalani,
Fath al-Bari, ...
```

---

# 47.21 Bibliography Engine

Buat:

```sql
CREATE TABLE publication_references (
    id UUID PRIMARY KEY,

    publication_id UUID,

    source_id UUID,

    citation_key TEXT,

    citation_text TEXT,

    order_number INTEGER
);
```

---

# 47.22 Bibliography Output

```text
Daftar Pustaka

1. Ibn Hajar al-'Asqalani.
   Fath al-Bari bi Sharh Sahih al-Bukhari.

2. ...
```

---

# 47.23 Citation Consistency Checker

Validator memeriksa:

```text
Citation exists?
       ↓
Source exists?
       ↓
Page exists?
       ↓
Passage exists?
       ↓
Citation supports claim?
```

Jika gagal:

```text
⚠ Citation requires review
```

---

# 47.24 Editorial Review

Buat review status:

```text
CONTENT_REVIEW
FACT_REVIEW
CITATION_REVIEW
LANGUAGE_REVIEW
FINAL_REVIEW
```

---

# 47.25 Reviewer Dashboard

```text
┌───────────────────────────────────────────────┐
│ PUBLICATION REVIEW                            │
├───────────────────────────────────────────────┤
│ Makna Niat dalam Fathul Bari                 │
│                                               │
│ Content       ✓                              │
│ Facts         ✓                              │
│ Citation      ⚠ 2 issues                     │
│ Attribution  ✓                              │
│ Language      ✓                              │
│                                               │
│ [Approve] [Request Revision] [Reject]        │
└───────────────────────────────────────────────┘
```

---

# 47.26 Review Comment

Reviewer dapat menyorot bagian tertentu:

```text
"Pendapat ini belum memiliki citation."
```

Terhubung ke:

```text
publication_block
claim
evidence
```

---

# 47.27 Editorial Issue

```sql
CREATE TABLE editorial_issues (
    id UUID PRIMARY KEY,

    publication_id UUID,

    block_id UUID,

    issue_type VARCHAR(50),

    severity VARCHAR(20),

    description TEXT,

    status VARCHAR(30),

    created_by UUID,

    resolved_by UUID,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 47.28 Issue Types

```text
MISSING_CITATION
INVALID_CITATION
UNSUPPORTED_CLAIM
ATTRIBUTION_ERROR
TRANSLATION_ISSUE
OCR_ISSUE
TYPO
AMBIGUOUS_STATEMENT
NEEDS_REVIEW
```

---

# 47.29 Severity

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Contoh:

```text
FALSE_ATTRIBUTION = CRITICAL
TYPO = LOW
```

---

# 47.30 Publication Quality Gate

Artikel hanya dapat dipublikasikan jika:

```text
[✓] No critical issues
[✓] All claims reviewed
[✓] All citations validated
[✓] Attribution validated
[✓] Source references available
[✓] Final reviewer approved
```

---

# 47.31 Publication API

Tambahkan:

```http
POST   /api/v1/publications
GET    /api/v1/publications
GET    /api/v1/publications/{id}

POST   /api/v1/publications/{id}/versions

POST   /api/v1/publications/{id}/review

GET    /api/v1/publications/{id}/issues

POST   /api/v1/publications/{id}/publish

POST   /api/v1/publications/{id}/archive
```

---

# 47.32 Public Reader

Setelah published:

```text
/app
   ↓
/research
   ↓
/publications
   ↓
/publication/{slug}
```

Reader:

```text
┌───────────────────────────────────────────────┐
│ Makna Niat dalam Fathul Bari                 │
│                                               │
│ Hadis                                         │
│ ───────────────────────────────────────────   │
│                                               │
│ Syarah Ibn Hajar                             │
│                                               │
│ ...                                           │
│                                               │
│ [1] Fathul Bari...                           │
│                                               │
│ Sources                                      │
└───────────────────────────────────────────────┘
```

---

# 47.33 Evidence Tooltip

Ketika pembaca mengklik:

```text
[Ibn Hajar menjelaskan...]
```

muncul:

```text
┌─────────────────────────────────────┐
│ SOURCE                              │
│                                     │
│ Fathul Bari                         │
│ Vol. 1                              │
│ p. 184                              │
│                                     │
│ Open Source →                       │
└─────────────────────────────────────┘
```

Ini akan menjadi salah satu fitur pembeda utama aplikasi.

---

# 47.34 "Show Evidence"

Tombol:

```text
[Show Evidence]
```

membuka:

```text
AI/Article Claim
       ↓
Original Passage
       ↓
Source Page
```

---

# 47.35 Evidence Transparency

Pembaca dapat mengetahui:

```text
This paragraph is based on:

✓ Fathul Bari
✓ Sahih Bukhari
✓ Ibn Hajar
```

Bukan sekadar membaca artikel AI tanpa sumber.

---

# 47.36 Public API

Publikasi yang sudah approved dapat diekspos:

```http
GET /api/v1/public/hadith/{id}

GET /api/v1/public/syarah/{id}

GET /api/v1/public/publications/{slug}

GET /api/v1/public/scholars/{id}
```

---

# 47.37 API Response

```json
{
  "title": "Makna Niat dalam Fathul Bari",

  "status": "PUBLISHED",

  "version": 3,

  "blocks": [],

  "references": [],

  "evidence": [],

  "updated_at": "2026-08-13"
}
```

---

# 47.38 Publication Metadata

Tambahkan:

```text
title
subtitle
author
editor
reviewer
language
topics
scholars
hadith_ids
sources
publication_date
updated_date
version
```

---

# 47.39 SEO Metadata

Untuk public reader:

```text
meta_title
meta_description
canonical_url
og_title
og_description
og_image
```

Tetapi metadata tidak boleh menghilangkan identitas sumber.

---

# 47.40 Structured Data

Gunakan schema sesuai jenis konten:

```text
Article
ScholarlyArticle
Book
Person
Dataset
```

Untuk artikel penelitian, metadata dapat mencantumkan:

```text
author
citation
datePublished
dateModified
```

---

# 47.41 Search Index

Publication yang sudah:

```text
APPROVED
```

dapat masuk search index.

Yang masih:

```text
DRAFT
```

tidak boleh muncul dalam public search.

---

# 47.42 Publication Search

Query:

> "niat"

Hasil:

```text
Publications
Hadith
Scholars
Topics
Sources
```

Ranking:

```text
Exact title
↓
Exact phrase
↓
Semantic relevance
↓
Evidence quality
```

---

# 47.43 Publication → Research Project

Setiap artikel harus dapat ditelusuri kembali:

```text
Publication
    ↓
Research Project
    ↓
Claims
    ↓
Evidence
    ↓
Original Source
```

---

# 47.44 Public → Private Boundary

Ini sangat penting.

```text
PRIVATE RESEARCH
       │
       ▼
EDITORIAL REVIEW
       │
       ▼
APPROVED CONTENT
       │
       ▼
PUBLIC
```

Tidak boleh:

```text
Private annotation
      ↓
Public
```

secara tidak sengaja.

---

# 47.45 Publication Audit Trail

Catat:

```text
created
edited
submitted
reviewed
approved
published
updated
archived
```

Contoh:

```json
{
  "action": "PUBLISH",
  "publication_id": "PUB-001",
  "version": 3,
  "approved_by": "USER-REVIEWER",
  "timestamp": "..."
}
```

---

# 47.46 Content Provenance

Setiap publikasi menyimpan:

```text
Corpus version
Research version
RAG version
Prompt version
Model version
Citation version
Reviewer version
```

Dengan demikian:

> Artikel yang terbit hari ini dapat ditelusuri kembali ke evidence yang digunakan saat artikel dibuat.

---

# 47.47 Publication Snapshot

Saat publish:

```text
PUB-001
   │
   ├── Research Snapshot
   ├── Source Snapshot
   ├── Evidence Snapshot
   ├── Citation Snapshot
   └── AI Provenance
```

---

# 47.48 Immutable Published Version

Setelah publish:

```text
v3 = IMMUTABLE
```

Jika ada koreksi:

```text
v4
```

bukan mengubah v3.

---

# 47.49 Correction Workflow

```text
Published v3
      ↓
Correction identified
      ↓
Editorial issue
      ↓
Review
      ↓
Create v4
      ↓
Publish v4
```

Riwayat tetap terlihat.

---

# 47.50 Correction Notice

Jika koreksi material:

```text
⚠ Artikel ini diperbarui pada 13 Agustus 2026.

Perubahan:
- Perbaikan citation
- Koreksi atribusi
```

---

# 47.51 AI Generated Label

Konten yang menggunakan AI dapat diberi metadata:

```text
AI_ASSISTED
```

Tetapi jangan menganggap:

```text
AI_ASSISTED = UNVERIFIED
```

Yang menentukan status adalah:

```text
review + evidence + citation validation
```

---

# 47.52 Content Generation Pipeline

```text
Research Project
      ↓
Select Evidence
      ↓
Select Claims
      ↓
Generate Outline
      ↓
Generate Draft
      ↓
Citation Validator
      ↓
Attribution Validator
      ↓
Human Review
      ↓
Fact Review
      ↓
Publish
```

---

# 47.53 One-Click Research Article

Di Research Workspace:

```text
[Create Article]
```

Dialog:

```text
Title:
[________________________]

Content type:
[Research Article ▼]

Evidence:
☑ Selected evidence
☑ Claims
☑ Citations

Language:
[Indonesia ▼]

[Generate Draft]
```

---

# 47.54 AI Outline

AI menghasilkan:

```text
1. Pendahuluan
2. Teks Hadis
3. Makna Hadis
4. Penjelasan Ibn Hajar
5. Pendapat Ulama
6. Analisis
7. Kesimpulan
8. Referensi
```

Outline harus bisa diedit sebelum drafting.

---

# 47.55 Controlled Generation

AI tidak boleh menambahkan section yang tidak diminta tanpa penanda.

Gunakan:

```text
Evidence-backed section
```

dan:

```text
Interpretive section
```

---

# 47.56 Distinguish Fact vs Analysis

Format:

```text
SUMBER MENYATAKAN
```

vs:

```text
ANALISIS
```

Ini sangat penting untuk mencegah pembaca mengira interpretasi sistem sebagai perkataan ulama.

---

# 47.57 Example

```text
### Penjelasan Ibn Hajar

Ibn Hajar menjelaskan bahwa ... [C001]

### Analisis

Berdasarkan penjelasan tersebut, dapat dipahami bahwa ...
```

---

# 47.58 Publication Quality Score

Gunakan indikator:

```text
Evidence Coverage
Citation Coverage
Attribution Accuracy
Editorial Completeness
Source Quality
```

Contoh:

```text
Publication Quality

Evidence       98%
Citation       100%
Attribution   100%
Editorial       96%

STATUS: READY
```

---

# 47.59 Definition of Done

Stage 47 selesai jika:

```text
[ ] Publication Entity
[ ] Publication Versioning
[ ] Content Blocks
[ ] Evidence Binding
[ ] Claim Binding
[ ] AI Writing Assistant
[ ] Citation Assistant
[ ] Bibliography Engine
[ ] Editorial Workflow
[ ] Review Comments
[ ] Editorial Issues
[ ] Publication Quality Gate
[ ] Public Reader
[ ] Evidence Tooltip
[ ] Public API
[ ] SEO Metadata
[ ] Publication Search
[ ] Provenance
[ ] Immutable Versions
[ ] Correction Workflow
[ ] Audit Trail
[ ] AI-Assisted Metadata
[ ] Research → Publication Pipeline
```

---

# 47.60 Arsitektur Setelah Stage 47

```text
                         ┌──────────────┐
                         │ HADITH API   │
                         └──────┬───────┘
                                │
                                ▼
                     ┌───────────────────┐
                     │ SOURCE CORPUS     │
                     │ Hadith/Fath Bari  │
                     └─────────┬─────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │ RAG / KNOWLEDGE   │
                     │ GRAPH / EVIDENCE  │
                     └─────────┬─────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │ RESEARCH WORKSPACE│
                     │ Stage 44          │
                     └─────────┬─────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │ QUALITY CONTROL   │
                     │ Stage 45          │
                     └─────────┬─────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │ PUBLICATION       │
                     │ Stage 47          │
                     └─────────┬─────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
             Reader         Public API      Export
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                    SCHOLARLY KNOWLEDGE
```

## Target akhir Stage 47

Dengan tahap ini, aplikasi Anda memiliki siklus lengkap:

```text
AMBIL HADIS
     ↓
TEMUKAN SYARAH
     ↓
VERIFIKASI SUMBER
     ↓
BANGUN EVIDENCE
     ↓
TELITI
     ↓
ANALISIS DENGAN RAG
     ↓
REVIEW
     ↓
TULIS
     ↓
VALIDASI CITATION
     ↓
EDITORIAL REVIEW
     ↓
PUBLISH
     ↓
PUBLIK DAPAT MELIHAT SUMBER ASLI
```

Dan yang paling penting, **artikel yang diterbitkan tetap mempunyai jalur balik ke hadis, passage Fathul Bari, claim, citation, evidence, reviewer, dan snapshot penelitian**. Jadi aplikasi ini tidak berubah menjadi sekadar *AI content generator*, melainkan tetap menjadi **platform penelitian dan publikasi syarah hadis yang auditable**.
