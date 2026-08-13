# Stage 22 — RAG Evidence Engine

Stage 22 adalah tahap ketika **Hadis + Fathul Bari + Knowledge Graph + Source Viewer** mulai disatukan menjadi mesin pencarian evidence untuk Syarah AI.

Prinsip utamanya:

> **LLM tidak mencari kebenaran sendiri. LLM hanya menyusun jawaban berdasarkan evidence yang berhasil diambil sistem.**

Arsitektur:

```text
User Question
     │
     ▼
Query Analyzer
     │
     ├──────────────┐
     ▼              ▼
Hadith Search   Fathul Bari Search
     │              │
     └──────┬───────┘
            ▼
      Candidate Fusion
            │
            ▼
        Reranker
            │
            ▼
      Evidence Pack
            │
            ▼
      Answer Generator
            │
            ▼
    Citation Validator
            │
      ┌─────┴─────┐
      ▼           ▼
   Answer       Audit Log
```

---

# 22.1 Target Stage 22

Kita ingin pertanyaan seperti:

> **"Apa penjelasan Ibnu Hajar tentang niat dalam hadis إنما الأعمال بالنيات?"**

menghasilkan:

```text
Hadis:
Sahih al-Bukhari #1

Fathul Bari:
Vol. 1, p. XX

Evidence:
قوله إنما الأعمال بالنيات...

Jawaban:
...

Sources:
[1] Bukhari #1
[2] Fathul Bari Vol. 1 p. XX
```

dan setiap citation dapat dibuka ke Source Viewer.

---

# 22.2 Prinsip Evidence-First

Jangan:

```text
Question
   ↓
LLM
   ↓
Answer
```

Gunakan:

```text
Question
   ↓
Retrieval
   ↓
Evidence
   ↓
LLM
   ↓
Citation
```

Lebih ketat lagi:

```text
Question
 ↓
Evidence
 ↓
Draft Answer
 ↓
Citation Validation
 ↓
Final Answer
```

---

# 22.3 Query Classification

Pertanyaan user perlu diklasifikasikan.

```text
FACTUAL
HADITH_LOOKUP
SHARH
COMPARATIVE
FIQH
THEMATIC
SOURCE_LOOKUP
CHAIN_OF_NARRATION
GENERAL_ISLAMIC
```

Contoh:

### Hadis

> "Sebutkan hadis Bukhari tentang niat."

```json
{
  "type": "HADITH_LOOKUP"
}
```

### Syarah

> "Apa penjelasan Ibnu Hajar tentang niat?"

```json
{
  "type": "SHARH"
}
```

### Perbandingan

> "Bagaimana Ibnu Hajar menjelaskan perbedaan riwayat hadis ini?"

```json
{
  "type": "COMPARATIVE"
}
```

---

# 22.4 Query Object

Buat:

```text
app/rag/query.py
```

```python
from pydantic import BaseModel
from typing import Optional


class RAGQuery(BaseModel):
    question: str
    language: str = "id"

    collection: Optional[str] = None
    hadith_number: Optional[str] = None

    include_hadith: bool = True
    include_sharh: bool = True
    include_related: bool = True

    max_evidence: int = 12
```

---

# 22.5 Query Analyzer

Struktur:

```text
app/rag/query_analyzer.py
```

Output:

```json
{
  "intent": "SHARH",
  "entities": {
    "hadith_collection": "bukhari",
    "hadith_number": "1",
    "topic": "niat"
  },
  "keywords": [
    "إنما الأعمال بالنيات",
    "النية",
    "الأعمال"
  ]
}
```

---

# 22.6 Jangan Terlalu Bergantung pada LLM

Query Analyzer dapat menggunakan kombinasi:

```text
Rule-based
+
Dictionary
+
Database lookup
+
LLM fallback
```

Contoh:

```text
"Bukhari 1"
```

tidak perlu LLM.

Parser langsung mengenali:

```text
collection = bukhari
number = 1
```

---

# 22.7 Query Expansion

Pertanyaan Bahasa Indonesia:

> "Apa maksud niat menurut Ibnu Hajar?"

dapat diperluas:

```text
niat
النية
نية
الأعمال بالنيات
إنما الأعمال بالنيات
قوله إنما الأعمال بالنيات
```

