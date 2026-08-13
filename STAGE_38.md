# Stage 38 — Scholarly Research Workspace & Comparative Syarah

Karena **Stage 37 Claim-Level Citation Engine tidak digunakan**, kita lanjutkan ke **Stage 38** dengan fokus pada fitur yang lebih bernilai untuk aplikasi *Fathul Bari*: **workspace penelitian ulama**, perbandingan syarah, pencatatan temuan, dan navigasi lintas hadis–syarah–sumber.

Tujuan Stage 38:

> Mengubah aplikasi dari sekadar **Hadith + AI Assistant** menjadi **Islamic Hadith Research Platform** yang memungkinkan peneliti menelusuri, membandingkan, mencatat, dan memverifikasi pembahasan hadis secara sistematis.

---

# 38.1 Posisi Stage 38

```text
Ahmad Sanusi Hadits API
          │
          ▼
       Hadith
          │
          ▼
 Alignment Engine
          │
          ▼
 Scholarly Reranker
          │
          ▼
 Evidence Scoring
          │
          ├───────────────┐
          ▼               ▼
   Fathul Bari       Knowledge Graph
          │               │
          └───────┬───────┘
                  ▼
       Research Workspace
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
    Compare    Notes      Collections
        │         │         │
        └─────────┼─────────┘
                  ▼
            AI Assistant
```

---

# 38.2 Masalah yang Diselesaikan

Peneliti sering membutuhkan alur seperti:

```text
Hadis
 ↓
Buka syarah
 ↓
Buka halaman scan
 ↓
Catat poin penting
 ↓
Cari hadis terkait
 ↓
Bandingkan penjelasan
 ↓
Simpan hasil penelitian
```

Jika semuanya dilakukan secara manual, pengguna harus berpindah-pindah aplikasi.

Stage 38 menyatukannya:

```text
SEARCH
→ READ
→ COMPARE
→ ANNOTATE
→ CONNECT
→ SAVE
→ EXPORT
```

---

# 38.3 Research Workspace

Buat konsep:

```text
Workspace
```

Contoh:

```text
Workspace:
"Bab Niat dalam Fathul Bari"
```

berisi:

```text
Hadis
Syarah
Catatan
Highlight
Referensi
Knowledge Graph
AI queries
```

---

# 38.4 Database Workspace

