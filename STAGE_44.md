# Stage 44 — Research Workspace & Scholarly Annotation

Karena **Stage 43 (Takhrij & Hadith Chain Intelligence)** Anda putuskan tidak diperlukan, kita lanjutkan langsung ke **Stage 44**.

Fokus Stage 44 adalah mengubah aplikasi dari sekadar mesin pencarian/syarah menjadi **workspace penelitian ilmiah** tempat pengguna dapat membaca, menandai, membandingkan, memberi catatan, dan membangun argumen berbasis sumber.

---

## 44.1 Tujuan Stage 44

Pengguna harus bisa melakukan alur:

```text
Cari Hadis
   ↓
Buka Fathul Bari
   ↓
Baca Syarah
   ↓
Highlight teks
   ↓
Tambahkan anotasi
   ↓
Hubungkan dengan Hadis / Ayat / Ulama
   ↓
Tambahkan catatan pribadi
   ↓
Simpan citation
   ↓
Masukkan ke Research Project
   ↓
Gunakan AI untuk menganalisis
   ↓
Export hasil penelitian
```

---

# 44.2 Arsitektur

```text
                 RESEARCH WORKSPACE
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Source Reader      Annotation       Research Notes
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  Evidence Library
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Claims      Citations    Entities
             │           │           │
             └───────────┼───────────┘
                         ▼
                    AI Assistant
                         │
                         ▼
                  Research Report
```

---

# 44.3 Research Project

Buat konsep **Project**.

Contoh:

```text
Project:
"Studi Syarah Hadis Niat"

├── Hadis
├── Fathul Bari passages
├── Annotations
├── Claims
├── Citations
├── Notes
├── Questions
└── AI analysis
```

---

# 44.4 Database

```sql
CREATE TABLE research_projects (
    id UUID PRIMARY KEY,

    name TEXT NOT NULL,

    description TEXT,

    user_id UUID NOT NULL,

    status VARCHAR(30) DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 44.5 Project Sources

```sql
CREATE TABLE project_sources (
    id UUID PRIMARY KEY,

    project_id UUID NOT NULL,

    source_type VARCHAR(50),

    source_id UUID,

    added_at TIMESTAMPTZ DEFAULT NOW(),

    metadata JSONB
);
```

Contoh:

```text
Project
   │
   ├── Fathul Bari
   ├── Sahih Bukhari
   ├── Qur'an
   └── Riyadhus Shalihin