Tetapi query expansion harus dibatasi agar tidak menghasilkan noise.

---

# 22.8 Retrieval Layer

Buat:

```text
app/rag/retriever.py
```

Interface:

```python
class Retriever:

    async def search_hadith(
        self,
        query: str,
        limit: int = 10
    ):
        ...

    async def search_sharh(
        self,
        query: str,
        limit: int = 20
    ):
        ...

    async def search_related(
        self,
        query: str,
        limit: int = 10
    ):
        ...
```

---

# 22.9 Hadith Retrieval

Hadis dapat dicari berdasarkan:

```text
exact number
collection
Arabic text
Indonesian translation
narrator
topic
embedding
```

Urutan prioritas:

```text
Exact reference
      ↓
Exact phrase
      ↓
Lexical
      ↓
Semantic
```

---

# 22.10 Fathul Bari Retrieval

Gunakan hybrid search:

```text
                    Query
                      │
              ┌───────┴───────┐
              ▼               ▼
          BM25/FTS         Vector
              │               │
              └───────┬───────┘
                      ▼
                  Candidate
                      │
                      ▼
                   Rerank
```

---

# 22.11 Evidence Candidate

Format internal:

```python
class EvidenceCandidate(BaseModel):
    id: str
    source_type: str

    document_id: str | None = None
    volume: int | None = None
    page: int | None = None

    text: str

    lexical_score: float = 0
    semantic_score: float = 0
    reference_score: float = 0

    retrieval_score: float = 0
```

---

# 22.12 Candidate Fusion

Misalnya:

```text
Lexical top 20
Semantic top 20
Reference top 10
Knowledge Graph top 10
```

Digabung:

```text
60 candidates
   ↓
deduplicate
   ↓
42 candidates
```

kemudian reranking.

---

# 22.13 Deduplication

Jangan menampilkan:

```text
Chunk A
Chunk A duplicate
Chunk A OCR copy
Chunk A normalized copy
```

Gunakan:

```text
content_hash
```

sebagai salah satu kunci deduplication.

---

# 22.14 Reranker

Retriever mencari kandidat.

Reranker menentukan kandidat terbaik.

```text
Retriever:
"Apakah ini mungkin relevan?"

Reranker:
"Mana yang paling relevan?"
```

Pipeline:

```text
100 chunks
    ↓
retrieval
    ↓
30 chunks
    ↓
reranker
    ↓
10 evidence
```

---

# 22.15 Reranking Features

Gunakan:

```text
semantic relevance
lexical relevance
hadith reference
section relevance
page proximity
query intent
verified match
source quality
```

Contoh:

```python
score = (
    0.30 * semantic +
    0.20 * lexical +
    0.20 * reference +
    0.10 * section +
    0.10 * verified_match +
    0.10 * source_quality
)
```

Bobot ini adalah **starting point**, bukan angka final.

---

# 22.16 Source Quality

Tidak semua evidence mempunyai status sama.

Misalnya:

```text
VERIFIED SOURCE
    1.00

OCR REVIEWED
    0.95

OCR UNVERIFIED
    0.75

SYSTEM GENERATED
    0.50
```

Untuk Fathul Bari, sumber primer yang telah diverifikasi harus mendapatkan prioritas.

---

# 22.17 Evidence Pack

Setelah retrieval:

```text
Evidence Pack
```

Contoh:

```json
{
  "query": "...",
  "hadiths": [
    {
      "id": "...",
      "collection": "bukhari",
      "number": "1"
    }
  ],
  "sharh": [
    {
      "chunk_id": "...",
      "volume": 1,
      "page": 45,
      "text": "قوله إنما الأعمال بالنيات..."
    }
  ]
}
```

---

# 22.18 Evidence Budget

Jangan mengirim 100 chunk ke LLM.

Misalnya:

```text
Maximum:
8–12 evidence chunks
```

Contoh:

```text
2 Hadith
+
6 Fathul Bari
+
2 Related
=
10 evidence
```

---

# 22.19 Context Builder

Buat:

```text
app/rag/context_builder.py
```

```python
def build_context(evidence_pack):

    sections = []

    for item in evidence_pack.hadiths:
        sections.append(
            format_hadith(item)
        )

    for item in evidence_pack.sharh:
        sections.append(
            format_sharh(item)
        )

    return "\n\n".join(sections)
```

