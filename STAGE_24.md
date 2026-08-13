# Stage 24 — Scholarly Citation & Bibliography Engine

Stage 24 membangun **mesin sitasi ilmiah** di atas Research Workspace dan Evidence Engine.

Target akhirnya:

```text
Evidence
   ↓
Citation Record
   ↓
Footnote / In-text Citation
   ↓
Bibliography
   ↓
Export PDF / DOCX / Markdown / BibTeX / RIS
```

Prinsip utama:

> **Setiap citation harus dapat ditelusuri kembali sampai ke teks sumber, halaman, chunk, dan provenance-nya.**

---

# 24.1 Posisi Stage 24 dalam Arsitektur

```text
┌─────────────────────────────────────────────┐
│           RESEARCH WORKSPACE                │
├─────────────────────────────────────────────┤
│ Notes · Findings · Highlights · Comparison │
├─────────────────────────────────────────────┤
│       SCHOLARLY CITATION ENGINE             │
│                                             │
│ Citation · Footnote · Bibliography          │
│ Style · DOI/ISBN · Export                   │
├─────────────────────────────────────────────┤
│              RAG ENGINE                     │
├─────────────────────────────────────────────┤
│ Evidence · Retrieval · Reranking            │
├─────────────────────────────────────────────┤
│             KNOWLEDGE GRAPH                 │
├─────────────────────────────────────────────┤
│ Hadith · Fathul Bari · Sources              │
└─────────────────────────────────────────────┘
```

---

# 24.2 Masalah yang Diselesaikan

Saat ini sistem kita mempunyai:

```text
FB-V1-P45-C003
```

Ini bagus untuk mesin, tetapi kurang ideal untuk tulisan ilmiah.

Kita ingin:

```text
Ibn Ḥajar al-ʿAsqalānī,
Fatḥ al-Bārī bi-Sharḥ Ṣaḥīḥ al-Bukhārī,
vol. 1 (Beirut: Dār al-Maʿrifah, 1379 H),
45.
```

Namun citation tersebut tetap menyimpan:

```text
source_id
page_id
chunk_id
content_hash
```

Jadi citation manusia dan provenance mesin hidup berdampingan.

---

# 24.3 Dua Layer Citation

Gunakan dua lapisan.

### Machine Citation

```text
FB-V1-P45-C003
```

### Scholarly Citation

```text
Ibn Hajar, Fath al-Bari,
1:45.
```

Relasinya:

```text
FB-V1-P45-C003
        │
        ▼
Citation Record
        │
        ▼
"Ibn Hajar, Fath al-Bari, 1:45"
```

---

# 24.4 Citation Object

Buat model:

```text
app/citation/models.py
```

```python
from pydantic import BaseModel
from typing import Optional


class Citation(BaseModel):
    id: str

    source_id: str
    page_id: Optional[str] = None
    chunk_id: Optional[str] = None

    author: Optional[str] = None
    title: str

    volume: Optional[int] = None
    page: Optional[int] = None

    publisher: Optional[str] = None
    publication_place: Optional[str] = None
    publication_year: Optional[str] = None

    isbn: Optional[str] = None
    doi: Optional[str] = None

    language: Optional[str] = None

    locator: Optional[str] = None
```

---

# 24.5 Source Bibliographic Record

Pisahkan metadata buku dari citation.

```sql
CREATE TABLE bibliographic_sources (
    id UUID PRIMARY KEY,

    source_type VARCHAR(40) NOT NULL,

    title TEXT NOT NULL,

    subtitle TEXT,

    language VARCHAR(20),

    publisher TEXT,

    publication_place TEXT,

    publication_year TEXT,

    edition TEXT,

    isbn TEXT,

    issn TEXT,

    doi TEXT,

    url TEXT,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 24.6 Authors

Jangan menyimpan author hanya sebagai string.

Buat entitas author.

```sql
CREATE TABLE authors (
    id UUID PRIMARY KEY,

    canonical_name TEXT NOT NULL,

    arabic_name TEXT,

    transliterated_name TEXT,

    nisbah TEXT,

    birth_year TEXT,

    death_year TEXT,

    authority_ids JSONB DEFAULT '{}',

    metadata JSONB DEFAULT '{}'
);
```

Contoh:

```text
canonical_name:
Ibn Hajar al-'Asqalani

