# Stage 25 — Research Document & Scholarly Publication Pipeline

Stage 25 mengubah **Research Workspace** menjadi lingkungan penulisan ilmiah end-to-end.

Targetnya:

```text
Hadis
  ↓
Fathul Bari
  ↓
Evidence
  ↓
Research Notes
  ↓
Findings
  ↓
Research Document
  ↓
Citation Validation
  ↓
Scholarly Review
  ↓
Final Manuscript
  ↓
PDF / DOCX / Markdown / HTML
```

Prinsip utama:

> **AI membantu menyusun dan menganalisis, tetapi setiap klaim ilmiah harus dapat ditelusuri ke evidence dan sumbernya.**

---

# 25.1 Arsitektur Stage 25

```text
┌─────────────────────────────────────────────────────────┐
│                 PUBLICATION PIPELINE                    │
├─────────────────────────────────────────────────────────┤
│ Research Document                                      │
│        ↓                                                │
│ Drafting Engine                                         │
│        ↓                                                │
│ Citation Resolver                                       │
│        ↓                                                │
│ Claim Verification                                      │
│        ↓                                                │
│ AI Review                                               │
│        ↓                                                │
│ Human Review                                            │
│        ↓                                                │
│ Publication                                             │
├─────────────────────────────────────────────────────────┤
│             RESEARCH WORKSPACE                          │
├─────────────────────────────────────────────────────────┤
│ RAG · Evidence · Knowledge Graph · Source Viewer       │
└─────────────────────────────────────────────────────────┘
```

---

# 25.2 Research Document

Kita sudah membuat model dasar pada Stage 24. Sekarang diperluas menjadi dokumen terstruktur.

Dokumen:

```text
Research Document
│
├── Metadata
├── Abstract
├── Introduction
├── Hadith
├── Syarah
├── Analysis
├── Findings
├── Discussion
├── Conclusion
├── References
└── Appendix
```

---

# 25.3 Document Metadata

```json
{
  "title": "Makna Niat dalam Fathul Bari",
  "subtitle": null,
  "language": "id",
  "document_type": "RESEARCH",
  "citation_style": "ISLAMIC_TRADITIONAL",
  "status": "DRAFT"
}
```

Document type:

```text
RESEARCH
ARTICLE
BOOK_CHAPTER
THESIS
LECTURE
SUMMARY
SYARAH
```

---

# 25.4 Document Status

Gunakan workflow:

```text
DRAFT
  ↓
IN_REVIEW
  ↓
REVISION_REQUIRED
  ↓
VERIFIED
  ↓
APPROVED
  ↓
PUBLISHED
  ↓
ARCHIVED
```

Jangan menggunakan satu boolean seperti:

```text
published = true
```

karena kita membutuhkan audit status.

---

# 25.5 Database Document Revision

```sql
CREATE TABLE research_document_revisions (
    id UUID PRIMARY KEY,

    document_id UUID NOT NULL
        REFERENCES research_documents(id),

    revision_number INTEGER NOT NULL,

    content JSONB NOT NULL,

    change_summary TEXT,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(document_id, revision_number)
);
```

Dengan ini:

```text
Revision 1
Revision 2
Revision 3
...
```

dapat dibandingkan.

---

# 25.6 Block-Based Editor

Saya sangat menyarankan editor berbasis block.

Contoh:

```json
{
  "type": "paragraph",
  "id": "block_001",
  "content": [...]
}
```

Jenis block:

```text
HEADING
PARAGRAPH
QUOTE
ARABIC_TEXT
HADITH
SHARH
FOOTNOTE
IMAGE
TABLE
LIST
CODE
CALLOUT
REFERENCE
```

---

# 25.7 Contoh Dokumen Internal

```json
{
  "blocks": [
    {
      "id": "b1",
      "type": "heading",
      "level": 1,
      "text": "Makna Niat"
    },
    {
      "id": "b2",
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Niat memiliki kedudukan penting..."
        },
        {
          "type": "citation",
          "citation_id": "cit_001"
        }
      ]
    }
  ]
}
```