---

# 22.20 Context Format

LLM menerima:

```text
[SOURCE H1]
Sahih al-Bukhari #1

TEXT:
إنما الأعمال بالنيات...

[/SOURCE H1]


[SOURCE FB1]
Fathul Bari
Vol. 1
p. 45
Chunk: FB-V1-P45-C003

TEXT:
قوله إنما الأعمال بالنيات...

[/SOURCE FB1]
```

Dengan demikian citation dapat dipetakan kembali.

---

# 22.21 Strict System Prompt

AI Assistant harus memiliki aturan:

```text
Anda adalah asisten penelitian hadis.

ATURAN:

1. Gunakan hanya evidence yang diberikan.
2. Jangan mengarang kutipan.
3. Jangan membuat nomor halaman.
4. Jangan membuat nomor hadis.
5. Jika evidence tidak cukup, katakan tidak cukup.
6. Bedakan teks hadis dari syarah.
7. Bedakan penjelasan Ibnu Hajar dari kesimpulan Anda.
8. Setiap klaim faktual harus mempunyai citation.
9. Jangan menyatakan confidence sebagai kebenaran.
10. Jangan mengubah teks Arab sumber.
```

---

# 22.22 Evidence Attribution

Jawaban internal:

```json
{
  "claim": "Ibnu Hajar menjelaskan bahwa niat berkaitan dengan maksud perbuatan.",
  "evidence": [
    "FB-V1-P45-C003"
  ]
}
```

Ini sangat penting.

Bukan hanya:

```text
Answer → citations
```

tetapi:

```text
Claim → Evidence
```

---

# 22.23 Claim Extraction

Setelah LLM menghasilkan draft:

```text
Draft Answer
      ↓
Claim Extractor
      ↓
Claims
```

Misalnya:

```json
[
  {
    "claim": "Niat menjadi pembeda nilai suatu amal.",
    "citation": "FB-V1-P45-C003"
  },
  {
    "claim": "Hadis ini merupakan hadis pertama dalam Sahih Bukhari.",
    "citation": "H-BUKHARI-1"
  }
]
```

---

# 22.24 Citation Validator

Buat:

```text
app/rag/citation_validator.py
```

Tugas:

```text
Claim
 ↓
Citation ID
 ↓
Evidence exists?
 ↓
Does evidence actually support claim?
```

Status:

```text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
MISSING
```

---

# 22.25 Guard Against Hallucination

Jika:

```text
Claim:
Ibnu Hajar berkata X.

Citation:
FB-V1-P45-C003
```

tetapi chunk tidak memuat atau mendukung X:

```text
UNSUPPORTED
```

Maka jawaban tidak boleh langsung dikirim.

---

# 22.26 Answer Gate

```text
                    Draft Answer
                         │
                         ▼
                 Citation Validator
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       All supported             Unsupported
             │                       │
             ▼                       ▼
          SEND                 Regenerate /
                               Remove claim
```

---

# 22.27 Regeneration Loop

Maksimal:

```text
2 attempts
```

Jangan:

```text
infinite regeneration
```

Flow:

```text
Draft 1
 ↓
Validation
 ↓
failed
 ↓
Draft 2
 ↓
Validation
 ↓
failed
 ↓
"Evidence tidak mencukupi"
```

---

# 22.28 Answer Structure

Untuk pertanyaan syarah, format default:

```text
### Hadis

...

### Penjelasan Ibnu Hajar

...

### Inti Syarah

...

### Kesimpulan

...

### Sumber

[1] Sahih al-Bukhari #1
[2] Fathul Bari, Vol. 1, p. 45
```

Tetapi bagian-bagian ini harus menyesuaikan pertanyaan user.

---

# 22.29 Distinguish Source vs Interpretation

Gunakan label:

```text
[TEKS HADIS]
[SYARAH IBNU HAJAR]
[ANALISIS]
```

Contoh:

```text
### Syarah Ibnu Hajar
...

### Analisis
Berdasarkan penjelasan tersebut, dapat dipahami bahwa...
```

Dengan demikian user tidak mengira analisis AI sebagai perkataan Ibnu Hajar.

