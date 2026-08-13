# Stage 23 — Research Workspace & Multi-Source Comparison

Stage 23 mengubah aplikasi kita dari **Syarah AI Assistant** menjadi **workspace penelitian hadis**.

Fokusnya:

> Peneliti dapat membuka hadis, Fathul Bari, sumber lain, evidence, catatan, dan citation dalam satu ruang kerja—tanpa kehilangan provenance setiap informasi.

---

# 23.1 Tujuan Stage 23

Target UX:

```text
Hadis
  │
  ├── Teks Arab
  ├── Terjemah
  ├── Metadata
  │
  ▼
Fathul Bari
  │
  ├── Syarah
  ├── Volume
  ├── Halaman
  └── Highlight
  │
  ▼
Evidence
  │
  ├── Citation
  ├── Confidence
  └── Source
  │
  ▼
Research Notes
  │
  └── Findings
```

---

# 23.2 Arsitektur

```text
                    RESEARCH WORKSPACE
                           │
         ┌─────────────────┼──────────────────┐
         ▼                 ▼                  ▼
      HADITH            SOURCES             NOTES
         │                 │                  │
         ▼                 ▼                  ▼
   Hadith Panel       Source Viewer      Note Editor
         │                 │                  │
         └─────────────────┼──────────────────┘
                           ▼
                    Evidence Manager
                           │
                           ▼
                     Citation Engine
                           │
                           ▼
                       RAG Engine
```

---

# 23.3 Konsep Workspace

Setiap penelitian mempunyai:

```text
Workspace
   │
   ├── Documents
   ├── Hadiths
   ├── Sources
   ├── Notes
   ├── Highlights
   ├── Citations
   ├── Queries
   └── Findings
```

Contoh:

```text
Workspace:
"Hadis Niat dalam Fathul Bari"

Documents:
- Sahih al-Bukhari
- Fathul Bari

Hadiths:
- Bukhari #1
- Bukhari #54
- Muslim ...

Notes:
- Definisi niat
- Hubungan niat dan amal
- Perbedaan riwayat
```

---

# 23.4 Database `research_workspaces`