Keuntungan:

* citation tidak rusak ketika teks diedit;
* footnote bisa direnumber;
* heading bisa dibuat otomatis;
* export menjadi lebih mudah.

---

# 25.8 Editor UI

Route:

```text
/research/documents/{documentId}
```

Layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ Document Title              [Save] [Review] [Export]        │
├─────────────┬───────────────────────────────┬───────────────┤
│ OUTLINE     │ DOCUMENT                      │ INSPECTOR     │
│             │                               │               │
│ Abstract    │ # Makna Niat                  │ Block         │
│ Hadis       │                               │ Citation      │
│ Syarah      │ إنما الأعمال بالنيات...       │ Evidence      │
│ Analysis    │                               │ Source        │
│ Findings    │ Menurut Ibn Hajar...¹         │               │
│ Conclusion  │                               │               │
│ References  │                               │               │
└─────────────┴───────────────────────────────┴───────────────┘
```

---

# 25.9 Outline Navigation

Heading otomatis membentuk:

```text
1. Pendahuluan
2. Hadis
3. Syarah Fathul Bari
   3.1 Makna Niat
   3.2 Hubungan Niat dan Amal
4. Analisis
5. Kesimpulan
```

Klik heading:

```text
→ scroll ke block
```

---

# 25.10 AI Drafting Assistant

AI tidak langsung menulis seluruh penelitian tanpa kontrol.

Gunakan mode:

```text
ASSIST
```

User memilih:

```text
[Generate Paragraph]
```

AI mendapatkan:

```text
workspace context
+
selected finding
+
evidence
+
citation rules
```

---

# 25.11 Contoh

User mempunyai Finding:

```text
Ibnu Hajar menjelaskan hubungan niat
dengan tujuan suatu amal.
```

Klik:

```text
Expand into paragraph
```

AI menghasilkan draft:

```text
Dalam pembahasan hadis tentang niat,
Ibnu Hajar menjelaskan bahwa ...
```

Citation otomatis:

```text
[Ibn Hajar, Fath al-Bari, 1:45]
```

Tetapi statusnya:

```text
AI_DRAFT
```

bukan:

```text
VERIFIED
```

---

# 25.12 AI Draft Provenance

Setiap paragraf hasil AI menyimpan:

```json
{
  "generated_by": "AI",
  "model": "configured-model",
  "generated_at": "...",
  "source_evidence": [
    "evidence_001",
    "evidence_002"
  ]
}
```

Dengan demikian kita tahu:

> bagian mana yang ditulis manusia dan mana yang dihasilkan AI.

---

# 25.13 Human vs AI Content

Block memiliki:

```text
origin
```

nilai:

```text
HUMAN
AI
IMPORTED
GENERATED_FROM_TEMPLATE
```

Contoh:

```json
{
  "origin": "AI",
  "review_status": "UNREVIEWED"
}
```

---

# 25.14 Claim Extraction

Ini fitur inti Stage 25.

Dari dokumen:

```text
Ibnu Hajar menjelaskan bahwa niat
membedakan tujuan suatu amal...
```

sistem mengekstrak:

```text
Claim #001

"Ibn Hajar explains that intention
distinguishes the purpose of an action."
```

Kemudian:

```text
Claim
 ↓
Citation
 ↓