---

# 22.30 RAG API

Endpoint utama:

```http
POST /api/v1/rag/query
```

Request:

```json
{
  "question": "Apa penjelasan Ibnu Hajar tentang niat?",
  "language": "id",
  "max_evidence": 10
}
```

---

# 22.31 Response

```json
{
  "answer": "...",

  "query": {
    "intent": "SHARH"
  },

  "citations": [
    {
      "id": "FB-V1-P45-C003",
      "source_type": "FATH_AL_BARI",
      "volume": 1,
      "page": 45,
      "chunk_id": "..."
    }
  ],

  "evidence": [
    {
      "id": "FB-V1-P45-C003",
      "score": 0.94
    }
  ],

  "validation": {
    "status": "SUPPORTED"
  }
}
```

---

# 22.32 Streaming Response

Untuk UX yang baik:

```text
POST /api/v1/rag/query
```

bisa menggunakan streaming.

Tetapi ada masalah:

> Jangan streaming jawaban final sebelum citation validation selesai.

Lebih aman:

```text
Retrieval
 ↓
Generate
 ↓
Validate
 ↓
Stream validated answer
```

Bukan:

```text
LLM mulai bicara
 ↓
kemudian baru dicek
```

---

# 22.33 RAG Audit Log

Tambahkan:

```sql
CREATE TABLE rag_queries (
    id UUID PRIMARY KEY,

    user_id UUID,

    question TEXT NOT NULL,

    query_analysis JSONB,

    retrieval_config JSONB,

    evidence_ids JSONB,

    answer TEXT,

    validation_result JSONB,

    model_name TEXT,
    model_version TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Ini menjadi rekaman penelitian.

---

# 22.34 Evidence Snapshot

Jangan hanya menyimpan:

```text
chunk_id
```

Simpan juga:

```text
chunk_id
content_hash
retrieval_score
rank
```

Contoh:

```json
{
  "chunk_id": "...",
  "content_hash": "a7f...",
  "rank": 2,
  "score": 0.94
}
```

Karena corpus mungkin berubah di masa depan.

---

# 22.35 Reproducibility

Satu query harus bisa direproduksi.

Simpan:

```text
query
query analyzer version
retriever version
reranker version
embedding model
LLM model
temperature
top_k
evidence IDs
prompt version
```

Dengan ini:

```text
Query tanggal 13 Agustus 2026
```

dapat dibandingkan dengan:

```text
Query tanggal 20 September 2026
```

---

# 22.36 Prompt Versioning

Buat:

```text
prompts/
├── rag_answer_v1.txt
├── rag_answer_v2.txt
└── citation_validator_v1.txt
```

Simpan:

```json
{
  "prompt_version": "rag_answer_v1"
}
```

---

# 22.37 Retrieval Configuration

Simpan:

```json
{
  "lexical_top_k": 30,
  "semantic_top_k": 30,
  "reference_top_k": 10,
  "rerank_top_k": 10
}
```

Ini membuat eksperimen dapat diulang.

---

# 22.38 Knowledge Graph Integration

Stage 22 juga menggunakan Knowledge Graph.

Misalnya:

```text
Hadith #1
   │
   ├── EXPLAINED_BY
   │       ↓
   │   FB-V1-P45-C003
   │
   ├── RELATED_TO
   │       ↓
   │   Hadith #2
   │
   └── TOPIC
           ↓
         NIYYAH
```

Jika user bertanya:

> "Hadis apa saja yang berkaitan dengan niat?"

Graph retrieval membantu memperluas kandidat.

---

# 22.39 Graph Retrieval

```text
Question
   ↓
Entity Detection
   ↓
Graph Lookup
   ↓
Related Hadith
   ↓
Related Fathul Bari
   ↓
