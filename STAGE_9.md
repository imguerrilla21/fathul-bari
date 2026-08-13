Baik. **Stage 9 — Knowledge Graph** kita bangun sebagai lapisan relasional di atas data hadis, Syarah Fathul Bari, dan hasil verifikasi Stage 4–8.

Tujuan utamanya bukan sekadar membuat visualisasi graph, tetapi membuat aplikasi mampu menjawab pertanyaan seperti:

> “Hadis apa saja yang disyarah Ibnu Hajar dalam pembahasan ini?”

> “Apa hubungan hadis Bukhari #1 dengan bagian-bagian Fathul Bari?”

> “Hadis mana yang memiliki syarah yang sama?”

> “Di mana sumber primer untuk hubungan tersebut?”

---

# Stage 9 — Knowledge Graph Architecture

```text
                         USER QUERY
                             │
                             ▼
                      RAG / Search
                             │
                             ▼
                     KNOWLEDGE GRAPH
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
     HADITH                SHARH                SOURCE
       │                     │                     │
       │                     │                     │
       ├───────[:EXPLAINED_BY]──────►│             │
       │                     │        │             │
       │                     ├────────┴──[:LOCATED_IN]
       │                     │                     │
       │                     │                     ▼
       │                     │                PDF PAGE
       │                     │
       └────[:IN_COLLECTION]─► BUKHARI
```

Tetapi saya sarankan **jangan langsung memakai Neo4j sebagai database utama**.

Untuk aplikasi kita:

```text
PostgreSQL
    │
    ├── authoritative data
    ├── audit trail
    ├── embeddings
    └── knowledge graph edges
             │
             ▼
       Graph API
             │
             ▼
      Visualization
```

Dengan demikian PostgreSQL tetap menjadi **source of truth**.

---

# 1. Model Knowledge Graph

Kita mulai dengan 7 node utama.

```text
Hadith
Collection
Book
Chapter
SharhSection
SourcePage
Person
```

Secara konseptual:

```text
Collection
    │
    └── Book
          │
          └── Chapter
                 │
                 └── Hadith
                        │
                        │ explained_by
                        ▼
                  SharhSection
                        │
                        │ located_on
                        ▼
                    SourcePage
```

Untuk Fathul Bari:

```text
Person
  │
  │ authored
  ▼
Fathul Bari
  │
  ▼
SharhSection
```

---

# 2. Relationship

Relationship awal:

```text
IN_COLLECTION
BELONGS_TO_BOOK
BELONGS_TO_CHAPTER

EXPLAINED_BY
REFERENCES
RELATED_TO

LOCATED_IN
NEXT_SECTION
PREVIOUS_SECTION

AUTHORED_BY
```

Contoh:

```text
Bukhari #1
    │
    └── EXPLAINED_BY
             │
             ▼
      Fathul Bari §001
             │
             └── LOCATED_IN
                       │
                       ▼
                 Volume 1
                 PDF p.45
                 Print p.12
```

---

# 3. Relationship harus memiliki provenance

Ini sangat penting.

Jangan membuat:

```json
{
  "from": "hadith-1",
  "to": "sharh-001",
  "relation": "EXPLAINED_BY"
}
```

saja.

Gunakan:

```json
{
  "from": "hadith-1",
  "to": "sharh-001",
  "relation": "EXPLAINED_BY",

  "confidence": 0.96,
  "verified": true,

  "evidence": {
    "source_page": 45,
    "pdf": "fathul-bari-vol-1.pdf"
  },

  "created_by": "matching-engine",
  "verified_by": "reviewer",
  "verified_at": "..."
}
```

Dengan demikian graph kita **auditable**.

---

# 4. Database schema

Tambahkan:

```sql
graph_nodes
graph_edges
```

### graph_nodes

```text
id
node_type
entity_id
label
metadata
created_at
updated_at
```

Contoh:

```json
{
  "id": "...",
  "node_type": "hadith",
  "entity_id": "...",
  "label": "Sahih al-Bukhari #1"
}
```

### graph_edges

```text
id
source_node_id
target_node_id
relation_type
confidence
verified
evidence_id
created_at
```

---

# 5. Graph harus berasal dari data terverifikasi

Pipeline:

```text
Hadith
  │
  ▼
Matching
  │
  ▼
Candidate
  │
  ▼
Human Review
  │
  ├── REJECT ──► STOP
  │
  └── VERIFY
          │
          ▼
    Knowledge Graph
```

Artinya:

> **Rejected relationship tidak boleh masuk ke verified graph.**

