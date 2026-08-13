# Stage 27 — Hadith Intelligence & Isnad Graph Engine

Stage 27 membangun **mesin kecerdasan hadis dan sanad** di atas Arabic NLP + Knowledge Graph yang sudah dibuat.

Target akhirnya:

```text
Hadis
 │
 ├── Matan
 ├── Sanad
 │    ├── Perawi 1
 │    ├── Perawi 2
 │    ├── Perawi 3
 │    └── ...
 ├── Mukharij
 ├── Kitab
 ├── Bab
 ├── Nomor Hadis
 ├── Variasi Riwayat
 ├── Status / Grading
 └── Syarah Fathul Bari
          │
          ▼
      Isnad Graph
```

**Catatan arsitektur penting:** Stage ini tidak boleh mengubah hasil NLP menjadi "hukum hadis" secara otomatis. Sistem membedakan antara **data yang ditemukan**, **relasi yang diinferensikan**, dan **penilaian yang diverifikasi**.

---

# 27.1 Tujuan Stage 27

Stage ini harus membuat aplikasi mampu menjawab pertanyaan seperti:

> Hadis ini diriwayatkan melalui siapa saja?

> Apa saja jalur sanad hadis ini?

> Apakah dua hadis memiliki matan yang sama atau hanya mirip?

> Di kitab mana hadis ini muncul?

> Siapa mukharrij-nya?

> Apa hubungan hadis ini dengan penjelasan Ibn Hajar?

> Apakah sanad A dan sanad B memiliki titik pertemuan?

> Variasi lafaz apa yang terdapat pada riwayat-riwayat hadis ini?

---

# 27.2 Arsitektur

```text
                    HADITH
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        MATN         SANAD       METADATA
          │            │
          │            ▼
          │       Narrator NER
          │            │
          │            ▼
          │       Entity Linking
          │            │
          │            ▼
          │       Isnad Parser
          │            │
          └──────┬─────┘
                 ▼
           HADITH GRAPH
                 │
       ┌─────────┼──────────┐
       ▼         ▼          ▼
   Variants    Sources    Fathul Bari
       │         │          │
       └─────────┼──────────┘
                 ▼
             HADITH RAG
```

---

# 27.3 Prinsip Data Model

Jangan menyimpan hadis sebagai satu record besar:

```text
Hadith {
   text
   narrator
   book
   chapter
}
```

Gunakan model relasional + graph.

```text
Hadith
 ├── HadithVariant
 ├── Matn
 ├── Isnād
 ├── Narrator
 ├── Collection
 ├── Book
 ├── Chapter
 ├── Source
 └── Commentary
```

---

# 27.4 Entitas Utama

Tambahkan:

```text
Hadith
HadithVariant
Matn
Isnad
IsnadNode
Narrator
NarratorAlias
Collection
Book
Chapter
HadithReference
HadithGrading
HadithSource
```

---

# 27.5 Hadith Canonical Record