Evidence
```

---

# 25.15 Claim Database

```sql
CREATE TABLE document_claims (
    id UUID PRIMARY KEY,

    document_id UUID NOT NULL
        REFERENCES research_documents(id),

    block_id UUID,

    claim_text TEXT NOT NULL,

    claim_type VARCHAR(40),

    status VARCHAR(30) DEFAULT 'UNVERIFIED',

    confidence NUMERIC(6,5),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Claim type:

```text
FACTUAL
INTERPRETIVE
HISTORICAL
LINGUISTIC
THEOLOGICAL
COMPARATIVE
OPINION
```

---

# 25.16 Claim Verification

Dashboard:

```text
┌──────────────────────────────────────────────┐
│ CLAIM VERIFICATION                           │
├──────────────────────────────────────────────┤
│ Claim #001                                   │
│                                              │
│ "Ibnu Hajar menjelaskan..."                  │
│                                              │
│ Evidence                                     │
│ ✓ FB-V1-P45-C003                             │
│                                              │
│ Citation                                     │
│ ✓ Ibn Hajar, Fath al-Bari, 1:45             │
│                                              │
│ Status: SUPPORTED                            │
│                                              │
│ [Verify] [Reject] [Edit]                     │
└──────────────────────────────────────────────┘
```

---

# 25.17 Claim Support Levels

Gunakan:

```text
DIRECT
INDIRECT
PARTIAL
CONTRADICTED
UNSUPPORTED
```

Contoh:

```text
DIRECT
```

berarti sumber secara jelas menyatakan claim tersebut.

```text
INDIRECT
```

berarti claim merupakan inferensi.

Ini jauh lebih berguna daripada sekadar confidence score.

---

# 25.18 Claim-Evidence Matrix

Buat tampilan:

```text
                  Evidence
Claim          E1   E2   E3
────────────────────────────
C1             ✓
C2                  ✓    ✓
C3             ✓
C4                       ⚠
```

Dengan:

```text
✓ DIRECT
◐ INDIRECT
⚠ PARTIAL
✕ CONTRADICTED
```

---

# 25.19 Citation Coverage Dashboard

Dashboard dokumen:

```text
Citation Coverage

██████████████████░░ 91%

Total claims       34
Supported          31
Partial             2
Unsupported         1
```

Klik:

```text
Unsupported: 1
```

langsung menuju claim.

---

# 25.20 AI Review

Tambahkan:

```text
[Run Scholarly Review]
```

AI memeriksa:

```text
1. Unsupported claims
2. Missing citations
3. Citation mismatch
4. Source mismatch
5. Overstatement
6. Contradictory sources
7. Duplicate claims
8. Unsupported chronology
9. Hallucinated references
```

---

# 25.21 AI Review Result

```text
SCHOLARLY REVIEW

✓ 27 claims supported
⚠ 3 claims need review
✕ 1 claim unsupported
⚠ 2 citations need verification
```

Contoh:

```text
Claim #18

"Menurut Ibnu Hajar..."

⚠ Citation exists, but evidence does not
directly support the complete statement.

[Open Claim]
[Open Evidence]
```

---

# 25.22 Jangan Gunakan AI sebagai Hakim Final

Status:

```text
AI_REVIEWED
```

berbeda dari:

```text
HUMAN_VERIFIED
```

Workflow:

```text
AI Review
    ↓
Human Review
    ↓
Verified
```

Ini penting untuk menjaga integritas ilmiah.

---

# 25.23 Scholarly Review Queue

Route:

```text
/research/review
```

Tampilan:

```text
┌──────────────────────────────────────────────┐
│ REVIEW QUEUE                                 │
├──────────────────────────────────────────────┤
│ 12 claims awaiting verification              │
│                                              │
│ #001  ✓ Supported                            │
│ #002  ⚠ Partial                              │
│ #003  ✕ Unsupported                          │
│ #004  ⚠ Citation mismatch                    │
└──────────────────────────────────────────────┘
```

---

# 25.24 Reviewer Actions

Reviewer dapat:

```text
VERIFY
REJECT
REQUEST_REVISION
MARK_PARTIAL
LINK_EVIDENCE
CHANGE_CITATION
```

Setiap action masuk audit trail.

---

# 25.25 Review Comment

Reviewer dapat menambahkan:

```text
"Evidence ini hanya mendukung bagian pertama
dari klaim. Pisahkan menjadi dua klaim."
```

Database:

```sql
CREATE TABLE review_comments (
    id UUID PRIMARY KEY,

    document_id UUID NOT NULL
        REFERENCES research_documents(id),

    claim_id UUID,

    block_id UUID,

    reviewer_id UUID,

    comment TEXT NOT NULL,

    status VARCHAR(30) DEFAULT 'OPEN',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 25.26 Revision Request

Jika reviewer menolak:

```text
REQUEST_REVISION
```

misalnya:

```text
Claim #17

Reason:
Citation does not directly support the claim.

Required action:
Reduce the claim to what is explicitly stated
in Fath al-Bari.
```

Author memperbaiki.

---

# 25.27 Review Cycle

```text
Draft
 ↓
Submit Review
 ↓
AI Review
 ↓
Human Review
 ↓
Revision Required
 ↓
Author Revision
 ↓
Human Review
 ↓
Approved
```

Tidak ada batas jumlah cycle.

---

# 25.28 Submission Snapshot

Ketika dokumen dikirim untuk review:

```text
document_revision = 12
```

Reviewer harus melihat snapshot revision 12.

Jika author mengedit menjadi revision 13:

```text
Review #1 → revision 12
Current    → revision 13
```

UI:

```text
⚠ Document changed after review submission.
```

Ini mencegah reviewer secara tidak sengaja memverifikasi versi yang berbeda.

---

# 25.29 Publication Snapshot

Saat approved:

```text
Publication Snapshot
```

menyimpan:

```text
document revision
source versions
citation versions
evidence hashes
review status
```

Sehingga publikasi dapat direproduksi.

---

# 25.30 Publication Database

```sql
CREATE TABLE publications (
    id UUID PRIMARY KEY,

    document_id UUID NOT NULL
        REFERENCES research_documents(id),

    revision_id UUID NOT NULL,

    title TEXT NOT NULL,

    status VARCHAR(30) DEFAULT 'PUBLISHED',

    snapshot JSONB NOT NULL,

    published_at TIMESTAMPTZ,

    published_by UUID
);
```

Status:

```text
READY
PUBLISHED
UNPUBLISHED
ARCHIVED
```

---

# 25.31 Publication ID

Setiap publikasi memperoleh:

```text
PUB-2026-000001
```

atau UUID.

Contoh:

```text
PUB-2026-000001
```

---

# 25.32 DOI-Ready Architecture

Jangan langsung mengklaim DOI.

Tetapi siapkan metadata:

```json
{
  "title": "...",
  "authors": [],
  "publisher": "Almaktaba Research",
  "publication_date": "2026-08-13",
  "version": "1.0",
  "language": "id",
  "keywords": []
}
```

Nanti dapat dihubungkan ke layanan DOI yang sesuai.

---

# 25.33 Publication Metadata

```text
Title
Authors
Abstract
Keywords
Language
Version
Publication Date
License
Publisher
Identifier
```

---

# 25.34 License

Pilihan:

```text
ALL_RIGHTS_RESERVED
CC_BY
CC_BY_SA
CC_BY_NC
CC_BY_NC_SA
CUSTOM
```

---

# 25.35 Public Research Page

Nantinya publikasi dapat mempunyai URL:

```text
/research/publications/PUB-2026-000001
```

Tampilan:

```text
┌───────────────────────────────────────────────┐
│ Makna Niat dalam Fathul Bari                  │
│                                               │
│ Zhoel Bzone                                  │
│ Published: 13 August 2026                     │
│ Version 1.0                                   │
├───────────────────────────────────────────────┤
│ Abstract                                      │
│ ...                                           │
│                                               │
│ Hadith                                        │
│ ...                                           │
│                                               │
│ Analysis                                      │
│ ...                                           │
├───────────────────────────────────────────────┤
│ References                                    │
│ ...                                           │
└───────────────────────────────────────────────┘
```

---

# 25.36 Public Evidence Links

Citation publik:

```text
Ibn Hajar, Fath al-Bari, 1:45.
```

dapat memiliki:

```text
[View Source]
```

Jika source memang boleh ditampilkan.

Jika tidak:

```text
[View Citation Metadata]
```

Jangan otomatis mempublikasikan PDF berhak cipta.

---

# 25.37 Copyright Boundary

Source Viewer harus membedakan:

```text
PUBLIC_DOMAIN
LICENSED
USER_PROVIDED
RESTRICTED
UNKNOWN
```

Publication pipeline tidak boleh otomatis menyalin teks panjang dari source berhak cipta.

Yang dapat dipublikasikan:

```text
citation
metadata
short quotation
user's analysis
```

sesuai hak penggunaan sumber.

---

# 25.38 AI Writing Guardrails

Prompt system untuk drafting:

```text
Anda adalah research writing assistant.

Aturan:
1. Jangan membuat referensi.
2. Jangan membuat nomor halaman.
3. Jangan membuat nomor hadis.
4. Jangan mengatributkan pendapat tanpa evidence.
5. Bedakan kutipan langsung dan parafrasa.
6. Jika evidence tidak cukup, nyatakan bahwa evidence tidak cukup.
7. Jangan mengubah makna sumber.
8. Pertahankan citation provenance.
```

---

# 25.39 Direct Quote Protection

Jika user memasukkan:

```text
قوله إنما الأعمال بالنيات
```

sistem memberi metadata:

```json
{
  "type": "quote",
  "source_id": "...",
  "citation_id": "...",
  "verified": true
}
```

Jangan menganggap semua teks yang ditempel user berasal dari source.

---

# 25.40 Quote Verification

Flow:

```text
Quote
 ↓
Compare source
 ↓
Exact match?
 ├── YES → VERIFIED_QUOTE
 ├── CLOSE → REVIEW
 └── NO → INVALID
```

Untuk bahasa Arab, gunakan normalisasi:

```text
Unicode normalization
diacritics handling
whitespace normalization
```

tetapi tetap simpan teks asli.

---

# 25.41 Document Linter

Tambahkan **Scholarly Linter**.

Contoh warning:

```text
⚠ Claim without citation
⚠ Citation has no page
⚠ Citation source not verified
⚠ AI-generated paragraph not reviewed
⚠ Quote not source-verified
⚠ Finding has insufficient evidence
```

Command:

```text
[Run Document Audit]
```

---

# 25.42 Audit Score

Contoh:

```text
DOCUMENT QUALITY

Citation Coverage      94%
Source Verification    98%
Quote Verification     100%
AI Content Reviewed    91%
Claim Support          93%

Overall:
92 / 100
```

Jangan menyebut ini sebagai "kebenaran ilmiah"; ini hanya **internal quality-control score**.

---

# 25.43 Export Pipeline

```text
Document
   ↓
Normalize Blocks
   ↓
Resolve Citations
   ↓
Validate Claims
   ↓
Generate Footnotes
   ↓
Generate Bibliography
   ↓
Render
   ↓
Output
```

Output:

```text
PDF
DOCX
Markdown
HTML
```

---

# 25.44 DOCX Structure

Hasil DOCX:

```text
Title
Author

Abstract

1. Introduction

2. Hadith

Arabic text

Translation

3. Fathul Bari

...

4. Analysis

...

Footnotes

Bibliography
```

Citation tetap sebagai footnote, bukan sekadar teks biasa.

---

# 25.45 PDF Structure

```text
Cover
Abstract
Table of Contents
Body
Footnotes
References
Appendix
```

PDF menyimpan metadata:

```text
Title
Author
Creation Date
Application
Publication ID
```

---

# 25.46 Publication Audit Trail

Timeline:

```text
08:30 Draft created
09:10 AI review
09:30 Submitted for review
10:15 Reviewer requested revision
11:00 Revision 2
11:30 Reviewer approved
12:00 Published
```

---

# 25.47 API

### Create document

```http
POST /api/v1/research/documents
```

### Update

```http
PATCH /api/v1/research/documents/{id}
```

### Submit review

```http
POST /api/v1/research/documents/{id}/submit-review
```

### AI review

```http
POST /api/v1/research/documents/{id}/ai-review
```

### Claims

```http
GET /api/v1/research/documents/{id}/claims
```

### Verify claim

```http
POST /api/v1/research/claims/{claim_id}/verify
```

### Publish

```http
POST /api/v1/research/documents/{id}/publish
```

### Export

```http
POST /api/v1/research/documents/{id}/export
```

---

# 25.48 AI Review Response

Contoh:

```json
{
  "document_id": "doc_001",
  "revision": 12,

  "summary": {
    "claims": 34,
    "supported": 31,
    "partial": 2,
    "unsupported": 1
  },

  "issues": [
    {
      "claim_id": "claim_018",
      "severity": "HIGH",
      "type": "UNSUPPORTED_CLAIM",
      "message": "Evidence does not directly support the complete claim."
    }
  ]
}
```

---

# 25.49 Publication Gate

Sebelum publish:

```text
┌─────────────────────────────────────────────┐
│ PUBLICATION CHECK                           │
├─────────────────────────────────────────────┤
│ ✓ No critical citation errors               │
│ ✓ All quotes verified                       │
│ ✓ Claims reviewed                            │
│ ✓ Bibliography generated                    │
│ ✓ Document revision locked                  │
│ ✓ Source snapshot created                   │
│                                             │
│             [PUBLISH]                       │
└─────────────────────────────────────────────┘
```

Jika ada critical error:

```text
[PUBLISH] disabled
```

---

# 25.50 Publication Snapshot

Snapshot:

```json
{
  "document_revision": 12,

  "citations": [
    {
      "id": "cit_001",
      "version": 2,
      "content_hash": "..."
    }
  ],

  "evidence": [
    {
      "id": "ev_001",
      "content_hash": "..."
    }
  ],

  "review": {
    "status": "APPROVED",
    "reviewer_count": 1
  }
}
```

---

# 25.51 Kenapa Snapshot Sangat Penting?

Misalnya hari ini:

```text
Fathul Bari p.45
```

memiliki OCR:

```text
"... الأعمال بالنيات ..."
```

enam bulan kemudian corpus diperbaiki:

```text
"... إنما الأعمال بالنيات ..."
```

Publikasi lama tetap menunjukkan:

```text
Source snapshot:
hash ABC123
```

sedangkan corpus terbaru:

```text
hash DEF456
```

Kita dapat mengetahui bahwa sumber berubah.

---

# 25.52 Definition of Done

Stage 25 selesai apabila:

```text
[x] Research document
[x] Block editor
[x] Document revisions
[x] Outline
[x] AI drafting assistant
[x] AI provenance
[x] Claim extraction
[x] Claim database
[x] Claim-evidence matrix
[x] Claim verification
[x] AI scholarly review
[x] Human review
[x] Review comments
[x] Revision workflow
[x] Submission snapshot
[x] Publication metadata
[x] Publication snapshot
[x] Publication ID
[x] Public research page
[x] Document linter
[x] Quality dashboard
[x] Copyright-aware source handling
[x] Quote verification
[x] PDF export
[x] DOCX export
[x] Markdown export
[x] Publication audit trail
```

---

# 25.53 Milestone Arsitektur

Setelah Stage 25, aplikasi kita sudah mempunyai pipeline:

```text
                 ┌───────────────┐
                 │ Ahmad Sanusi  │
                 │ Hadits API    │
                 └───────┬───────┘
                         │
                         ▼
                    HADITH DATA
                         │
                         ▼
                ┌─────────────────┐
                │ KNOWLEDGE GRAPH │
                └────────┬────────┘
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
        FATHUL BARI               SOURCES
             │                       │
             └───────────┬───────────┘
                         ▼
                       RAG
                         │
                         ▼
                     EVIDENCE
                         │
                         ▼
                 RESEARCH WORKSPACE
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
           NOTES      FINDINGS     COMPARE
             │           │           │
             └───────────┼───────────┘
                         ▼
                RESEARCH DOCUMENT
                         │
                         ▼
                 CLAIM VERIFICATION
                         │
                         ▼
                  SCHOLARLY REVIEW
                         │
                         ▼
                     PUBLISH
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
            PDF         DOCX       WEB
```