Unverified candidate masih boleh disimpan dalam **candidate graph**, tetapi harus diberi status berbeda.

---

# 6. Dua Graph

Saya sarankan kita mempunyai:

### Verified Graph

```text
verified = true
```

Digunakan oleh:

* Research Mode
* RAG
* citation
* analytics

### Candidate Graph

```text
verified = false
```

Digunakan untuk:

* review
* discovery
* menemukan kemungkinan hubungan baru

Visual:

```text
             KNOWLEDGE GRAPH
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   VERIFIED GRAPH       CANDIDATE GRAPH
          │                   │
       RAG/API             Reviewer
```

---

# 7. Graph API

Tambahkan endpoint:

```http
GET /api/v1/graph/hadith/{hadith_id}
```

Mengambil seluruh hubungan sebuah hadis.

Contoh response:

```json
{
  "node": {
    "type": "hadith",
    "label": "Sahih al-Bukhari #1"
  },

  "edges": [
    {
      "relation": "EXPLAINED_BY",
      "target": {
        "type": "sharh",
        "label": "Fathul Bari §1"
      },
      "confidence": 0.96,
      "verified": true
    }
  ]
}
```

---

# 8. Neighbor Search

Endpoint:

```http
GET /api/v1/graph/node/{node_id}/neighbors
```

Contoh:

```text
Hadith #1
    │
    ├── Fathul Bari §1
    │      │
    │      ├── Source p.12
    │      └── Volume 1
    │
    ├── Related Hadith #2
    │
    └── Chapter: Beginning of Revelation
```

---

# 9. Multi-hop Query

Ini yang mulai membuat aplikasi menjadi menarik.

Misalnya:

> “Tampilkan hadis yang memiliki hubungan dengan pembahasan niat dan berada dalam bab yang sama.”

Graph query:

```text
Hadith
   │
   ▼
SharhSection
   │
   ▼
Chapter
   │
   ▼
Other Hadith
```

Atau:

```text
Hadith A
   ↓
Sharh A
   ↓
Topic
   ↓
Sharh B
   ↓
Hadith B
```

Dengan graph kita bisa menemukan hubungan yang sulit ditemukan dengan keyword search saja.

---

# 10. Topic Node

Setelah graph dasar stabil, tambahkan:

```text
Topic
```

Contoh:

```text
Topic: NIAT
Topic: IKHLAS
Topic: SHALAT
Topic: WUDHU
Topic: IMAN
Topic: AKHLAK
```

Kemudian:

```text
Hadith #1
      │
      └── ABOUT
            │
            ▼
          NIAT
            ▲
            │
      DISCUSSES
            │
      Fathul Bari §1
```

**Namun topic yang dihasilkan AI harus tetap diberi provenance.**

---

# 11. Person Entity

Kemudian:

```text
Person
```

Contoh:

```text
Ibn Hajar al-Asqalani
```

Relasi:

```text
Ibn Hajar
    │
    └── AUTHORED
           │
           ▼
      Fathul Bari
```

Nanti kita bisa menambahkan:

```text
Companion
Narrator
Author
Scholar
```

Tetapi jangan memasukkan identitas yang belum memiliki sumber.

---

# 12. Graph Visualization

Dashboard:

```text
┌──────────────────────────────────────────────────────────┐
│ FATHUL BARI KNOWLEDGE GRAPH                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                    ┌─────────────┐                       │
│                    │ FATHUL BARI │                       │
│                    └──────┬──────┘                       │
│                           │                              │
│                     EXPLAINS                             │
│                           │                              │
│                    ┌──────▼──────┐                       │
│                    │ SHARH §001   │                       │
│                    └──────┬──────┘                       │
│                           │                              │
│                 EXPLAINS  │                              │
│                           ▼                              │
│                    ┌─────────────┐                       │
│                    │ BUKHARI #1  │                       │
│                    └──────┬──────┘                       │
│                           │                              │
│                      LOCATED IN                          │
│                           ▼                              │
│                    ┌─────────────┐                       │
│                    │ VOL 1 P. 12 │                       │
│                    └─────────────┘                       │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ ✓ Verified: 1    Candidate: 2    Confidence: 96%         │
└──────────────────────────────────────────────────────────┘
```

Klik node:

```text
Bukhari #1
```

→ buka hadis.

Klik:

```text
Fathul Bari §001
```

→ buka Review Dashboard.

Klik:

```text
Vol 1 p.12
```

→ buka Source Viewer.

---

# 13. Graph → RAG