arabic_name:
أحمد بن علي بن حجر العسقلاني

death_year:
852 H
```

---

# 24.7 Book-Author Relation

```sql
CREATE TABLE bibliographic_source_authors (
    source_id UUID NOT NULL
        REFERENCES bibliographic_sources(id),

    author_id UUID NOT NULL
        REFERENCES authors(id),

    role VARCHAR(40) DEFAULT 'author',

    author_order INTEGER,

    PRIMARY KEY(source_id, author_id, role)
);
```

Role:

```text
author
editor
translator
compiler
annotator
commentator
```

---

# 24.8 Edition

Ini sangat penting untuk kitab klasik.

**Jangan menganggap halaman selalu sama.**

Fathul Bari dapat memiliki:

```text
Edition A
Volume 1 → page 45
```

dan:

```text
Edition B
Volume 1 → page 52
```

Karena itu buat:

```sql
CREATE TABLE source_editions (
    id UUID PRIMARY KEY,

    bibliographic_source_id UUID NOT NULL
        REFERENCES bibliographic_sources(id),

    edition_label TEXT,

    publisher TEXT,

    publication_place TEXT,

    publication_year TEXT,

    total_volumes INTEGER,

    metadata JSONB DEFAULT '{}'
);
```

---

# 24.9 Source Page Harus Menunjuk Edition

Struktur:

```text
Book
 │
 └── Edition
       │
       ├── Volume 1
       │      ├── Page 45
       │      └── Page 46
       │
       └── Volume 2