```sql
CREATE TABLE research_workspaces (
    id UUID PRIMARY KEY,

    owner_id UUID,

    name TEXT NOT NULL,

    description TEXT,

    status VARCHAR(30) DEFAULT 'ACTIVE',

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Status:

```text
ACTIVE
ARCHIVED
DELETED
```

---

# 23.5 Workspace Members

Agar nanti bisa digunakan tim:

```sql
CREATE TABLE workspace_members (
    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    user_id UUID NOT NULL,

    role VARCHAR(30) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(workspace_id, user_id)
);
```

Role:

```text
OWNER
RESEARCHER
REVIEWER
VIEWER
```

---

# 23.6 Workspace Items

Daripada membuat banyak tabel relasi sederhana, kita dapat membuat tabel:

```sql
CREATE TABLE workspace_items (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    item_type VARCHAR(40) NOT NULL,

    entity_id UUID NOT NULL,

    position INTEGER,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

`item_type`:

```text
HADITH
SHARH_CHUNK
SOURCE_PAGE
RAG_QUERY
NOTE
CITATION
```

---

# 23.7 Workspace Layout

Frontend:

```text
/research/workspaces/{workspaceId}
```

Layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ Hadith Research · Hadis Niat                               │
├───────────────┬───────────────────────────┬─────────────────┤
│ HADITH        │ SOURCE                    │ NOTES           │
│               │                           │                 │
│ Bukhari #1    │ Fathul Bari               │ Niat            │
│               │ Vol 1 · p.45              │                 │
│ Arabic text   │                           │ • Definisi      │
│               │ قوله إنما الأعمال...      │ • Amal          │
│ Translation   │                           │ • Ikhlas        │
│               │ [Highlight]               │                 │
│               │                           │                 │
├───────────────┴───────────────────────────┴─────────────────┤
│ EVIDENCE / CITATIONS                                        │
│ [FB-V1-P45-C003]                                           │
└─────────────────────────────────────────────────────────────┘
```

---

# 23.8 Resizable Panels

User dapat:

```text
Hadith 30%
Source 45%
Notes 25%
```

atau:

```text
Hadith 20%
Source 60%
Notes 20%
```

State layout disimpan:

```json
{
  "panels": {
    "hadith": 30,
    "source": 45,
    "notes": 25
  }
}
```

---

# 23.9 Persistent Workspace State

Jika browser ditutup:

```text
Open workspace
       ↓
restore layout
       ↓
restore pages
       ↓
restore selected evidence
       ↓
continue research
```

Simpan:

```sql
CREATE TABLE workspace_sessions (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    user_id UUID,

    layout JSONB,

    active_items JSONB,

    scroll_positions JSONB,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 23.10 Hadith Panel

Panel hadis menampilkan:

```text
Sahih al-Bukhari
Hadith #1

Arabic:
إنما الأعمال بالنيات...

Narrator:
عمر بن الخطاب

Chapter:
بدء الوحي

Source:
Ahmad Sanusi Hadits API
```

Tombol:

```text
[Open Full Hadith]
[Copy Arabic]
[Copy Translation]
[Find Sharh]
[Add to Workspace]
```

---

# 23.11 Source Panel

Source panel terintegrasi dengan Stage 21:

```text
Fathul Bari
Vol. 1
Page 45

[PDF] [TEXT]

قوله إنما الأعمال بالنيات...
```

Kontrol:

```text
◀ Previous
Page 45 / 800
Next ▶
```

---

# 23.12 Highlight Engine

User dapat memilih teks:

```text
قوله إنما الأعمال بالنيات
```

kemudian:

```text
[Highlight]
[Add Note]
[Copy Citation]
[Ask AI]
```

---

# 23.13 Highlight Database

```sql
CREATE TABLE source_highlights (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    page_id UUID NOT NULL
        REFERENCES source_pages(id),

    chunk_id UUID
        REFERENCES sharh_chunks(id),

    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,

    selected_text TEXT NOT NULL,

    color VARCHAR(30),

    note_id UUID,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 23.14 Jangan Menyimpan Highlight Berdasarkan Pixel

Jangan:

```text
x=100
y=200
width=300
```

sebagai identifier utama.

Karena tampilan PDF bisa berubah.

Gunakan:

```text
page_id
+
text offset
+
selected text
+
content hash
```

Dengan begitu highlight dapat direkonstruksi.

---

# 23.15 Highlight Anchor

Simpan:

```json
{
  "page_id": "...",
  "start_offset": 1450,
  "end_offset": 1490,
  "selected_text": "قوله إنما الأعمال بالنيات",
  "content_hash": "..."
}
```

Jika teks berubah:

```text
hash berbeda
```

sistem memberi:

```text
⚠ Highlight anchor may be outdated
```

---

# 23.16 Research Notes

Notes harus mendukung Markdown.

Contoh:

```markdown
## Niat

Ibnu Hajar membahas hubungan antara niat
dan amal pada bagian awal syarah hadis.

### Evidence

- [FB-V1-P45-C003]

### Pertanyaan

Apakah pembahasan ini juga muncul pada
riwayat lain?
```

---

# 23.17 Notes Database

```sql
CREATE TABLE research_notes (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    parent_id UUID
        REFERENCES research_notes(id),

    title TEXT,

    content TEXT NOT NULL,

    content_format VARCHAR(20) DEFAULT 'markdown',

    position INTEGER,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 23.18 Note Types

Tambahkan:

```text
OBSERVATION
QUESTION
HYPOTHESIS
FINDING
QUOTE
TODO
SUMMARY
```

Contoh:

```text
[OBSERVATION]
Ibnu Hajar menggunakan istilah...

[QUESTION]
Apakah istilah ini digunakan oleh ulama lain?

[FINDING]
...
```

---

# 23.19 Citation di Notes

User dapat mengetik:

```text
Menurut Ibnu Hajar [FB-V1-P45-C003], ...
```

Citation menjadi clickable.

Flow:

```text
Note
 ↓
Citation ID
 ↓
Source Page
 ↓
Highlight
```

---

# 23.20 Citation Picker

Ketika user mengetik:

```text
[
```

muncul:

```text
Search evidence...

FB-V1-P45-C003
قوله إنما الأعمال بالنيات...

Bukhari #1
إنما الأعمال بالنيات...
```

Pilih:

```text
[Insert Citation]
```

hasil:

```markdown
Menurut Ibnu Hajar [FB-V1-P45-C003], ...
```

---

# 23.21 Citation Storage

```sql
CREATE TABLE research_citations (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    citation_type VARCHAR(40) NOT NULL,

    source_id UUID,

    source_reference JSONB NOT NULL,

    label TEXT,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 23.22 Multi-Source Comparison

Sekarang kita tambahkan:

```text
Compare Mode
```

Contoh:

```text
Hadis Bukhari #1

        │
        ├── Fathul Bari
        ├── Syarah lain
        ├── Riwayat Muslim
        └── Riwayat lain
```

UI:

```text
┌──────────────────┬──────────────────┬──────────────────┐
│ HADIS             │ FATHUL BARI      │ SOURCE B         │
├──────────────────┼──────────────────┼──────────────────┤
│ إنما الأعمال...  │ قوله إنما...     │ إنما الأعمال... │
│                  │                  │                  │
│                  │                  │                  │
└──────────────────┴──────────────────┴──────────────────┘
```

---

# 23.23 Source Comparison Entity

```sql
CREATE TABLE research_comparisons (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    title TEXT,

    comparison_type VARCHAR(40),

    configuration JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 23.24 Comparison Types

```text
HADITH_VARIANTS
SHARH_COMPARISON
SOURCE_COMPARISON
NARRATOR_COMPARISON
WORDING_COMPARISON
```

---

# 23.25 Hadith Variant Comparison

Contoh:

```text
Bukhari
إنما الأعمال بالنيات...

Muslim
إنما الأعمال بالنية...

Other narration
...
```

Sistem menampilkan perbedaan:

```text
+ بالنيات
- بالنية
```

Tetapi perubahan teks harus berasal dari data sumber, bukan hasil AI.

---

# 23.26 Text Diff

Gunakan:

```text
original Arabic
      ↓
tokenization
      ↓
sequence comparison
      ↓
diff
```

Output:

```text
إنما الأعمال [بالنيات]
إنما الأعمال [بالنية]
```

UI:

```text
ADDED
REMOVED
UNCHANGED
```

---

# 23.27 Word-Level Analysis

User dapat klik kata:

```text
الأعمال
```

dan melihat:

```text
Occurrences
├── Bukhari #1
├── Fathul Bari
├── Related hadiths
└── Notes
```

Ini membuka jalan ke **linguistic research tools**.

---

# 23.28 Ask AI From Selection

User memilih:

```text
قوله إنما الأعمال بالنيات
```

klik:

```text
Ask AI
```

prompt otomatis:

```text
Jelaskan bagian Fathul Bari berikut
berdasarkan corpus yang tersedia:

"قوله إنما الأعمال بالنيات"

Sertakan sumber halaman.
```

AI kemudian menggunakan Stage 22.

---

# 23.29 Context-Aware AI

Jika user berada di:

```text
Fathul Bari
Vol. 1
p.45
```

dan bertanya:

> "Apa maksud bagian ini?"

sistem otomatis memasukkan context:

```json
{
  "active_source": "FB-V1-P45",
  "selected_text": "...",
  "workspace_id": "..."
}
```

Jadi user tidak perlu menjelaskan ulang.

---

# 23.30 Research Chat

Panel kanan dapat berubah menjadi:

```text
┌───────────────────────────┐
│ RESEARCH AI               │
├───────────────────────────┤
│ User:                     │
│ Apa maksud bagian ini?    │
│                           │
│ AI:                       │
│ ...                       │
│                           │
│ [FB-V1-P45-C003]          │
├───────────────────────────┤
│ Ask about this source...  │
└───────────────────────────┘
```

---

# 23.31 Workspace Context

RAG query mendapatkan:

```text
workspace documents
+
active hadith
+
active source page
+
selected text
+
workspace notes
```

Tetapi ada aturan:

> **Notes pengguna bukan otomatis dianggap sebagai sumber primer.**

Notes diberi:

```text
source_type = USER_NOTE
```

dan bobot retrieval berbeda.

---

# 23.32 Source Trust Levels

```text
PRIMARY
SECONDARY
DERIVED
USER_NOTE
AI_GENERATED
```

Untuk jawaban syarah:

```text
PRIMARY > SECONDARY > DERIVED > USER_NOTE > AI_GENERATED
```

---

# 23.33 Research Finding

Finding berbeda dari note biasa.

Contoh:

```text
Finding:
Ibnu Hajar menghubungkan hadis niat
dengan prinsip pembeda antara amal
dan tujuan amal.
```

Finding harus mempunyai evidence:

```text
Finding
   │
   ├── Evidence 1
   ├── Evidence 2
   └── Evidence 3
```

---

# 23.34 Findings Table

```sql
CREATE TABLE research_findings (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    title TEXT NOT NULL,

    statement TEXT NOT NULL,

    status VARCHAR(30) DEFAULT 'DRAFT',

    confidence NUMERIC(6,5),

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Status:

```text
DRAFT
SUPPORTED
REVIEW_REQUIRED
REJECTED
FINAL
```

---

# 23.35 Finding Evidence

```sql
CREATE TABLE finding_evidence (
    finding_id UUID NOT NULL
        REFERENCES research_findings(id),

    evidence_id UUID NOT NULL
        REFERENCES rag_evidence(id),

    support_type VARCHAR(30),

    PRIMARY KEY(finding_id, evidence_id)
);
```

Sehingga:

```text
Finding
   ↓
Evidence
   ↓
Source
   ↓
Page
```

---

# 23.36 Research Workflow

```text
Explore
   ↓
Collect
   ↓
Highlight
   ↓
Annotate
   ↓
Ask AI
   ↓
Compare
   ↓
Create Finding
   ↓
Verify
   ↓
Finalize
```

---

# 23.37 Finding Verification

Reviewer melihat:

```text
FINDING

"Menurut Ibnu Hajar, ..."

Evidence:
✓ FB-V1-P45-C003
✓ FB-V1-P46-C001

Status:
REVIEW_REQUIRED

[ VERIFY ]
[ RETURN TO DRAFT ]
```

Jika verified:

```text
SUPPORTED
```

---

# 23.38 Research Timeline

Tambahkan activity stream:

```text
13 Aug 09:12
Opened Bukhari #1

13 Aug 09:15
Highlighted FB-V1-P45-C003

13 Aug 09:18
Created note "Makna Niat"

13 Aug 09:22
Asked AI

13 Aug 09:25
Created finding

13 Aug 09:30
Verified finding
```

Database:

```sql
CREATE TABLE workspace_activity (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    user_id UUID,

    action VARCHAR(60) NOT NULL,

    entity_type VARCHAR(50),
    entity_id UUID,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 23.39 Undo / Versioning

Research note:

```text
Version 1
    ↓
Version 2
    ↓
Version 3
```

Jangan hanya menyimpan versi terakhir.

```sql
CREATE TABLE research_note_versions (
    id UUID PRIMARY KEY,

    note_id UUID NOT NULL
        REFERENCES research_notes(id),

    version INTEGER NOT NULL,

    content TEXT NOT NULL,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(note_id, version)
);
```

---

# 23.40 Export Research

Workspace nantinya bisa diekspor:

```text
Markdown
PDF
DOCX
JSON
```

Contoh Markdown:

```markdown
# Hadis Niat dalam Fathul Bari

## Hadis

إنما الأعمال بالنيات...

## Syarah

...

## Findings

### 1. Makna Niat

...

## Sources

1. Sahih al-Bukhari #1
2. Fathul Bari, Vol. 1, p.45
```

Citation tetap dipertahankan.

---

# 23.41 Export Audit Metadata

Setiap export juga menyimpan:

```json
{
  "workspace_id": "...",
  "export_version": "23.1.0",
  "generated_at": "...",
  "source_snapshot": "...",
  "citation_count": 14
}
```

Dengan demikian dokumen hasil penelitian dapat ditelusuri kembali.

---

# 23.42 Workspace API

### Create

```http
POST /api/v1/workspaces
```

### List

```http
GET /api/v1/workspaces
```

### Detail

```http
GET /api/v1/workspaces/{workspace_id}
```

### Add item

```http
POST /api/v1/workspaces/{workspace_id}/items
```

### Remove item

```http
DELETE /api/v1/workspaces/{workspace_id}/items/{item_id}
```

### Notes

```http
GET /api/v1/workspaces/{workspace_id}/notes
POST /api/v1/workspaces/{workspace_id}/notes
```

### Highlights

```http
POST /api/v1/workspaces/{workspace_id}/highlights
```

### Findings

```http
GET /api/v1/workspaces/{workspace_id}/findings
POST /api/v1/workspaces/{workspace_id}/findings
```

---

# 23.43 Ask AI Endpoint

Context-aware:

```http
POST /api/v1/workspaces/{workspace_id}/ask
```

Request:

```json
{
  "question": "Apa maksud bagian ini?",
  "active_item_id": "...",
  "selected_text": "قوله إنما الأعمال بالنيات"
}
```

Server otomatis mengambil:

```text
active source
+
selected text
+
workspace context
+
RAG
```

---

# 23.44 Comparison API

```http
POST /api/v1/comparisons
```

Request:

```json
{
  "workspace_id": "...",
  "type": "HADITH_VARIANTS",
  "sources": [
    "hadith:bukhari:1",
    "hadith:muslim:1907"
  ]
}
```

---

# 23.45 Research Workspace Security

Workspace harus menerapkan:

```text
OWNER
   ↓
RESEARCHER
   ↓
REVIEWER
   ↓
VIEWER
```

Contoh:

| Action           | Owner | Researcher | Reviewer | Viewer |
| ---------------- | ----: | ---------: | -------: | -----: |
| Read             |     ✓ |          ✓ |        ✓ |      ✓ |
| Add note         |     ✓ |          ✓ |        ✓ |      - |
| Edit note        |     ✓ |          ✓ |        ✓ |      - |
| Verify finding   |     ✓ |          - |        ✓ |      - |
| Delete workspace |     ✓ |          - |        - |      - |
| Export           |     ✓ |          ✓ |        ✓ |      ✓ |

---

# 23.46 Audit

Setiap perubahan:

```text
CREATE_NOTE
EDIT_NOTE
DELETE_NOTE
CREATE_HIGHLIGHT
VERIFY_FINDING
REJECT_FINDING
ADD_SOURCE
REMOVE_SOURCE
EXPORT_WORKSPACE
```

masuk audit trail.

---

# 23.47 Definition of Done

Stage 23 selesai apabila:

```text
[ ] Research workspace
[ ] Workspace members
[ ] Workspace items
[ ] Persistent layout
[ ] Hadith panel
[ ] Source panel
[ ] Notes panel
[ ] Text highlighting
[ ] Highlight anchors
[ ] Citation picker
[ ] Multi-source comparison
[ ] Hadith variant comparison
[ ] Text diff
[ ] Context-aware AI
[ ] Research chat
[ ] Findings
[ ] Finding evidence
[ ] Finding verification
[ ] Activity timeline
[ ] Note versioning
[ ] Workspace export
[ ] Workspace audit
```

---

# 23.48 Milestone Setelah Stage 23

Sekarang platform kita memiliki empat lapisan besar:

```text
┌─────────────────────────────────────────────┐
│              RESEARCH WORKSPACE             │
├─────────────────────────────────────────────┤
│ Notes · Highlights · Findings · Comparison  │
├─────────────────────────────────────────────┤
│                 RAG ENGINE                  │
├─────────────────────────────────────────────┤
│ Retrieval · Reranking · Evidence · Citation│
├─────────────────────────────────────────────┤
│               KNOWLEDGE LAYER               │
├─────────────────────────────────────────────┤
│ Hadith · Fathul Bari · Graph · References   │
├─────────────────────────────────────────────┤
│                 SOURCE LAYER                │
├─────────────────────────────────────────────┤
│ PDF · Pages · OCR · Hash · Provenance       │
└─────────────────────────────────────────────┘
```

Dengan fondasi ini, aplikasi sudah mulai menyerupai **platform penelitian hadis**, bukan sekadar aplikasi pencarian hadis.

---