Evidence Fusion
```

Jangan membuat graph menggantikan vector search.

Gunakan:

```text
Vector
+
Lexical
+
Graph
+
Reference
```

---

# 22.40 Evidence Ranking Final

Formula awal:

```text
Final Evidence Score
=
0.25 Semantic
+
0.20 Lexical
+
0.20 Reference
+
0.15 Verified Match
+
0.10 Graph Relevance
+
0.10 Source Quality
```

Nantinya bobot dioptimalkan berdasarkan golden dataset.

---

# 22.41 Source Hierarchy

Prioritas:

```text
1. Verified Fathul Bari page
2. Verified Hadith source
3. Reviewed OCR
4. Unreviewed OCR
5. Derived metadata
6. AI-generated content
```

AI-generated content **tidak boleh menjadi evidence primer**.

---

# 22.42 Fallback

Jika evidence tidak ditemukan:

```text
Saya belum menemukan evidence yang cukup dalam corpus
Fathul Bari yang tersedia untuk menjawab pertanyaan ini
dengan tingkat kepastian yang memadai.
```

Bukan:

```text
Ibnu Hajar mengatakan...
```

berdasarkan pengetahuan umum LLM.

---

# 22.43 Confidence

Bedakan tiga confidence:

```text
Retrieval Confidence
```

Seberapa yakin sistem menemukan evidence relevan.

```text
Citation Confidence
```

Seberapa kuat evidence mendukung claim.

```text
Answer Confidence
```

Seberapa lengkap evidence untuk menjawab keseluruhan pertanyaan.

Jangan mencampur ketiganya menjadi satu angka.

---

# 22.44 RAG Dashboard

Tambahkan halaman:

```text
/rag/inspect/{query_id}
```

UI:

```text
┌──────────────────────────────────────────────┐
│ RAG INSPECTOR                                │
├──────────────────────────────────────────────┤
│ Question                                     │
│ Apa penjelasan Ibnu Hajar tentang niat?      │
├──────────────────────────────────────────────┤
│ QUERY ANALYSIS                               │
│ Intent: SHARH                                │
│ Entity: Niyyah                               │
├──────────────────────────────────────────────┤
│ RETRIEVAL                                    │
│                                             │
│ Lexical: 30                                  │
│ Semantic: 30                                 │
│ Graph: 10                                    │
│                                             │
├──────────────────────────────────────────────┤
│ TOP EVIDENCE                                 │
│                                             │
│ #1 FB-V1-P45-C003   0.94                    │
│ #2 FB-V1-P46-C001   0.91                    │
│ #3 FB-V1-P44-C007   0.87                    │
├──────────────────────────────────────────────┤
│ VALIDATION                                   │
│                                             │
│ Claim #1 ✓ SUPPORTED                         │
│ Claim #2 ✓ SUPPORTED                         │
│ Claim #3 ⚠ PARTIAL                           │
└──────────────────────────────────────────────┘
```

---

# 22.45 User-Facing Syarah Assistant

UI utama:

```text
┌──────────────────────────────────────────────┐
│ ALMAKTABA · SYARAH ASSISTANT                 │
├──────────────────────────────────────────────┤
│                                              │
│ Tanya tentang hadis atau Fathul Bari...      │
│                                              │
│ [ Apa penjelasan Ibnu Hajar tentang niat? ] │
│                                              │
├──────────────────────────────────────────────┤
│ ANSWER                                       │
│                                              │
│ ...                                          │
│                                              │
│ [1] [2]                                      │
│                                              │
├──────────────────────────────────────────────┤
│ SOURCES                                      │
│                                              │
│ [1] Sahih al-Bukhari #1                      │
│ [2] Fathul Bari · Vol. 1 · p.45              │
│     [Open Source]                            │
└──────────────────────────────────────────────┘
```

---

# 22.46 Citation Click Flow

Ketika user klik:

```text
[2]
```

maka:

```text
Citation
   ↓
chunk_id
   ↓
page_id
   ↓
Source Viewer
   ↓
highlight evidence
```

Jadi user tidak perlu mencari halaman secara manual.

---

# 22.47 Audit Trail

Setiap query:

```text
User
 ↓
Question
 ↓
Query analysis
 ↓
Retrieved candidates
 ↓
Selected evidence
 ↓
Prompt
 ↓
LLM output
 ↓
Citation validation
 ↓