Ini bagian terpenting.

Stage 7 sebelumnya:

```text
Query
 ↓
Vector Search
 ↓
Evidence
 ↓
LLM
```

Sekarang:

```text
Query
 ↓
Hybrid Search
 ↓
Knowledge Graph
 ↓
Graph Expansion
 ↓
Verified Evidence
 ↓
Reranker
 ↓
LLM
```

Misalnya query:

> Jelaskan hubungan niat dengan amal.

Search menemukan:

```text
Hadith #1
```

Graph kemudian memperluas:

```text
Hadith #1
     ↓
Fathul Bari §1
     ↓
Topic: Niat
     ↓
Related Sharh Sections
     ↓
Related Hadiths
```

Kemudian RAG mendapatkan evidence yang lebih lengkap.

---

# 14. Graph RAG

Dengan demikian sistem kita berubah menjadi:

```text
             ┌─────────────────┐
             │ User Question   │
             └────────┬────────┘
                      ▼
             ┌─────────────────┐
             │ Hybrid Search   │
             └────────┬────────┘
                      ▼
             ┌─────────────────┐
             │ Knowledge Graph │
             └────────┬────────┘
                      ▼
             ┌─────────────────┐
             │ Graph Expansion │
             └────────┬────────┘
                      ▼
             ┌─────────────────┐
             │ Reranker        │
             └────────┬────────┘
                      ▼
             ┌─────────────────┐
             │ Verified RAG    │
             └────────┬────────┘
                      ▼
             ┌─────────────────┐
             │ AI Assistant    │
             └────────┬────────┘
                      ▼
             Answer + Citations
```

Ini merupakan fondasi **GraphRAG** untuk aplikasi Fathul Bari kita.

---

# 15. Audit Graph

Setiap edge harus dapat menjawab:

```text
Siapa yang membuat hubungan ini?
Dari sumber mana?
Kapan dibuat?
Apakah diverifikasi?
Siapa yang memverifikasi?
Berapa confidence?
```

Contoh:

```text
EXPLAINED_BY
──────────────────────────────
Hadith: Bukhari #1
        ↓
Sharh: Fathul Bari §1

Confidence: 0.96
Status: VERIFIED

Evidence:
Volume: 1
Printed page: 12
PDF page: 45

Created by:
Matching Engine v1.0

Verified by:
Reviewer

Audit ID:
xxxxxxxx
```

---

# 16. Struktur Stage 9

Project nantinya:

```text
backend/app/
│
├── api/
│   ├── graph.py
│   └── graph_search.py
│
├── graph/
│   ├── builder.py
│   ├── nodes.py
│   ├── edges.py
│   ├── traversal.py
│   └── provenance.py
│
├── rag/
│   ├── retriever.py
│   ├── graph_retriever.py
│   └── reranker.py
│
└── models/
    ├── graph_node.py
    └── graph_edge.py
```

Frontend:

```text
frontend/
└── graph/
    ├── GraphViewer
    ├── NodeDetails
    ├── EdgeDetails
    └── SourcePanel
```

---

# 17. Urutan implementasi yang aman

Saya sarankan Stage 9 dikerjakan dalam empat sub-tahap:

### 9A — Graph Schema

```text
graph_nodes
graph_edges
```

### 9B — Graph Builder

Konversi:

```text
hadith_sharh_links
      ↓
graph_edges
```

**hanya verified links sebagai verified edges.**

### 9C — Graph API

```text
/node
/neighbors
/hadith/{id}
/sharh/{id}
/path
```

### 9D — GraphRAG

```text
Search
 ↓
Graph
 ↓
Expansion
 ↓
Reranking
 ↓
RAG
```

---

## Target akhir Stage 9

Aplikasi kita mulai berubah dari sekadar:

> **“AI yang bisa mencari Fathul Bari”**

menjadi:

> **“Knowledge system yang mengetahui hubungan antara hadis, bab, syarah, topik, sumber halaman, dan keputusan verifikasi.”**

Dan prinsip yang harus kita pertahankan sejak sekarang adalah:

```text
SOURCE
   ↓
EXTRACTION
   ↓
MATCHING
   ↓
HUMAN VERIFICATION
   ↓
KNOWLEDGE GRAPH
   ↓
RAG
   ↓
AI ANSWER
   ↓
CITATION
   ↓
SOURCE PAGE
```

Dengan rantai ini, jawaban AI dapat ditelusuri kembali sampai **halaman sumber Fathul Bari**, bukan berhenti pada output model.