```

Jadi `page = 45` saja **tidak cukup**.

Yang benar:

```text
edition_id
volume_id
page_number
```

---

# 24.10 Citation Locator

Buat format standar:

```json
{
  "edition_id": "...",
  "volume": 1,
  "page": 45,
  "chapter": null,
  "hadith_number": "1"
}
```

Locator dapat berupa:

```text
page
volume
chapter
hadith_number
section
line
paragraph
```

---

# 24.11 Citation Record

```sql
CREATE TABLE citations (
    id UUID PRIMARY KEY,

    workspace_id UUID
        REFERENCES research_workspaces(id),

    bibliographic_source_id UUID NOT NULL
        REFERENCES bibliographic_sources(id),

    edition_id UUID
        REFERENCES source_editions(id),

    page_id UUID,

    chunk_id UUID,

    locator JSONB NOT NULL,

    citation_label TEXT,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 24.12 Citation Styles

Minimal implementasikan:

```text
CHICAGO
TURABIAN
APA
MLA
ISLAMIC_TRADITIONAL
SHORT
CUSTOM
```

Untuk proyek ini saya sarankan **ISLAMIC_TRADITIONAL** menjadi style khusus.

---

# 24.13 Contoh Style

### Full Note

```text
Ibn Hajar al-'Asqalani,
Fath al-Bari bi-Sharh Sahih al-Bukhari,
jil. 1 (Beirut: Dar al-Ma'rifah, 1379 H), 45.
```

### Short Note

```text
Ibn Hajar, Fath al-Bari, 1:45.
```

### Internal

```text
[FB-V1-P45-C003]
```

### Footnote

```text
¹ Ibn Hajar al-'Asqalani,
Fath al-Bari, 1:45.
```

---

# 24.14 Citation Formatter

Buat:

```text
app/citation/formatter.py
```

```python
class CitationFormatter:

    def format_full_note(self, citation):
        author = citation.author
        title = citation.title

        locator = self.format_locator(citation)

        return (
            f"{author}, {title}, "
            f"{locator}."
        )

    def format_short_note(self, citation):
        return (
            f"{citation.author}, "
            f"{citation.title}, "
            f"{citation.volume}:{citation.page}."
        )

    def format_locator(self, citation):
        if citation.volume and citation.page:
            return f"{citation.volume}:{citation.page}"

        if citation.page:
            return f"p. {citation.page}"

        return ""
```

Nanti formatter dibuat lebih kuat untuk berbagai style.

---

# 24.15 Citation Style Interface

Gunakan Strategy Pattern:

```python
class CitationStyle:

    def full_note(self, citation):
        raise NotImplementedError

    def short_note(self, citation):
        raise NotImplementedError

    def bibliography(self, citation):
        raise NotImplementedError
```

Kemudian:

```text
ChicagoStyle
TurabianStyle
APAStyle
IslamicTraditionalStyle
```

---

# 24.16 Citation Manager

```python
class CitationManager:

    def create(self, source, locator):
        ...

    def format(self, citation, style):
        ...

    def bibliography(self, workspace_id, style):
        ...

    def validate(self, citation):
        ...
```

---

# 24.17 Citation Validation

Sebelum citation dipakai:

```text
Citation
 ↓
Source exists?
 ↓
Edition exists?
 ↓
Volume exists?
 ↓
Page exists?
 ↓
Page belongs to edition?
 ↓
Chunk belongs to page?
```

Status:

```text
VALID
PARTIAL
INVALID
```

---

# 24.18 Citation Integrity

Contoh citation:

```text
Fathul Bari, vol. 1, p. 45
```

Sistem memverifikasi:

```text
✓ Book exists
✓ Edition exists
✓ Volume exists
✓ Page exists
✓ Page content exists
✓ Chunk exists
```

Jika halaman tidak ditemukan:

```text
⚠ Page locator could not be verified
```

Jangan diam-diam membuat citation.

---

# 24.19 Citation → Source Viewer

Ketika user mengklik:

```text
Ibn Hajar, Fath al-Bari, 1:45
```

langsung:

```text
Source Viewer
     ↓
Edition
     ↓
Volume 1
     ↓
Page 45
     ↓
Chunk
     ↓
Highlight
```

Ini salah satu fitur paling penting dari seluruh platform.

---

# 24.20 Bibliography Generator

Workspace:

```text
Hadis Niat
```

mempunyai citations:

```text
1. Sahih al-Bukhari
2. Fath al-Bari
3. Sahih Muslim
4. ...
```

Klik:

```text
Generate Bibliography
```

Output:

```text
BIBLIOGRAPHY

Ibn Hajar al-'Asqalani.
Fath al-Bari bi-Sharh Sahih al-Bukhari.
Beirut: Dar al-Ma'rifah, 1379 H.

Al-Bukhari, Muhammad ibn Isma'il.
Sahih al-Bukhari.
...
```

---

# 24.21 Deduplicate Bibliography

Jika 20 citation menunjuk:

```text
Fath al-Bari 1:45
Fath al-Bari 1:46
Fath al-Bari 1:48
```

bibliography hanya:

```text
Ibn Hajar al-'Asqalani.
Fath al-Bari...
```

sedangkan locator berada di footnote.

---

# 24.22 Citation Graph

Sekarang Knowledge Graph kita berkembang:

```text
                 BOOK
                  │
                  ▼
               EDITION
                  │
             ┌────┴────┐
             ▼         ▼
          VOLUME      AUTHOR
             │
             ▼
           PAGE
             │
             ▼
           CHUNK
             │
             ▼
         EVIDENCE
             │
             ▼
          CLAIM
             │
             ▼
          FINDING
```

Ini adalah backbone provenance aplikasi.

---

# 24.23 Citation Graph UI

Tambahkan:

```text
/citations/{citation_id}
```

UI:

```text
┌─────────────────────────────────────────┐
│ CITATION                                │
├─────────────────────────────────────────┤
│ Ibn Hajar al-'Asqalani                  │
│ Fath al-Bari                            │
│                                         │
│ Edition: Dar al-Ma'rifah                │
│ Volume: 1                               │
│ Page: 45                                │
├─────────────────────────────────────────┤
│ USED BY                                 │
│                                         │
│ Finding: Makna Niat                     │
│ Note: Definisi Niat                     │
│ RAG Answer #283                         │
├─────────────────────────────────────────┤
│ [OPEN SOURCE]                           │
└─────────────────────────────────────────┘
```

---

# 24.24 Footnote Engine

Untuk export:

```text
Paragraph
    │
    ├── citation
    │
    └── citation
```

menjadi:

```text
Paragraph text.¹

────────────

¹ Ibn Hajar, Fath al-Bari, 1:45.
```

---

# 24.25 Footnote IDs

Jangan menyimpan nomor footnote secara permanen.

Simpan:

```json
{
  "citation_id": "...",
  "position": 1245
}
```

Nomor:

```text
¹
²
³
```

dihasilkan ketika dokumen dirender.

Ini menghindari masalah ketika user menambahkan citation di tengah dokumen.

---

# 24.26 Bibliography Sorting

Default:

```text
Author surname
```

Tetapi untuk Arab:

```text
Arabic canonical ordering
```

harus configurable.

Misalnya:

```text
Ibn Hajar
Al-Bukhari
Muslim
Al-Nawawi
```

Jangan hard-code satu aturan.

---

# 24.27 Arabic Name Normalization

Problem:

```text
ابن حجر
ابن حجر العسقلاني
أحمد بن علي بن حجر العسقلاني
Ibn Hajar
Ibn Hajar al-Asqalani
```

harus bisa dipetakan ke:

```text
author_id = AUTHOR_IBN_HAJAR
```

Gunakan:

```text
canonical_name
aliases
arabic_name
transliterated_name
```

---

# 24.28 Author Authority Mapping

```json
{
  "author_id": "...",
  "aliases": [
    "Ibn Hajar",
    "Ibn Hajar al-Asqalani",
    "ابن حجر",
    "ابن حجر العسقلاني"
  ]
}
```

Ini akan sangat membantu Knowledge Graph dan search.

---

# 24.29 Hadith Citation

Hadis mempunyai struktur berbeda dari buku.

Contoh:

```text
Sahih al-Bukhari, no. 1.
```

atau:

```text
Sahih Muslim, no. 1907.
```

Maka citation type:

```text
BOOK
HADITH
SHARH
ARTICLE
WEBSITE
MANUSCRIPT
PDF
```

---

# 24.30 Hadith Citation Object

```json
{
  "type": "HADITH",

  "collection": "Sahih al-Bukhari",

  "hadith_number": "1",

  "book": "Bad' al-Wahy",

  "chapter": "...",

  "source_id": "..."
}
```

Formatter:

```text
Sahih al-Bukhari, no. 1.
```

---

# 24.31 Syarah Citation

```json
{
  "type": "SHARH",

  "author": "Ibn Hajar al-'Asqalani",

  "work": "Fath al-Bari",

  "volume": 1,

  "page": 45,

  "chunk_id": "FB-V1-P45-C003"
}
```

Output:

```text
Ibn Hajar, Fath al-Bari, 1:45.
```

---

# 24.32 Source Snapshot

Ini sangat penting untuk audit.

Ketika citation dibuat:

```text
content_hash = abc123...
```

Jika corpus diperbarui:

```text
content_hash = def456...
```

sistem mengetahui bahwa evidence telah berubah.

UI:

```text
⚠ Source updated since citation was created.
[Review]
```

---

# 24.33 Citation Versioning

```sql
CREATE TABLE citation_versions (
    id UUID PRIMARY KEY,

    citation_id UUID NOT NULL
        REFERENCES citations(id),

    version INTEGER NOT NULL,

    locator JSONB NOT NULL,

    content_hash VARCHAR(64),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(citation_id, version)
);
```

---

# 24.34 Export Formats

Stage 24 mendukung:

```text
Markdown
HTML
DOCX
PDF
BibTeX
RIS
CSL-JSON
JSON
```

Prioritas implementasi:

```text
1. Markdown
2. DOCX
3. PDF
4. BibTeX
5. RIS
6. CSL-JSON
```

---

# 24.35 CSL-JSON

Untuk kompatibilitas reference manager:

```json
{
  "type": "book",
  "title": "Fath al-Bari bi-Sharh Sahih al-Bukhari",
  "author": [
    {
      "family": "Ibn Hajar al-'Asqalani"
    }
  ],
  "publisher": "Dar al-Ma'rifah",
  "issued": {
    "raw": "1379 AH"
  }
}
```

CSL-JSON menjadi format internal yang sangat berguna untuk interoperability.

---

# 24.36 BibTeX

Contoh:

```bibtex
@book{ibnhajar_fathalbari,
  author    = {Ibn Hajar al-'Asqalani},
  title     = {Fath al-Bari bi-Sharh Sahih al-Bukhari},
  publisher = {Dar al-Ma'rifah},
  year      = {1379}
}
```

---

# 24.37 RIS

Contoh:

```text
TY  - BOOK
AU  - Ibn Hajar al-'Asqalani
TI  - Fath al-Bari bi-Sharh Sahih al-Bukhari
PB  - Dar al-Ma'rifah
PY  - 1379
ER  -
```

---

# 24.38 Citation API

### Create citation

```http
POST /api/v1/citations
```

Request:

```json
{
  "workspace_id": "...",
  "source_id": "...",
  "edition_id": "...",
  "page_id": "...",
  "chunk_id": "..."
}
```

---

### Format

```http
POST /api/v1/citations/{citation_id}/format
```

```json
{
  "style": "ISLAMIC_TRADITIONAL",
  "format": "FULL_NOTE"
}
```

Response:

```json
{
  "text": "Ibn Hajar al-'Asqalani, Fath al-Bari, 1:45."
}
```

---

# 24.39 Bibliography API

```http
GET /api/v1/workspaces/{workspace_id}/bibliography
```

Parameter:

```text
?style=ISLAMIC_TRADITIONAL
```

---

# 24.40 Export API

```http
POST /api/v1/workspaces/{workspace_id}/export
```

```json
{
  "format": "docx",
  "citation_style": "ISLAMIC_TRADITIONAL",
  "include_notes": true,
  "include_sources": true,
  "include_bibliography": true
}
```

---

# 24.41 Citation Picker UI

Di editor:

```text
[ Insert Citation ]
```

membuka:

```text
┌──────────────────────────────────────────┐
│ SEARCH SOURCES                           │
├──────────────────────────────────────────┤
│ Fath al-Bari                             │
│                                          │
│ 1:45                                     │
│ قوله إنما الأعمال بالنيات                │
│                                          │
│ 1:46                                     │
│ ...                                      │
├──────────────────────────────────────────┤
│ [Insert]                                 │
└──────────────────────────────────────────┘
```

---

# 24.42 Smart Citation

Jika user sedang berada pada:

```text
Fathul Bari
Vol. 1
Page 45
```

dan klik:

```text
Insert Citation
```

sistem otomatis menawarkan:

```text
Ibn Hajar, Fath al-Bari, 1:45.
```

---

# 24.43 Citation Preview

Hover:

```text
[Ibn Hajar, Fath al-Bari, 1:45]
```

muncul:

```text
┌──────────────────────────────┐
│ Fath al-Bari                 │
│ Vol. 1 · p.45                │
│                              │
│ قوله إنما الأعمال بالنيات... │
│                              │
│ [Open Source]                │
└──────────────────────────────┘
```

---

# 24.44 Citation Status Indicator

Gunakan:

```text
✓ VERIFIED
◐ PARTIALLY VERIFIED
⚠ NEEDS REVIEW
✕ INVALID
```

Misalnya:

```text
Ibn Hajar, Fath al-Bari, 1:45 ✓
```

---

# 24.45 Citation Quality

Pisahkan:

```text
Citation Validity
```

dan:

```text
Source Quality
```

Contoh:

```text
Citation:
✓ Valid

Source:
⚠ OCR not reviewed
```

Artinya citation menunjuk ke lokasi yang benar, tetapi teks sumber belum diverifikasi secara manual.

---

# 24.46 Integration dengan Stage 22

RAG sekarang menghasilkan:

```json
{
  "claim": "Ibnu Hajar menjelaskan ...",
  "evidence_id": "...",
  "citation_id": "..."
}
```

Bukan lagi hanya:

```text
[1]
```

Flow:

```text
RAG Evidence
      ↓
Citation Resolver
      ↓
Citation Record
      ↓
Answer
```

---

# 24.47 AI Citation Generation

AI boleh **mengusulkan** citation:

```text
Candidate citation
```

tetapi tidak boleh langsung membuat citation yang tidak ada.

Flow:

```text
AI
 ↓
Citation Candidate
 ↓
Database Verification
 ↓
Valid?
 ├── YES → use
 └── NO  → reject
```

---

# 24.48 Anti-Hallucination Rule

Prompt:

```text
Jangan pernah membuat:
- nomor halaman
- volume
- nomor hadis
- edisi
- penerbit
- DOI
- ISBN

jika informasi tersebut tidak terdapat
dalam metadata sumber.
```

Ini sangat penting untuk aplikasi akademik.

---

# 24.49 Citation Audit

Audit:

```text
User Answer
    │
    ├── Claim 1
    │      └── Citation 1 ✓
    │
    ├── Claim 2
    │      └── Citation 2 ✓
    │
    └── Claim 3
           └── Citation ? ✕
```

Dashboard:

```text
Citation Coverage: 92%

Supported Claims: 23
Unsupported Claims: 2
Uncited Claims: 1
```

---

# 24.50 Citation Coverage

Formula sederhana:

```text
Citation Coverage =
supported factual claims
/
total factual claims
```

Misalnya:

```text
23 / 25 = 92%
```

Untuk mode penelitian, kita bisa menetapkan:

```text
≥ 90%  → Good
≥ 95%  → Excellent
100%   → Ideal
```

Tetapi angka ini adalah **quality metric internal**, bukan jaminan kebenaran ilmiah.

---

# 24.51 Research Document

Pada tahap ini kita dapat membuat:

```text
Research Document
```

Struktur:

```text
Document
│
├── Title
├── Abstract
├── Introduction
├── Hadith
├── Syarah
├── Analysis
├── Findings
├── Conclusion
└── Bibliography
```

Citation terintegrasi ke seluruh dokumen.

---

# 24.52 Database Research Documents

```sql
CREATE TABLE research_documents (
    id UUID PRIMARY KEY,

    workspace_id UUID NOT NULL
        REFERENCES research_workspaces(id),

    title TEXT NOT NULL,

    content JSONB NOT NULL,

    citation_style VARCHAR(50),

    version INTEGER DEFAULT 1,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 24.53 Citation-Aware Editor

Editor sebaiknya menyimpan citation sebagai object:

```json
{
  "type": "citation",
  "citation_id": "...",
  "display": "Ibn Hajar, Fath al-Bari, 1:45"
}
```

bukan hanya string:

```text
"Ibn Hajar, Fath al-Bari, 1:45"
```

Dengan begitu style dapat diubah kapan saja.

---

# 24.54 Ganti Style Secara Global

User menulis:

```text
Chicago
```

kemudian mengubah:

```text
Islamic Traditional
```

seluruh citation otomatis berubah.

```text
Chicago:
Ibn Hajar, Fath al-Bari, 1:45.

Islamic:
Ibn Hajar al-'Asqalani,
Fath al-Bari, jil. 1, hlm. 45.
```

Isi dokumen tidak perlu diedit manual.

---

# 24.55 Definition of Done

Stage 24 selesai apabila:

```text
[ ] Bibliographic source model
[ ] Author model
[ ] Edition model
[ ] Volume/page relationship
[ ] Citation model
[ ] Citation validation
[ ] Citation formatter
[ ] Citation styles
[ ] Islamic citation style
[ ] Hadith citation
[ ] Sharh citation
[ ] Footnote engine
[ ] Bibliography generator
[ ] Citation deduplication
[ ] Citation preview
[ ] Citation → Source Viewer
[ ] Content hash
[ ] Citation versioning
[ ] CSL-JSON
[ ] BibTeX
[ ] RIS
[ ] Markdown export
[ ] DOCX export
[ ] PDF export
[ ] Citation coverage audit
[ ] RAG integration
```

---

# 24.56 Hasil Arsitektur Setelah Stage 24

Sekarang alur penelitian menjadi:

```text
                         USER
                          │
                          ▼
                 RESEARCH WORKSPACE
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          HADITH        SOURCE        NOTES
             │            │            │
             └────────────┼────────────┘
                          ▼
                     RAG ENGINE
                          │
                          ▼
                      EVIDENCE
                          │
                          ▼
                        CLAIM
                          │
                          ▼
                      CITATION
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           FOOTNOTE   BIBLIOGRAPHY  SOURCE
              │                       │
              ▼                       ▼
          DOCUMENT              SOURCE VIEWER
```

---