```

---

# 44.6 Annotation

Annotation adalah highlight terhadap sumber.

```sql
CREATE TABLE annotations (
    id UUID PRIMARY KEY,

    project_id UUID NOT NULL,

    passage_id UUID NOT NULL,

    start_offset INTEGER,

    end_offset INTEGER,

    selected_text TEXT,

    annotation_type VARCHAR(50),

    note TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 44.7 Annotation Types

Gunakan:

```text
IMPORTANT
QUESTION
DEFINITION
EVIDENCE
ARGUMENT
COUNTER_ARGUMENT
LINGUISTIC
FIQH
HADITH
THEOLOGY
HISTORICAL
PERSON
REFERENCE
TODO
```

---

# 44.8 Highlight System

UI:

```text
┌───────────────────────────────────────────────┐
│ FATHUL BARI                                  │
│                                               │
│ ... قال ابن حجر ...                           │
│                                               │
│ ███████████████████████████████████          │
│ Highlighted passage                           │
│                                               │
│        [Annotate] [Ask AI] [Citation]         │
└───────────────────────────────────────────────┘
```

---

# 44.9 Annotation Menu

Ketika teks dipilih:

```text
┌─────────────────────────┐
│ Highlight               │
├─────────────────────────┤
│ Add Note                │
│ Add Citation            │
│ Ask AI                  │
│ Create Claim            │
│ Link Scholar            │
│ Link Hadith             │
│ Link Verse              │
│ Add to Project          │
└─────────────────────────┘
```

---

# 44.10 Annotation + Source

Setiap anotasi wajib menyimpan:

```text
project_id
passage_id
selected_text
source_location
created_by
created_at
```

Sehingga catatan tidak kehilangan konteks.

---

# 44.11 Permanent Anchor

Masalah penting:

Jika versi OCR diperbaiki, offset teks dapat berubah.

Jangan hanya menyimpan:

```text
start_offset
end_offset
```

Gunakan juga:

```text
passage_id
text_hash
selected_text
anchor_context
```

---

# 44.12 Annotation Anchor

```json
{
  "passage_id": "P88421",

  "selected_text": "إنما الأعمال بالنيات",

  "text_hash": "sha256...",

  "before": "قال رسول الله",

  "after": "وإنما لكل امرئ",

  "start_offset": 122,

  "end_offset": 145
}
```

Dengan demikian annotation dapat dipulihkan jika OCR berubah.

---

# 44.13 Annotation Recovery

Jika offset tidak cocok:

```text
Original anchor
      ↓
Search selected_text
      ↓
Search surrounding context
      ↓
Similarity matching
      ↓
New offset
```

Status:

```text
RESTORED
AMBIGUOUS
FAILED
```

---

# 44.14 Research Note

Buat:

```sql
CREATE TABLE research_notes (
    id UUID PRIMARY KEY,

    project_id UUID NOT NULL,

    title TEXT,

    content TEXT,

    note_type VARCHAR(40),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 44.15 Note Types

```text
GENERAL
SUMMARY
HYPOTHESIS
ARGUMENT
QUESTION
CONCLUSION
METHODOLOGY
TODO
```

---

# 44.16 Note ↔ Evidence

Jangan membuat catatan terisolasi.

Buat:

```sql
CREATE TABLE note_evidence (
    note_id UUID NOT NULL,

    evidence_type VARCHAR(50),

    evidence_id UUID NOT NULL,

    relation VARCHAR(50)
);
```

Contoh:

```text
NOTE
 │
 ├──SUPPORTED_BY → Citation C001
 ├──SUPPORTED_BY → Passage P002
 └──RELATED_TO → Hadith H001
```

---

# 44.17 Research Claims

User dapat membuat:

> "Ibn Hajar mengutamakan pendapat A dibandingkan pendapat B."

Simpan sebagai:

```text
CLAIM
```

Tetapi bedakan:

```text
SOURCE_CLAIM
USER_CLAIM
AI_CLAIM
```

---

# 44.18 Claim Status

```text
DRAFT
SUPPORTED
PARTIALLY_SUPPORTED
CONTRADICTED
UNVERIFIED
REJECTED
```

---

# 44.19 Claim Evidence Matrix

UI:

```text
┌──────────────────────────────────────────────┐
│ CLAIM                                       │
├──────────────────────────────────────────────┤
│ Ibn Hajar cenderung memilih pendapat A.    │
│                                              │
│ Evidence                                     │
│                                              │
│ ✓ Fathul Bari 1/184                         │
│ ✓ Fathul Bari 1/185                         │
│ ? Fathul Bari 1/190                         │
│                                              │
│ Support: 2                                   │
│ Contradiction: 0                             │
└──────────────────────────────────────────────┘
```

---

# 44.20 Evidence Strength

```text
DIRECT
STRONG
MODERATE
WEAK
INDIRECT
CONTRADICTORY
```

---

# 44.21 AI Research Assistant

AI tidak hanya menjawab pertanyaan umum.

Mode baru:

```text
Ask about selected text
Ask about project
Compare sources
Find contradictions
Summarize evidence
Find missing evidence
Generate research outline
```

---

# 44.22 Context Modes

User dapat memilih:

### Selected Passage

```text
AI hanya melihat teks yang dipilih.
```

### Current Page

```text
AI melihat halaman aktif.
```

### Current Chapter

```text
AI melihat seluruh bab.
```

### Current Project

```text
AI menggunakan semua evidence project.
```

### Entire Corpus

```text
AI melakukan retrieval global.
```

---

# 44.23 Research AI Guardrail

Prompt:

```text
Anda adalah Research Assistant.

Prioritaskan:
1. Sumber primer.
2. Kutipan yang dapat diverifikasi.
3. Atribusi yang tepat.
4. Citation.
5. Perbedaan antara sumber dan inferensi.

Jangan mengubah interpretasi menjadi kutipan.
Jangan membuat citation yang tidak ditemukan.
Jika evidence tidak cukup, katakan tidak cukup.
```

---

# 44.24 Ask AI on Selection

Contoh user highlight:

> وقال النووي...

Lalu:

**Ask AI → "Apa maksud pernyataan ini?"**

AI menerima:

```text
Selected text
+
Surrounding context
+
Source metadata
+
Attribution graph
```

---

# 44.25 Compare Sources

Fitur:

```text
Compare:
Fathul Bari
vs
Sahih Muslim
```

Output:

```text
                 Fathul Bari     Sahih Muslim
──────────────────────────────────────────────
Wording             X               Y
Narrator             A               A
Additional phrase    Yes             No
Commentary           Yes             No
```

---

# 44.26 Side-by-Side Reader

```text
┌──────────────────────┬──────────────────────┐
│ FATHUL BARI          │ HADIS                │
│                      │                      │
│ Arabic               │ Arabic               │
│                      │                      │
│ Translation          │ Translation          │
│                      │                      │
│ Commentary           │ Metadata             │
└──────────────────────┴──────────────────────┘
```

---

# 44.27 Synchronized Highlight

Jika hadis muncul di Fathul Bari:

```text
Hadith H001
     ↓
Fathul Bari Passage P001
```

Klik hadis:

```text
→ otomatis membuka lokasi syarah
```

---

# 44.28 Cross-Reference Panel

Panel:

```text
RELATED SOURCES

Hadith
├── Sahih Bukhari
├── Fathul Bari
└── Other sources

Scholars
├── Ibn Hajar
├── al-Nawawi
└── al-Khattabi

Topics
├── Niyyah
├── Amal
└── Ikhlas
```

---

# 44.29 Research Bookmark

Tambahkan:

```sql
CREATE TABLE research_bookmarks (
    id UUID PRIMARY KEY,

    project_id UUID NOT NULL,

    target_type VARCHAR(50),

    target_id UUID,

    title TEXT,

    note TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 44.30 Bookmark Types

```text
PASSAGE
PAGE
HADITH
SCHOLAR
CLAIM
ANNOTATION
SOURCE
```

---

# 44.31 Tags

Tambahkan:

```sql
CREATE TABLE research_tags (
    id UUID PRIMARY KEY,

    project_id UUID NOT NULL,

    name TEXT NOT NULL
);
```

Relasi:

```sql
CREATE TABLE research_tag_links (
    tag_id UUID,

    entity_type VARCHAR(50),

    entity_id UUID
);
```

Contoh:

```text
#niat
#ikhlas
#fiqh
#bahasa
#perbandingan
```

---

# 44.32 Search Project

User dapat mencari:

```text
"niat"
```

Hasil:

```text
Annotations: 17
Notes: 8
Claims: 5
Sources: 12
Hadith: 3
```

---

# 44.33 Semantic Search

Search tidak hanya keyword.

Contoh:

> "pendapat Ibn Hajar tentang perbedaan niat dan tujuan"

→ mencari:

```text
niyyah
qasd
murad
intent
purpose
```

menggunakan vector retrieval.

---

# 44.34 Research Timeline

Tampilkan aktivitas:

```text
13 Aug
│
├── Added Fathul Bari p.184
├── Highlighted passage
├── Created Claim #12
├── Added citation C031
└── Asked AI
```

---

# 44.35 Audit Trail

Semua perubahan:

```text
USER
 ↓
ACTION
 ↓
OBJECT
 ↓
OLD VALUE
 ↓
NEW VALUE
 ↓
TIMESTAMP
```

Contoh:

```json
{
  "action": "UPDATE_CLAIM",
  "object": "CLAIM-001",
  "old_status": "UNVERIFIED",
  "new_status": "SUPPORTED"
}
```

---

# 44.36 Collaboration

Untuk tahap ini, siapkan model:

```text
OWNER
EDITOR
REVIEWER
VIEWER
```

Walaupun fitur multi-user belum diaktifkan.

---

# 44.37 Review Workflow

```text
Draft
  ↓
Research
  ↓
Evidence collected
  ↓
Claim formulated
  ↓
Peer review
  ↓
Verified
  ↓
Published
```

---

# 44.38 Reviewer Comment

Reviewer dapat menulis:

> "Citation C004 tidak cukup untuk mendukung klaim ini."

Status:

```text
NEEDS_REVISION
```

---

# 44.39 Research Conflict

Jika reviewer berbeda pendapat:

```text
Claim
├── Evidence A
├── Evidence B
│
└── Reviewer disagreement
```

Jangan otomatis memilih salah satu.

---

# 44.40 Export Research

Project dapat diekspor menjadi:

```text
Markdown
PDF
DOCX
JSON
CSV
BibTeX
RIS
```

Struktur Markdown:

```markdown
# Studi Syarah Hadis Niat

## Hadis

...

## Syarah Ibn Hajar

...

## Temuan

...

## Claims

### Claim 1

...

### Evidence

- Fath al-Bari 1/184
- Fath al-Bari 1/185

## Kesimpulan

...
```

---

# 44.41 Citation Preservation

Ketika export, citation tidak boleh hilang.

Contoh:

```markdown
Ibn Hajar menjelaskan bahwa... [C001]

[C001]: Fath al-Bari, Vol. 1, p. 184,
Passage P88421.
```

---

# 44.42 Research Snapshot

Tambahkan kemampuan:

> **Freeze Research State**

Snapshot menyimpan:

```text
Corpus version
Model version
Prompt version
Sources
Claims
Annotations
Citations
Timestamp
```

Ini sangat penting untuk reproduksibilitas.

---

# 44.43 Research Version

```text
Project v1
Project v2
Project v3
```

Jika AI menghasilkan analisis berbeda setelah model berubah, user masih dapat melihat hasil lama.

---

# 44.44 AI Provenance

Setiap AI-generated content:

```json
{
  "model": "configured-model",
  "prompt_version": "research-v3",
  "retrieval_version": "rag-v7",
  "source_count": 8,
  "generated_at": "2026-08-13T..."
}
```

---

# 44.45 Research Dashboard

Dashboard utama:

```text
┌────────────────────────────────────────────────────┐
│ RESEARCH WORKSPACE                                 │
├────────────────────────────────────────────────────┤
│ Studi Syarah Hadis Niat                            │
│                                                    │
│ Sources       24                                   │
│ Annotations   57                                   │
│ Claims        18                                   │
│ Citations     43                                   │
│ Notes         21                                   │
│                                                    │
│ ─────────────────────────────────────────────────  │
│                                                    │
│ Recent Evidence                                    │
│                                                    │
│ Fathul Bari 1/184                                  │
│ Fathul Bari 1/185                                  │
│ Sahih Bukhari #1                                   │
│                                                    │
│ [Open Reader] [Ask AI] [Export]                    │
└────────────────────────────────────────────────────┘
```

---

# 44.46 Research Reader

Layout yang saya rekomendasikan:

```text
┌───────────┬──────────────────────────┬──────────────┐
│ SOURCES   │ DOCUMENT                 │ INSPECTOR    │
│           │                          │              │
│ Bukhari   │ Arabic Text              │ Annotation   │
│ Fath Bari │                          │              │
│ Muslim    │ Translation              │ Citation     │
│           │                          │              │
│           │ Syarah                   │ Scholar      │
│           │                          │ Claim        │
└───────────┴──────────────────────────┴──────────────┘
```

---

# 44.47 Inspector Panel

Ketika passage dipilih:

```text
SOURCE
Fathul Bari

LOCATION
Vol. 1 / p. 184

AUTHOR
Ibn Hajar

ATTRIBUTION
Verified

CITED SCHOLARS
al-Nawawi

RELATED HADITH
Bukhari #1

CLAIMS
3

ANNOTATIONS
2
```

---

# 44.48 AI Citation Requirement

AI tidak boleh menghasilkan:

> "Menurut Ibn Hajar..."

tanpa:

```text
citation_id
```

Validator:

```text
IF attribution_claim
AND citation_id == NULL
THEN REVIEW_REQUIRED
```

---

# 44.49 Unsupported Claim Detector

```text
Claim:
"Ibn Hajar berpendapat X."

Evidence:
Tidak ditemukan.

Result:
⚠ UNSUPPORTED
```

AI harus:

> "Saya belum menemukan sumber yang cukup untuk memastikan klaim tersebut."

---

# 44.50 Research Quality Score

Buat skor internal:

```text
Research Quality
────────────────────────

Source coverage       92%
Citation coverage     97%
Attribution accuracy  99%
Evidence strength     88%
Unsupported claims     3%

Overall                94%
```

Ini **bukan penilaian kebenaran agama**, tetapi indikator kualitas evidence workflow.

---

# 44.51 Important Separation

Sistem harus memisahkan:

```text
SOURCE TRUTH
```

dari:

```text
AI CONFIDENCE
```

Contoh:

```text
AI confidence: 98%
```

tidak berarti:

```text
98% certain that the scholarly claim is true.
```

Artinya hanya model yakin terhadap proses yang dilakukan berdasarkan evidence.

---

# 44.52 API Endpoints

Tambahkan:

```http
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{id}

POST   /api/v1/projects/{id}/sources

POST   /api/v1/projects/{id}/annotations
GET    /api/v1/projects/{id}/annotations

POST   /api/v1/projects/{id}/notes
GET    /api/v1/projects/{id}/notes

POST   /api/v1/projects/{id}/claims
GET    /api/v1/projects/{id}/claims

POST   /api/v1/projects/{id}/bookmarks

POST   /api/v1/projects/{id}/ask

POST   /api/v1/projects/{id}/export

POST   /api/v1/projects/{id}/snapshot
```

---

# 44.53 Example Ask API

```http
POST /api/v1/projects/PROJECT-001/ask
```

```json
{
  "question": "Apa perbedaan pendapat Ibn Hajar dan al-Nawawi?",
  "context_mode": "CURRENT_PROJECT"
}
```

Response:

```json
{
  "answer": "...",
  "claims": [
    {
      "text": "...",
      "citation_ids": ["C001", "C002"]
    }
  ],
  "evidence": [
    "P88421",
    "P88422"
  ]
}
```

---

# 44.54 Security

Research notes bisa bersifat pribadi.

Tambahkan:

```text
PRIVATE
PROJECT_SHARED
PUBLIC
```

Default:

```text
PRIVATE
```

---

# 44.55 Backup

Project harus dapat diekspor sebagai satu bundle:

```text
research-project.zip

├── project.json
├── notes.json
├── claims.json
├── annotations.json
├── citations.json
├── sources.json
└── bibliography.json
```

Source asli tidak perlu diduplikasi jika copyright/licensing melarangnya; simpan reference dan metadata sumber.

---

# 44.56 Stage 44 Definition of Done

```text
[ ] Research Project
[ ] Project Sources
[ ] Source Reader
[ ] Highlight
[ ] Annotation
[ ] Annotation Recovery
[ ] Research Notes
[ ] Claims
[ ] Evidence Matrix
[ ] Bookmarks
[ ] Tags
[ ] Semantic Search
[ ] Cross References
[ ] Side-by-Side Reader
[ ] AI Research Mode
[ ] Citation Integration
[ ] Attribution Integration
[ ] Reviewer Workflow
[ ] Audit Trail
[ ] Research Snapshot
[ ] Versioning
[ ] AI Provenance
[ ] Export Markdown
[ ] Export PDF
[ ] Export DOCX
[ ] Export JSON
[ ] Bibliography Export
[ ] Project Backup
```

---

# 44.57 Posisi Sistem Setelah Stage 44

```text
                         ┌──────────────────┐
                         │ RESEARCH PROJECT │
                         └────────┬─────────┘
                                  │
               ┌──────────────────┼──────────────────┐
               ▼                  ▼                  ▼
          SOURCE READER       ANNOTATION          NOTES
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  ▼
                         EVIDENCE LIBRARY
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                  CLAIM        CITATION       ENTITY
                    │             │             │
                    └─────────────┼─────────────┘
                                  ▼
                         KNOWLEDGE GRAPH
                                  │
                                  ▼
                         RAG/SYARAH AI
                                  │
                                  ▼
                       VALIDATED ANSWER
                                  │
                                  ▼
                         RESEARCH REPORT
```