Final answer
```

disimpan.

Ini membuat sistem cocok untuk **riset**, bukan sekadar chatbot.

---

# 22.48 Database Tambahan

Stage 22 membutuhkan:

```sql
CREATE TABLE rag_evidence (
    id UUID PRIMARY KEY,

    rag_query_id UUID NOT NULL
        REFERENCES rag_queries(id),

    source_type VARCHAR(50) NOT NULL,

    source_id UUID,

    rank INTEGER NOT NULL,

    retrieval_score NUMERIC(8,6),

    lexical_score NUMERIC(8,6),
    semantic_score NUMERIC(8,6),
    graph_score NUMERIC(8,6),

    content_hash VARCHAR(64),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Dan:

```sql
CREATE TABLE rag_claims (
    id UUID PRIMARY KEY,

    rag_query_id UUID NOT NULL
        REFERENCES rag_queries(id),

    claim_text TEXT NOT NULL,

    validation_status VARCHAR(40),

    confidence NUMERIC(8,6),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 22.49 Claim-Evidence Relation

```sql
CREATE TABLE rag_claim_evidence (
    claim_id UUID NOT NULL
        REFERENCES rag_claims(id),

    evidence_id UUID NOT NULL
        REFERENCES rag_evidence(id),

    support_type VARCHAR(30),

    support_score NUMERIC(8,6),

    PRIMARY KEY(claim_id, evidence_id)
);
```

Sekarang graph-nya:

```text
RAG Query
   │
   ├── Claim
   │      │
   │      └── Evidence
   │             │
   │             └── Fathul Bari Page
   │
   └── Answer
```

---

# 22.50 Ini Mengubah Arsitektur Kita

Sebelumnya:

```text
Hadith → Syarah → AI
```

Sekarang:

```text
                       ┌── Hadith API
                       │
User → Query Analyzer ─┼── Fathul Bari
                       │
                       └── Knowledge Graph
                              │
                              ▼
                         Evidence Layer
                              │
                              ▼
                           Reranker
                              │
                              ▼
                        Answer Generator
                              │
                              ▼
                      Citation Validator
                              │
                       ┌──────┴──────┐
                       ▼             ▼
                    Answer         Audit
```

---

# 22.51 Definition of Done

Stage 22 dianggap selesai jika:

```text
[ ] Query analyzer
[ ] Query classification
[ ] Query expansion
[ ] Hadith retriever
[ ] Fathul Bari retriever
[ ] Hybrid retrieval
[ ] Graph retrieval
[ ] Candidate fusion
[ ] Deduplication
[ ] Reranker
[ ] Evidence pack
[ ] Context builder
[ ] Answer generator
[ ] Claim extraction
[ ] Citation validator
[ ] Regeneration guard
[ ] Evidence confidence
[ ] RAG audit log
[ ] Query reproducibility
[ ] RAG Inspector
[ ] Citation → Source Viewer
```

---

# 22.52 Test Case Utama

Gunakan pertanyaan benchmark:

```text
1. Apa hadis tentang niat?

2. Apa penjelasan Ibnu Hajar tentang hadis niat?

3. Mengapa Imam Bukhari membuka kitabnya dengan hadis niat?

4. Apa hubungan niat dengan amal menurut Fathul Bari?

5. Tunjukkan sumber halaman yang membahas hadis tersebut.

6. Bandingkan penjelasan Ibnu Hajar terhadap dua riwayat terkait.

7. Apakah hadis ini memiliki riwayat lain?

8. Apa saja istilah penting yang digunakan Ibnu Hajar?
```

Setiap jawaban harus menghasilkan:

```text
Answer
+
Evidence
+
Citation
+
Validation
```

---

# 22.53 Target Akhir Stage 22

Pada titik ini aplikasi kita sudah mempunyai **closed-loop evidence system**:

```text
                    USER
                     │
                     ▼
                  QUERY
                     │
                     ▼
              ┌─────────────┐
              │   RETRIEVE  │
              └──────┬──────┘
                     │
                     ▼
                 EVIDENCE
                     │
                     ▼
                 RERANK
                     │
                     ▼
                 LLM DRAFT
                     │
                     ▼
              CLAIM EXTRACTION
                     │
                     ▼
             CITATION VALIDATOR
                     │
              ┌──────┴──────┐
              ▼             ▼
           SUPPORTED      FAILED
              │             │
              ▼             ▼
            ANSWER      REGENERATE
              │
              ▼
          AUDIT TRAIL
```

**Inilah fondasi utama Syarah AI Assistant yang aman untuk penelitian.**

---