```sql
CREATE TABLE hadiths (
    id UUID PRIMARY KEY,

    canonical_key VARCHAR(255) UNIQUE,

    title TEXT,

    language VARCHAR(10) DEFAULT 'ar',

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

`canonical_key` tidak boleh hanya:

```text
bukhari_1
```

karena nomor hadis berbeda antar-edisi.

Lebih aman:

```text
collection + edition + reference
```

---

# 27.6 Hadith Variant

Satu hadis dapat memiliki banyak riwayat teks.

```sql
CREATE TABLE hadith_variants (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL
        REFERENCES hadiths(id),

    source_id UUID,

    arabic_text TEXT,

    normalized_text TEXT,

    translation TEXT,

    variant_type VARCHAR(40),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

`variant_type`:

```text
FULL
PARTIAL
MATN_VARIANT
SANAD_VARIANT
COMBINED
```

---

# 27.7 Mengapa Variant Sangat Penting?

Misalnya:

```text
Riwayat A:
إنما الأعمال بالنيات

Riwayat B:
إنما الأعمال بالنيات وإنما لكل امرئ ما نوى
```

Jangan membuat dua hadis sepenuhnya terpisah.

Model:

```text
Hadith Canonical
      │
      ├── Variant A
      └── Variant B
```

---

# 27.8 Jangan Menentukan "Hadis Sama" Hanya dari Kemiripan Embedding

Gunakan beberapa sinyal:

```text
Exact normalized matn
        +
Lexical overlap
        +
Semantic similarity
        +
Narrator overlap
        +
Collection metadata
        +
Reference metadata
```

Kemudian:

```text
MATCH
POSSIBLE_MATCH
RELATED
UNRELATED
```

---

# 27.9 Hadith Matching Score

Contoh internal scoring:

```text
Matn exact          0.35
Lexical similarity  0.20
Semantic similarity 0.20
Sanad similarity    0.15
Metadata             0.10
```

Sekali lagi, ini **initial heuristic**, bukan nilai final. Bobot harus diuji dengan dataset hadis yang telah diverifikasi.

---

# 27.10 Matn Fingerprint

Buat fingerprint:

```text
raw_text
normalized_text
token_hash
lemma_hash
semantic_embedding
```

Contoh:

```json
{
  "raw_hash": "...",
  "normalized_hash": "...",
  "lemma_hash": "...",
  "embedding_id": "emb_001"
}
```

Ini mempercepat pencarian riwayat paralel.

---

# 27.11 Isnad Model

Sanad harus dimodelkan sebagai **ordered chain**.

```text
A
 ↓
B
 ↓
C
 ↓
Prophet ﷺ
```

Urutan sangat penting.

Jangan hanya menyimpan:

```text
A connected_to B
```

karena kehilangan arah dan posisi.

---

# 27.12 Isnad Table

```sql
CREATE TABLE isnads (
    id UUID PRIMARY KEY,

    hadith_variant_id UUID NOT NULL
        REFERENCES hadith_variants(id),

    extraction_method VARCHAR(40),

    confidence NUMERIC(6,5),

    verification_status VARCHAR(30)
        DEFAULT 'UNVERIFIED',

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 27.13 Isnad Nodes

```sql
CREATE TABLE isnad_nodes (
    id UUID PRIMARY KEY,

    isnad_id UUID NOT NULL
        REFERENCES isnads(id),

    position INTEGER NOT NULL,

    narrator_entity_id UUID,

    surface_name TEXT NOT NULL,

    normalized_name TEXT,

    role VARCHAR(30),

    confidence NUMERIC(6,5),

    verification_status VARCHAR(30)
        DEFAULT 'UNVERIFIED'
);
```

Role:

```text
NARRATOR
COMPANION
PROPHET
UNKNOWN
```

---

# 27.14 Isnad Edges

```sql
CREATE TABLE isnad_edges (
    id UUID PRIMARY KEY,

    isnad_id UUID NOT NULL
        REFERENCES isnads(id),

    from_node_id UUID NOT NULL,

    to_node_id UUID NOT NULL,

    transmission_term TEXT,

    edge_type VARCHAR(30),

    confidence NUMERIC(6,5),

    verification_status VARCHAR(30)
        DEFAULT 'UNVERIFIED'
);
```

Contoh:

```text
حدثنا
حدثني
أخبرنا
سمعت
عن
قال
```

---

# 27.15 Transmission Term

Jangan membuang kata sanad.

Simpan:

```json
{
  "surface": "حدثنا",
  "normalized": "حدثنا",
  "semantic_type": "TRANSMISSION"
}
```

Karena lafaz periwayatan memiliki nilai ilmiah.

---

# 27.16 Isnad Parser

Pipeline:

```text
Arabic Hadith
     ↓
Segment Sanad / Matn
     ↓
Transmission Marker Detection
     ↓
Name Detection
     ↓
Entity Linking
     ↓
Sequence Construction
     ↓
Isnad Graph
```

---

# 27.17 Sanad-Matn Boundary

Ini salah satu bagian tersulit.

Contoh sederhana:

```text
حدثنا مالك عن نافع عن ابن عمر قال...
أن رسول الله ﷺ قال...
```

Sistem harus memperkirakan:

```text
SANAD
────────────
حدثنا مالك
عن نافع
عن ابن عمر
قال

MATN
────────────
أن رسول الله ﷺ قال...
```

Tetapi boundary tidak selalu eksplisit.

Karena itu:

```text
boundary_confidence
```

harus disimpan.

---

# 27.18 Boundary Model

```json
{
  "sanad_start": 0,
  "sanad_end": 48,
  "matn_start": 49,
  "confidence": 0.87
}
```

Jika tidak yakin:

```text
status = NEEDS_REVIEW
```

---

# 27.19 Narrator Entity Linking

Contoh:

```text
ابن عمر
```

candidate:

```text
عبد الله بن عمر بن الخطاب
```

Simpan:

```json
{
  "surface": "ابن عمر",
  "candidate_entity": "person_123",
  "confidence": 0.97,
  "resolution_method": "ALIAS_MATCH"
}
```

---

# 27.20 Jangan Menghapus Nama Asli

Database harus menyimpan:

```text
surface_name:
ابن عمر

canonical_name:
عبد الله بن عمر بن الخطاب
```

Karena penelitian sanad perlu mengetahui **lafaz asli sumber**.

---

# 27.21 Narrator Alias Table

```sql
CREATE TABLE narrator_aliases (
    id UUID PRIMARY KEY,

    narrator_id UUID NOT NULL,

    alias TEXT NOT NULL,

    normalized_alias TEXT NOT NULL,

    source VARCHAR(50),

    confidence NUMERIC(6,5)
);
```

Contoh:

```text
ابن عمر
عبد الله بن عمر
عبد الله بن عمر بن الخطاب
```

---

# 27.22 Narrator Authority Record

Tambahkan:

```sql
CREATE TABLE narrators (
    id UUID PRIMARY KEY,

    canonical_name TEXT NOT NULL,

    arabic_name TEXT,

    kunya TEXT,

    nasab TEXT,

    nisbah TEXT,

    birth_year INTEGER,

    death_year INTEGER,

    metadata JSONB DEFAULT '{}'
);
```

Field tahun tidak selalu tersedia, sehingga nullable.

---

# 27.23 Narrator Relationship

Knowledge Graph:

```text
Narrator
 ├── teacher_of
 ├── student_of
 ├── narrated_from
 ├── contemporary_of
 ├── relative_of
 └── mentioned_by
```

Namun setiap relasi harus mempunyai provenance.

---

# 27.24 Teacher-Student Graph

```text
مالك
  │
  │ teacher_of
  ▼
نافع
  │
  │ teacher_of
  ▼
ابن عمر
```

Simpan:

```text
source
evidence
confidence
verification
```

---

# 27.25 Evidence-backed Relationship

```json
{
  "from": "person_001",
  "relation": "TEACHER_OF",
  "to": "person_002",
  "evidence": [
    "FB-V2-P134-C02"
  ],
  "confidence": 0.91,
  "status": "VERIFIED"
}
```

---

# 27.26 Isnad Graph Visualization

UI:

```text
┌───────────────────────────────────────────────┐
│ ISNAD GRAPH                                   │
│                                               │
│   ┌───────┐                                   │
│   │ Malik │                                   │
│   └───┬───┘                                   │
│       │ حدثنا                                  │
│       ▼                                       │
│   ┌───────┐                                   │
│   │ Nafi' │                                   │
│   └───┬───┘                                   │
│       │ عن                                    │
│       ▼                                       │
│ ┌───────────────┐                             │
│ │ Ibn Umar      │                             │
│ └───────┬───────┘                             │
│         │ قال                                  │
│         ▼                                     │
│      Prophet ﷺ                                │
└───────────────────────────────────────────────┘
```

---

# 27.27 Graph Interaction

Klik perawi:

```text
Ibn Umar
```

muncul:

```text
┌─────────────────────────────┐
│ عبد الله بن عمر             │
├─────────────────────────────┤
│ Narrations:  xxx            │
│ Teachers:    xxx            │
│ Students:    xxx            │
│ Collections: xxx            │
│                             │
│ [Open Narrator Profile]     │
└─────────────────────────────┘
```

---

# 27.28 Hadith Variant Graph

```text
                  HADITH
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      Variant A   Variant B   Variant C
        │           │           │
       Bukhari     Muslim      Other
        │           │           │
      Sanad A      Sanad B     Sanad C
```

---

# 27.29 Cross-Collection Mapping

Buat:

```sql
CREATE TABLE hadith_references (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL,

    collection_id UUID NOT NULL,

    book_id UUID,

    chapter_id UUID,

    hadith_number TEXT,

    edition TEXT,

    page TEXT,

    reference_label TEXT,

    verification_status VARCHAR(30)
);
```

Ini menghindari masalah:

```text
"Bukhari 1"
```

yang bisa ambigu antar-edisi.

---

# 27.30 Reference Example

```json
{
  "collection": "Sahih al-Bukhari",
  "book": "Beginning of Revelation",
  "chapter": "...",
  "hadith_number": "1",
  "edition": "configured edition",
  "page": "..."
}
```

---

# 27.31 Mukharij

Tambahkan:

```text
MUKHARRIJ
```

sebagai relationship:

```text
Hadith
 ├── narrated_in → Bukhari
 ├── narrated_in → Muslim
 ├── narrated_in → Abu Dawud
 └── ...
```

Jangan otomatis menyimpulkan semua kitab yang memiliki matan mirip sebagai mukharrij yang sama.

---

# 27.32 Hadith Grading

Model:

```sql
CREATE TABLE hadith_gradings (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL,

    grader_entity_id UUID,

    grading TEXT NOT NULL,

    grading_scope VARCHAR(40),

    source_id UUID,

    evidence TEXT,

    confidence NUMERIC(6,5),

    verification_status VARCHAR(30)
);
```

Contoh:

```text
صحيح
حسن
ضعيف
```

---

# 27.33 Grading Provenance

Jangan:

```text
hadith.grade = "SAHIH"
```

secara global.

Lebih benar:

```text
Bukhari → grading: ...
Muslim → grading: ...
Scholar X → grading: ...
Scholar Y → grading: ...
```

Dengan demikian perbedaan penilaian tetap terlihat.

---

# 27.34 Grading UI

```text
HADITH GRADING

┌──────────────────────────────────────┐
│ Source        Grader        Grade    │
├──────────────────────────────────────┤
│ Source A       ...          Sahih    │
│ Source B       ...          Hasan    │
│ Source C       ...          Da'if    │
└──────────────────────────────────────┘
```

Jangan membuat satu "AI grade" seolah-olah menggantikan ulama.

---

# 27.35 Fathul Bari Link

Inilah hubungan utama aplikasi.

```text
Hadith
   │
   ├── Bukhari Reference
   │
   └── Fathul Bari Commentary
             │
             ├── Explanation
             ├── Linguistic Analysis
             ├── Fiqh
             ├── Narrator Discussion
             ├── Variant Discussion
             └── Reconciliation
```

---

# 27.36 Commentary Relation

```sql
CREATE TABLE hadith_commentary_links (
    id UUID PRIMARY KEY,

    hadith_id UUID NOT NULL,

    commentary_source_id UUID NOT NULL,

    chunk_id UUID,

    relation_type VARCHAR(40),

    evidence TEXT,

    confidence NUMERIC(6,5),

    verification_status VARCHAR(30)
);
```

Relation:

```text
DIRECT_COMMENTARY
VARIANT_DISCUSSION
NARRATOR_DISCUSSION
LINGUISTIC_DISCUSSION
FIQH_DISCUSSION
CONTEXTUAL_DISCUSSION
```

---

# 27.37 Fathul Bari Retrieval

Ketika user membuka:

```text
Sahih al-Bukhari #1
```

UI:

```text
┌───────────────────────────────────────────┐
│ HADITH                                    │
│ إنما الأعمال بالنيات...                   │
├───────────────────────────────────────────┤
│ SANAD                                     │
│ Malik → Nafi' → Ibn Umar → Prophet ﷺ     │
├───────────────────────────────────────────┤
│ FATHUL BARI                               │
│                                           │
│ Ibn Hajar explains...                     │
│                                           │
│ [Open Source] [Evidence]                  │
└───────────────────────────────────────────┘
```

---

# 27.38 Hadith Intelligence Panel

Tambahkan panel:

```text
INTELLIGENCE

Narrators              4
Variants                7
Collections             3
Related Hadiths        12
Commentary Chunks       9
Verified Relations      8
Needs Review             2
```

---

# 27.39 Variant Comparison

UI:

```text
┌───────────────────────────────────────────────┐
│ RIWAYAT COMPARISON                            │
├───────────────────────────────────────────────┤
│ Bukhari                                       │
│ إنما الأعمال بالنيات...                       │
│                                               │
│ Muslim                                        │
│ إنما الأعمال بالنيات وإنما لكل امرئ...       │
│                                               │
│ Other                                         │
│ ...                                           │
└───────────────────────────────────────────────┘
```

Highlight:

```text
ADDED
REMOVED
CHANGED
```

---

# 27.40 Arabic Diff Engine

Jangan menggunakan character diff saja.

Gunakan:

```text
Character diff
        +
Token diff
        +
Lemma diff
```

Contoh:

```text
Token:
إنما | الأعمال | بالنيات

Lemma:
إنما | عمل | نية
```

Ini membuat perbandingan lebih bermakna.

---

# 27.41 Hadith Similarity Search

Endpoint:

```http
GET /api/v1/hadith/{id}/related
```

Response:

```json
{
  "results": [
    {
      "hadith_id": "h_002",
      "relation": "POSSIBLE_VARIANT",
      "score": 0.94
    },
    {
      "hadith_id": "h_003",
      "relation": "RELATED",
      "score": 0.82
    }
  ]
}
```

---

# 27.42 Sanad Similarity

Dua hadis:

```text
A → B → C → Prophet
```

dan:

```text
A → B → D → Prophet
```

memiliki:

```text
common_prefix = A → B
```

Gunakan untuk mencari **common isnad pathways**.

---

# 27.43 Isnad Path Comparison

```text
Path A:
Malik → Nafi' → Ibn Umar

Path B:
Malik → Nafi' → Salim → Ibn Umar
```

UI:

```text
Common:
Malik → Nafi'

Divergence:
Nafi'
   ├── Ibn Umar
   └── Salim
```

---

# 27.44 Isnad Graph Query

Pertanyaan:

> Siapa saja perawi yang menjadi titik temu dua jalur hadis?

Query:

```text
Hadith A
 ↓
Ancestors
 ↓
Intersection
 ↓
Hadith B
```

Hasil:

```text
Common Narrators:
1. Malik
2. Nafi'
```

---

# 27.45 Graph Database atau PostgreSQL?

Untuk tahap ini saya sarankan **jangan langsung memindahkan seluruh sistem ke Neo4j**.

Gunakan:

```text
PostgreSQL
+
pgvector
+
Graph abstraction
```

terlebih dahulu.

Alasan:

```text
Hadith
Source
Citation
Review
Audit
NLP
Publication
```

semuanya sudah relational.

Graph layer dapat dibangun di atasnya.

---

# 27.46 Graph Projection

Buat view/logical projection:

```text
PostgreSQL
     │
     ▼
Graph Projection
     │
     ▼
Narrator Graph
Hadith Graph
Source Graph
Concept Graph
```

Jika nanti graph menjadi sangat besar, baru evaluasi graph database khusus.

---

# 27.47 Graph Edge Provenance

Setiap edge:

```text
A ──TEACHER_OF──> B
```

harus menyimpan:

```json
{
  "source": "source_001",
  "chunk": "chunk_445",
  "extraction": "NLP",
  "confidence": 0.88,
  "verification": "UNVERIFIED"
}
```

Ini prinsip yang sama dengan Stage 25.

---

# 27.48 Human Verification

Graph reviewer:

```text
┌─────────────────────────────────────┐
│ RELATION REVIEW                     │
├─────────────────────────────────────┤
│ Malik → Nafi'                       │
│                                     │
│ Relation: TEACHER_OF                │
│ Confidence: 0.94                   │
│ Evidence: Source X, p. 123         │
│                                     │
│ [Verify] [Reject] [Edit]            │
└─────────────────────────────────────┘
```

---

# 27.49 Isnad Quality Dashboard

```text
ISNAD DATA QUALITY

Total Hadith                15,240
Parsed Sanads               12,832
Entity-linked               10,991
Verified chains              8,421

Needs review                 2,570
Unknown narrators              418
```

Angka ini akan berasal dari database aktual, bukan hard-coded.

---

# 27.50 Unknown Narrator Queue

Jika:

```text
حدثنا رجل
```

atau nama tidak dapat diidentifikasi:

```text
UNKNOWN_NARRATOR
```

Jangan dipaksa menjadi entity tertentu.

UI:

```text
Unknown Narrator #341

Surface:
رجل

Possible candidates:
1. ...
2. ...

[Research]
```

---

# 27.51 Hadith Intelligence API

Tambahkan endpoint:

```http
GET /api/v1/hadith/{id}/intelligence
```

Response:

```json
{
  "hadith": {},
  "variants": [],
  "isnads": [],
  "narrators": [],
  "collections": [],
  "gradings": [],
  "commentary": [],
  "related_hadiths": []
}
```

---

# 27.52 Full Hadith Profile

Route:

```text
/hadith/{hadithId}
```

Layout:

```text
┌─────────────────────────────────────────────────────┐
│ HADITH INTELLIGENCE                                 │
├──────────────────────┬──────────────────────────────┤
│ MATN                 │ METADATA                     │
│                      │                              │
│ Arabic text          │ Bukhari                      │
│                      │ Book: Revelation              │
│ Translation          │ Hadith: #1                    │
│                      │                              │
├──────────────────────┴──────────────────────────────┤
│ ISNAD GRAPH                                          │
├─────────────────────────────────────────────────────┤
│ VARIANTS                                             │
├─────────────────────────────────────────────────────┤
│ FATHUL BARI                                          │
├─────────────────────────────────────────────────────┤
│ GRADING                                              │
├─────────────────────────────────────────────────────┤
│ SOURCES                                              │
└─────────────────────────────────────────────────────┘
```

---

# 27.53 Integrasi Ahmad Sanusi Hadits API

Karena aplikasi Anda memang dirancang terintegrasi dengan **Ahmad Sanusi Hadits API**, gunakan API tersebut sebagai salah satu **ingestion/source adapter**, bukan sebagai satu-satunya sumber kebenaran internal.

Arsitektur:

```text
Ahmad Sanusi Hadits API
          │
          ▼
     Source Adapter
          │
          ▼
    Raw Hadith Store
          │
          ▼
 Normalization / NLP
          │
          ▼
 Canonical Hadith Model
          │
          ▼
 Isnad + Knowledge Graph
```

Dengan demikian jika API berubah:

```text
API v1
  ↓
Adapter v1

API v2
  ↓
Adapter v2
```

database internal tetap stabil.

---

# 27.54 Source Adapter Contract

```python
class HadithSourceAdapter:

    def search(self, query):
        ...

    def get_hadith(self, external_id):
        ...

    def get_collection(self, collection_id):
        ...

    def get_metadata(self):
        ...
```

Implementasi:

```text
AhmadSanusiAdapter
BukhariAdapter
MuslimAdapter
LocalCorpusAdapter
```

---

# 27.55 Raw Data Layer

Simpan respons API mentah.

```sql
CREATE TABLE source_raw_records (
    id UUID PRIMARY KEY,

    source_id UUID NOT NULL,

    external_id TEXT,

    payload JSONB NOT NULL,

    content_hash TEXT NOT NULL,

    fetched_at TIMESTAMPTZ DEFAULT NOW()
);
```

Ini penting untuk audit.

---

# 27.56 Ingestion Flow

```text
API
 ↓
Raw JSON
 ↓
Hash
 ↓
Validate
 ↓
Normalize
 ↓
Deduplicate
 ↓
Canonical Hadith
 ↓
NLP
 ↓
Graph
 ↓
Index
```

---

# 27.57 Deduplication

Gunakan:

```text
external_id
+
source_id
+
content_hash
```

Jika teks berubah:

```text
old hash
    ↓
new hash
```

buat **new source version**, jangan overwrite tanpa histori.

---

# 27.58 Source Version

```sql
CREATE TABLE source_versions (
    id UUID PRIMARY KEY,

    source_id UUID NOT NULL,

    version_label TEXT,

    content_hash TEXT,

    retrieved_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 27.59 Event Audit

Setiap ingestion:

```text
API_FETCHED
RAW_SAVED
NORMALIZED
NLP_COMPLETED
ENTITY_LINKED
GRAPH_UPDATED
INDEX_UPDATED
```

masuk audit trail.

---

# 27.60 RAG Setelah Stage 27

RAG sekarang jauh lebih kuat:

```text
                    QUERY
                      │
                      ▼
                Arabic NLP
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     Terms          Entities       Hadith
       │              │              │
       └──────────────┼──────────────┘
                      ▼
               Hybrid Retrieval
                      │
             ┌────────┼─────────┐
             ▼        ▼         ▼
          Hadith    Isnad     Fathul Bari
          Variants  Graph     Commentary
             │        │         │
             └────────┼─────────┘
                      ▼
                   Reranker
                      │
                      ▼
                   Evidence
                      │
                      ▼
                 AI Assistant
```

---

# 27.61 Contoh Pertanyaan Kompleks

User:

> Bagaimana Ibn Hajar menjelaskan hadis tentang niat, siapa saja perawi dalam jalurnya, dan apakah terdapat variasi matan dalam riwayat lain?

Sistem melakukan:

```text
1. Identify hadith
2. Identify Fathul Bari commentary
3. Extract relevant commentary
4. Traverse isnad graph
5. Find hadith variants
6. Compare matn
7. Retrieve evidence
8. Generate answer
9. Attach citations
```

Ini jauh lebih kuat daripada:

```text
prompt → embedding → LLM
```

---

# 27.62 Output AI

Jawaban ideal:

```text
Hadis tersebut diriwayatkan melalui jalur ...

Jalur sanad:
A → B → C → ...

Dalam Fathul Bari, Ibn Hajar menjelaskan ...

Terdapat beberapa variasi riwayat. Pada riwayat X,
lafaz ... muncul, sedangkan riwayat Y memiliki ...

[Sumber hadis]
[Sumber Fathul Bari]
[Perbandingan riwayat]
```

Setiap klaim memiliki provenance.

---

# 27.63 Guardrail Hadith AI

Tambahkan aturan sistem:

```text
1. Jangan membuat sanad.
2. Jangan menggabungkan dua sanad berbeda tanpa label.
3. Jangan menyebut perawi jika entity belum cukup terverifikasi.
4. Jangan mengubah grading menjadi kesimpulan final.
5. Jangan menganggap hadis semakna sebagai hadis identik.
6. Jangan menyatakan Ibn Hajar mengatakan sesuatu tanpa evidence.
7. Bedakan teks sumber dan interpretasi AI.
8. Selalu tampilkan source provenance untuk klaim hadis.
```

---

# 27.64 Definition of Done

Stage 27 dianggap selesai apabila:

```text
[ ] Canonical Hadith model
[ ] Hadith variants
[ ] Matn fingerprint
[ ] Hadith matching
[ ] Sanad parser
[ ] Sanad/matn boundary
[ ] Narrator entity linking
[ ] Narrator aliases
[ ] Isnad nodes
[ ] Isnad edges
[ ] Transmission terms
[ ] Isnad graph
[ ] Teacher/student relations
[ ] Cross-collection references
[ ] Mukharij relations
[ ] Grading provenance
[ ] Variant comparison
[ ] Arabic diff
[ ] Isnad comparison
[ ] Unknown narrator queue
[ ] Human verification
[ ] Hadith intelligence API
[ ] Hadith profile UI
[ ] Ahmad Sanusi adapter
[ ] Raw source storage
[ ] Source versioning
[ ] Ingestion audit
[ ] RAG integration
```

---

# 27.65 Struktur Folder

```text
backend/
└── app/
    ├── hadith/
    │   ├── models.py
    │   ├── canonical.py
    │   ├── variants.py
    │   ├── matching.py
    │   ├── grading.py
    │   └── references.py
    │
    ├── isnad/
    │   ├── parser.py
    │   ├── boundary.py
    │   ├── nodes.py
    │   ├── edges.py
    │   ├── resolver.py
    │   ├── comparison.py
    │   └── graph.py
    │
    ├── narrators/
    │   ├── models.py
    │   ├── aliases.py
    │   ├── authority.py
    │   └── linking.py
    │
    ├── sources/
    │   ├── adapters/
    │   │   ├── base.py
    │   │   └── ahmad_sanusi.py
    │   ├── raw_store.py
    │   ├── versions.py
    │   └── ingestion.py
    │
    └── api/
        ├── hadith.py
        ├── isnad.py
        └── narrators.py
```

---

# 27.66 Arsitektur Milestone Sekarang

Setelah Stage 27, sistem kita sudah berkembang menjadi:

```text
┌───────────────────────────────────────────────────────────┐
│                  PUBLICATION LAYER                        │
│ Research · Review · Citation · PDF · DOCX                │
├───────────────────────────────────────────────────────────┤
│                     RAG LAYER                             │
│ Query · Retrieval · Reranking · Evidence · AI            │
├───────────────────────────────────────────────────────────┤
│                 HADITH INTELLIGENCE                       │
│ Variants · Isnad · Narrators · Grading · Cross-reference │
├───────────────────────────────────────────────────────────┤
│                    ARABIC NLP                             │
│ Token · Lemma · Root · Morphology · NER                  │
├───────────────────────────────────────────────────────────┤
│                  KNOWLEDGE GRAPH                          │
│ Hadith · Narrator · Scholar · Book · Concept             │
├───────────────────────────────────────────────────────────┤
│                    SOURCE LAYER                           │
│ Ahmad Sanusi API · Fathul Bari · Local Corpus            │
├───────────────────────────────────────────────────────────┤
│                    AUDIT LAYER                            │
│ Provenance · Version · Hash · Review · Audit Trail       │
└───────────────────────────────────────────────────────────┘
```