```sql
CREATE TABLE research_workspaces (
    id UUID PRIMARY KEY,

    user_id UUID NOT NULL,

    name TEXT NOT NULL,

    description TEXT,

    is_archived BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 38.5 Workspace Items

```sql
CREATE TABLE workspace_items (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL,

    item_type VARCHAR(40) NOT NULL,

    entity_id UUID,

    title TEXT,

    position INTEGER,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Jenis:

```text
HADITH
PASSAGE
PAGE
BOOK
NOTE
GRAPH_NODE
SEARCH
AI_SESSION
```

---

# 38.6 Research Workspace UI

```text
┌──────────────────────────────────────────────────┐
│ 📚 Bab Niat dalam Fathul Bari                    │
├──────────────┬───────────────────────────────────┤
│ COLLECTION   │ MAIN RESEARCH AREA                │
│              │                                   │
│ Hadith       │ Hadith #1                         │
│ ├─ H1571     │ ───────────────────────────────   │
│ ├─ H1572     │ Matn                              │
│ └─ H1573     │                                   │
│              │ Fathul Bari                       │
│ Passages     │ Vol. 1 • p. 48                    │
│ ├─ P881      │                                   │
│ └─ P882      │ [Source Viewer]                   │
│              │                                   │
│ Notes        │ 📝 Notes                           │
│ ├─ Note 1    │                                   │
│ └─ Note 2    │                                   │
└──────────────┴───────────────────────────────────┘
```

---

# 38.7 Research Tabs

Workspace memiliki:

```text
OVERVIEW
HADITH
SHARH
SOURCES
NOTES
GRAPH
AI
HISTORY
```

---

# 38.8 Persistent Research Context

Ketika pengguna membuka:

```text
Hadis #1571
```

kemudian pindah ke:

```text
Fathul Bari p. 218
```

workspace tetap mengetahui konteks:

```text
Current Research Context:
Hadith H1571
Passage P88421
Book Fathul Bari
Kitab al-Iman
Bab ...
```

Ini penting untuk AI Assistant.

---

# 38.9 Research Context → AI

User:

> Jelaskan perbedaan dua pendapat Ibn Hajar di halaman ini.

AI otomatis menerima:

```json
{
  "workspace": "W123",
  "current_passage": "P88421",
  "selected_passage": "P88422",
  "hadith": "H1571"
}
```

Tidak perlu user menjelaskan ulang.

---

# 38.10 Notes System

Buat note yang bisa ditempel pada:

```text
Hadith
Passage
Sentence
Page
Book
Graph node
```

---

# 38.11 Notes Database

```sql
CREATE TABLE research_notes (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL,

    user_id UUID NOT NULL,

    title TEXT,

    content TEXT NOT NULL,

    note_type VARCHAR(40),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 38.12 Note Types

```text
OBSERVATION
QUESTION
REFERENCE
INTERPRETATION
TODO
WARNING
COMPARISON
CONCLUSION
```

---

# 38.13 Anchored Notes

Note dapat memiliki anchor:

```sql
CREATE TABLE note_anchors (
    id UUID PRIMARY KEY,

    note_id UUID NOT NULL,

    entity_type VARCHAR(40),

    entity_id UUID,

    start_offset INTEGER,

    end_offset INTEGER,

    selected_text TEXT
);
```

Contoh:

```text
Note:
"Ibn Hajar membedakan makna X dan Y."

Anchor:
Fathul Bari P88421
Text:
"..."
```

---

# 38.14 Highlight System

Pengguna dapat memilih teks:

```text
"الأعمال بالنيات"
```

lalu:

```text
Highlight
```

Pilihan warna/label:

```text
IMPORTANT
DEFINITION
EVIDENCE
QUESTION
KEY_ARGUMENT
```

---

# 38.15 Highlight Database

```sql
CREATE TABLE text_highlights (
    id UUID PRIMARY KEY,

    user_id UUID NOT NULL,

    entity_type VARCHAR(40),

    entity_id UUID,

    start_offset INTEGER,

    end_offset INTEGER,

    selected_text TEXT,

    label VARCHAR(40),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 38.16 Comparative Syarah

Ini fitur utama Stage 38.

Misalnya:

```text
Fathul Bari
vs
Syarh Muslim
vs
Umdatul Qari
```

Pengguna dapat melihat pembahasan secara paralel.

---

# 38.17 Comparison Workspace

```text
┌───────────────────┬───────────────────┬───────────────────┐
│ FATHUL BARI       │ SHARH MUSLIM      │ UMDATUL QARI      │
├───────────────────┼───────────────────┼───────────────────┤
│ Passage           │ Passage           │ Passage           │
│                   │                   │                   │
│ ...               │ ...               │ ...               │
│                   │                   │                   │
│ Ibn Hajar         │ al-Nawawi         │ al-'Ayni          │
└───────────────────┴───────────────────┴───────────────────┘
```

---

# 38.18 Comparative Entity Model

```text
Hadith
   │
   ├── Fathul Bari
   │
   ├── Sharh Muslim
   │
   ├── Umdatul Qari
   │
   └── Other Sharh
```

Dengan demikian aplikasi mulai menjadi **comparative hadith research system**.

---

# 38.19 Sharh Provider Abstraction

Buat:

```text
SharhProvider
```

Implementasi:

```text
FathulBariProvider
SharhMuslimProvider
UmdatulQariProvider
OtherSharhProvider
```

Walaupun Stage 38 fokus Fathul Bari, arsitektur tidak dikunci pada satu kitab.

---

# 38.20 Comparative Passage

```sql
CREATE TABLE comparative_links (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL,

    source_a_id UUID NOT NULL,

    source_b_id UUID NOT NULL,

    relationship VARCHAR(50),

    score NUMERIC(6,5),

    verification_status VARCHAR(30),

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 38.21 Relationship Types

```text
AGREE
DISAGREE
COMPLEMENT
ELABORATE
SUMMARIZE
DIFFERENT_INTERPRETATION
DIFFERENT_WORDING
SAME_ARGUMENT
RELATED
```

---

# 38.22 Jangan Otomatis Menentukan "Disagreement"

AI boleh mendeteksi:

```text
potential disagreement
```

tetapi jangan langsung menyatakan:

```text
DISAGREE
```

tanpa verifikasi.

Lebih aman:

```text
POTENTIAL_DIFFERENCE
```

---

# 38.23 Comparative AI

User:

> Bandingkan penjelasan Ibn Hajar dan al-Nawawi mengenai hadis ini.

Pipeline:

```text
Hadith
 ↓
Alignment
 ↓
Fathul Bari passages
 ↓
Other Sharh passages
 ↓
Comparison retrieval
 ↓
AI synthesis
```

---

# 38.24 AI Comparison Output

Struktur:

```text
### Ibn Hajar

...

### Al-Nawawi

...

### Persamaan

...

### Perbedaan

...

### Catatan

...
```

Setiap bagian harus terhubung dengan source passage.

---

# 38.25 Research Collections

Workspace dapat memiliki collection:

```text
"Hadis tentang Niat"
"Hadis tentang Shalat"
"Hadis tentang Akhlak"
"Bab Wudhu"
```

Collection bukan sekadar folder.

Ia dapat memiliki:

```text
description
tags
research question
status
```

---

# 38.26 Research Question

Tambahkan:

```sql
ALTER TABLE research_workspaces
ADD COLUMN research_question TEXT;
```

Contoh:

> Bagaimana Ibn Hajar menjelaskan hubungan antara niat dan amal dalam hadis pertama Shahih Bukhari?

AI dapat menggunakan pertanyaan ini sebagai context.

---

# 38.27 Research Status

```text
DRAFT
IN_RESEARCH
REVIEW
COMPLETED
ARCHIVED
```

---

# 38.28 Research Tags

```text
#niat
#iman
#fiqh
#akhlak
#hadis
#fathulbari
```

---

# 38.29 Saved Search

User menjalankan:

```text
"النية"
```

dan ingin menyimpannya.

```sql
CREATE TABLE saved_searches (
    id UUID PRIMARY KEY,

    workspace_id UUID,

    query TEXT NOT NULL,

    filters JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 38.30 Research Timeline

Setiap workspace memiliki timeline:

```text
Aug 13
│
├── Added Hadith H1571
├── Verified Passage P88421
├── Created note "Makna niat"
├── Compared with al-Nawawi
└── AI summary generated
```

---

# 38.31 Research Audit

Gunakan event:

```text
WORKSPACE_CREATED
HADITH_ADDED
PASSAGE_ADDED
NOTE_CREATED
HIGHLIGHT_CREATED
COMPARISON_CREATED
AI_QUERY
SOURCE_VERIFIED
```

---

# 38.32 Research Event Table

```sql
CREATE TABLE research_events (
    id UUID PRIMARY KEY,

    workspace_id UUID,

    user_id UUID,

    event_type VARCHAR(50),

    entity_type VARCHAR(50),

    entity_id UUID,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 38.33 Research Graph

Workspace dapat divisualisasikan:

```text
                 H1571
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
       P88421    P88422    H1572
          │        │
          ▼        ▼
       Note A    Note B
          │
          ▼
      Research Question
```

---

# 38.34 Graph Filtering

User dapat memilih:

```text
☑ Hadith
☑ Fathul Bari
☑ Notes
☑ References
☐ Related topics
☐ Other scholars
```

Graph kemudian menyederhana sesuai kebutuhan.

---

# 38.35 Research Snapshot

User dapat menyimpan keadaan workspace:

```text
Snapshot:
"Final review – Bab Niat"
```

Berisi:

```text
selected hadiths
selected passages
notes
graph state
filters
AI context
```

---

# 38.36 Export Research

Sediakan:

```text
Markdown
PDF
DOCX
JSON
BibTeX
```

Contoh:

```text
Research
 ├── Introduction
 ├── Hadith
 ├── Fathul Bari
 ├── Comparative Sources
 ├── Notes
 └── References
```

---

# 38.37 Markdown Export

Contoh:

```markdown
# Bab Niat

## Hadis

Bukhari #1571

## Fathul Bari

### Vol. 1, p. 48

...

## Catatan Peneliti

...

## Referensi

1. Sahih al-Bukhari
2. Fathul Bari
```

---

# 38.38 Citation Metadata

Setiap source menyimpan:

```json
{
  "author": "Ibn Hajar al-Asqalani",
  "title": "Fath al-Bari",
  "volume": 1,
  "page": 48,
  "edition": "...",
  "publisher": "...",
  "year": "..."
}
```

Jika metadata edition tersedia.

---

# 38.39 Edition Awareness

Ini sangat penting.

Jangan hanya:

```text
Fathul Bari p. 48
```

Simpan:

```text
Fathul Bari
Edition X
Volume 1
Page 48
```

Karena halaman antar-edisi dapat berbeda.

---

# 38.40 Canonical Citation

Buat format internal:

```text
FATHUL_BARI:
edition_id
volume
page
passage_id
```

Contoh:

```json
{
  "source": "FATHUL_BARI",
  "edition": "EDITION_01",
  "volume": 1,
  "page": 48,
  "passage_id": "P88421"
}
```

---

# 38.41 Research API

Tambahkan:

```http
POST   /api/v1/workspaces
GET    /api/v1/workspaces
GET    /api/v1/workspaces/{id}

POST   /api/v1/workspaces/{id}/items
DELETE /api/v1/workspaces/{id}/items/{itemId}

POST   /api/v1/workspaces/{id}/notes
GET    /api/v1/workspaces/{id}/notes

POST   /api/v1/workspaces/{id}/highlights

POST   /api/v1/workspaces/{id}/comparisons

GET    /api/v1/workspaces/{id}/graph

POST   /api/v1/workspaces/{id}/snapshots

POST   /api/v1/workspaces/{id}/export
```

---

# 38.42 Comparison API

```http
POST /api/v1/comparison
```

Request:

```json
{
  "hadith_id": "H1571",
  "sources": [
    "FATHUL_BARI",
    "SHARH_MUSLIM"
  ]
}
```

Response:

```json
{
  "comparison_id": "C123",
  "status": "READY"
}
```

---

# 38.43 AI Research API

```http
POST /api/v1/research/{workspaceId}/ask
```

Request:

```json
{
  "question": "Apa perbedaan penjelasan kedua ulama?"
}
```

Context otomatis:

```text
Workspace
+
Hadith
+
Passages
+
Notes
+
Comparisons
```

---

# 38.44 AI Context Hierarchy

Prioritas:

```text
1. Explicit user selection
2. Verified passages
3. Workspace items
4. Research question
5. Related graph nodes
6. General corpus search
```

Ini mencegah AI keluar terlalu jauh dari konteks penelitian.

---

# 38.45 Research Mode vs General Mode

Aplikasi memiliki dua mode:

```text
GENERAL MODE
```

dan:

```text
RESEARCH MODE
```

Research Mode:

```text
strict citations
strict source scope
visible evidence
audit trail
```

---

# 38.46 Research Mode UI

```text
┌─────────────────────────────────────────┐
│ 🔬 RESEARCH MODE                        │
│                                         │
│ Sources: 3                              │
│ Verified: 2                             │
│ Candidates: 1                           │
│                                         │
│ AI answers restricted to workspace     │
└─────────────────────────────────────────┘
```

---

# 38.47 Source Lock

User dapat mengunci:

```text
☑ Fathul Bari
☑ Sahih Bukhari
☐ Other books
☐ Web
```

AI hanya mengambil sumber yang dipilih.

---

# 38.48 Source Scope

```json
{
  "allowed_sources": [
    "FATHUL_BARI",
    "BUKHARI"
  ],
  "allow_external_search": false
}
```

---

# 38.49 AI Research Guard

Jika sumber tidak tersedia:

```text
"Saya tidak menemukan bukti yang cukup dalam sumber yang dipilih."
```

bukan:

```text
"Menurut Ibn Hajar..."
```

---

# 38.50 Research Collaboration

Tahap awal dapat mendukung:

```text
Owner
Editor
Reviewer
Viewer
```

---

# 38.51 Workspace Permissions

```text
OWNER
  ├── full access

EDITOR
  ├── notes
  ├── highlights
  └── research items

REVIEWER
  ├── verify
  └── comment

VIEWER
  └── read
```

---

# 38.52 Shared Workspace

URL internal:

```text
/workspaces/W123
```

Pengguna yang memiliki akses dapat membuka penelitian yang sama.

---

# 38.53 Research Comments

Tambahkan:

```sql
CREATE TABLE research_comments (
    id UUID PRIMARY KEY,

    workspace_id UUID,

    entity_type VARCHAR(40),

    entity_id UUID,

    user_id UUID,

    content TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Contoh:

> Apakah passage ini benar-benar merujuk hadis #1571 atau hadis sebelumnya?

---

# 38.54 Scholarly Discussion

Comment dapat diberi status:

```text
OPEN
RESOLVED
REOPENED
```

Ini berguna untuk collaborative review.

---

# 38.55 Research Quality Indicator

Workspace dapat menampilkan:

```text
Research Quality

Hadith verified:      92%
Sharh verified:       87%
Sources verified:     100%
Open questions:       4
Disputed alignments:  2
```

Ini bukan "nilai keilmuan", melainkan **status kelengkapan penelitian**.

---

# 38.56 Research Completeness

Formula sederhana:

```text
completeness =
verified_items
/
required_items
```

Misalnya:

```text
12 / 15 = 80%
```

---

# 38.57 Important Distinction

Jangan menampilkan:

```text
"Research is 90% correct"
```

Lebih tepat:

```text
"Research coverage: 90%"
```

Karena coverage ≠ correctness.

---

# 38.58 Research Recommendation Engine

AI dapat membantu:

> "Apa yang masih perlu saya periksa?"

Engine menganalisis:

```text
unverified alignment
missing source
contradictory notes
unresolved questions
missing comparative source
```

kemudian:

```text
Research Tasks

[ ] Verify P88421
[ ] Check narration variant
[ ] Compare al-Nawawi
[ ] Resolve note #12
```

---

# 38.59 Research Task Database

```sql
CREATE TABLE research_tasks (
    id UUID PRIMARY KEY,

    workspace_id UUID,

    title TEXT NOT NULL,

    description TEXT,

    priority VARCHAR(20),

    status VARCHAR(20),

    linked_entity_type VARCHAR(40),

    linked_entity_id UUID,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    completed_at TIMESTAMPTZ
);
```

---

# 38.60 Research Workflow

```text
Question
   ↓
Collect Hadith
   ↓
Find Fathul Bari
   ↓
Verify Evidence
   ↓
Compare Sources
   ↓
Annotate
   ↓
Ask AI
   ↓
Review
   ↓
Conclusion
   ↓
Export
```

---

# 38.61 Stage 38 Architecture

```text
                       ┌───────────────┐
                       │ Ahmad Sanusi  │
                       │ Hadith API    │
                       └───────┬───────┘
                               ▼
                          Hadith Layer
                               │
                               ▼
                     Alignment + Evidence
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
             Fathul Bari    Other Sharh   Sources
                 │             │             │
                 └─────────────┼─────────────┘
                               ▼
                    Research Workspace
                               │
          ┌────────────────────┼───────────────────┐
          ▼                    ▼                   ▼
        Notes              Comparison           Graph
          │                    │                   │
          └────────────────────┼───────────────────┘
                               ▼
                        Research AI
                               │
                               ▼
                         Export / Share
```

---

# 38.62 Folder Structure

```text
src/
├── research/
│   ├── workspace/
│   ├── notes/
│   ├── highlights/
│   ├── comparison/
│   ├── comments/
│   ├── tasks/
│   ├── snapshots/
│   ├── collaboration/
│   └── export/
│
├── alignment/
├── evidence/
├── hadith/
├── sharh/
├── source/
├── rag/
└── knowledge-graph/
```

---

# 38.63 Definition of Done

Stage 38 selesai apabila:

```text
[ ] Research Workspace
[ ] Workspace Items
[ ] Research Questions
[ ] Hadith Collections
[ ] Notes
[ ] Anchored Notes
[ ] Text Highlights
[ ] Comparative Syarah
[ ] Comparative Links
[ ] Source Scope
[ ] Research Mode
[ ] Research AI Context
[ ] Saved Searches
[ ] Research Timeline
[ ] Research Audit
[ ] Research Graph
[ ] Snapshots
[ ] Markdown Export
[ ] PDF Export
[ ] DOCX Export
[ ] Citation Metadata
[ ] Edition Awareness
[ ] Research Comments
[ ] Collaborative Roles
[ ] Research Tasks
[ ] Research Completeness
[ ] AI Research Recommendations
```

---

# 38.64 Hasil Akhir Stage 38

Setelah tahap ini, pengalaman pengguna berubah menjadi:

```text
                HADIS
                  │
                  ▼
          ┌───────────────┐
          │ FATHUL BARI   │
          └───────┬───────┘
                  │
          ┌───────┴────────┐
          ▼                ▼
       Evidence        Comparison
          │                │
          └───────┬────────┘
                  ▼
        RESEARCH WORKSPACE
                  │
       ┌──────────┼───────────┐
       ▼          ▼           ▼
     Notes      Graph        Tasks
       │          │           │
       └──────────┼───────────┘
                  ▼
             RESEARCH AI
                  │
                  ▼
             Final Output
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      PDF       DOCX      Markdown
```

Dengan demikian aplikasi Anda tidak lagi sekadar **"AI yang menjelaskan Fathul Bari"**, tetapi menjadi **workspace penelitian hadis berbasis sumber**, dengan hubungan terstruktur antara **hadis, syarah, evidence, halaman sumber, catatan peneliti, perbandingan ulama, dan Knowledge Graph**.
