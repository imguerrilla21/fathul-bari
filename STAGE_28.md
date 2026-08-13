# Stage 28 — Natural Language Hadith Research Engine

Stage 28 adalah lapisan yang mengubah aplikasi dari **"mesin pencari hadis + RAG"** menjadi **asisten riset hadis**.

Target utamanya:

> Pengguna bertanya dalam Bahasa Indonesia secara natural, sistem memahami maksud pertanyaan, menemukan hadis yang relevan, menelusuri variasi matan dan sanad, mengambil syarah *Fathul Bari*, menyusun evidence, lalu memberikan jawaban dengan peta sitasi yang dapat diaudit.

---

# 28.1 Tujuan Utama

Contoh pertanyaan:

> **"Apa penjelasan Ibn Hajar tentang hadis niat, siapa saja perawinya, dan apakah ada perbedaan lafaz dalam riwayat lain?"**

Stage 28 mengubahnya menjadi:

```text
User Question
      │
      ▼
Intent Detection
      │
      ▼
Research Plan
      │
      ├── Identify Hadith
      ├── Search Arabic
      ├── Find Variants
      ├── Traverse Isnad
      ├── Retrieve Fathul Bari
      ├── Compare Sources
      └── Build Evidence
              │
              ▼
        Evidence Graph
              │
              ▼
          LLM Answer
              │
              ▼
       Citation Mapping
```

---

# 28.2 Prinsip Fundamental

Ada 5 aturan utama.

### 1. LLM bukan sumber

```text
LLM
  ↓
interpretation
```

sedangkan:

```text
Hadith
Fathul Bari
Source
  ↓
evidence
```

---

### 2. Retrieval sebelum generation

```text
Question
 ↓
Retrieve
 ↓
Verify
 ↓
Generate
```

bukan:

```text
Question
 ↓
LLM improvisation
```

---

### 3. Setiap klaim penting harus punya evidence

```text
Claim
 ↓
Evidence
 ↓
Source
 ↓
Page / Hadith / Chunk
```

---

### 4. Pisahkan fakta dan inferensi

Misalnya:

```text
SOURCE_FACT
```

vs:

```text
AI_INFERENCE
```

---

### 5. Ketidakpastian harus terlihat

Jika sistem tidak yakin:

```text
confidence = 0.61
```

maka UI tidak boleh menampilkan:

> "Ibn Hajar pasti mengatakan..."

tetapi:

> "Sumber yang ditemukan menunjukkan..."

---

# 28.3 Research Intent

Buat taxonomy intent.

```text
HADITH_LOOKUP
HADITH_EXPLANATION
SHARH_LOOKUP
NARRATOR_LOOKUP
ISNAD_ANALYSIS
MATN_COMPARISON
VARIANT_SEARCH
SOURCE_COMPARISON
GRADING_LOOKUP
FIQH_EXPLANATION
LINGUISTIC_ANALYSIS
THEMATIC_RESEARCH
CROSS_REFERENCE
```

---

# 28.4 Contoh Intent Detection

Pertanyaan:

> "Siapa perawi hadis ini?"

```json
{
  "intent": "NARRATOR_LOOKUP"
}
```

Pertanyaan:

> "Apa kata Ibn Hajar tentang kata النية?"

```json
{
  "intent": "SHARH_LOOKUP",
  "focus": "LINGUISTIC_ANALYSIS"
}
```

Pertanyaan:

> "Bandingkan hadis ini dengan riwayat Muslim."

```json
{
  "intent": "MATN_COMPARISON"
}
```

---

# 28.5 Research Query Model

```python
class ResearchQuery:
    original_query: str
    language: str
    intent: str

    entities: list
    hadith_candidates: list

    concepts: list
    arabic_terms: list

    source_constraints: list
    scholar_constraints: list

    requested_outputs: list
```

---

# 28.6 Contoh Research Query

Input:

```text
Apa penjelasan Ibn Hajar tentang niat?
```

Output:

```json
{
  "original_query": "Apa penjelasan Ibn Hajar tentang niat?",
  "language": "id",
  "intent": "SHARH_LOOKUP",
  "entities": [
    {
      "type": "SCHOLAR",
      "value": "Ibn Hajar"
    }
  ],
  "concepts": [
    "niat"
  ],
  "arabic_terms": [
    "النية",
    "النيات",
    "نية"
  ],
  "source_constraints": [
    "Fathul Bari"
  ]
}
```

---

# 28.7 Query Planner

Setelah intent diketahui, jangan langsung memanggil LLM.

Buat:

```text
Research Plan
```

Contoh:

```json
{
  "steps": [
    "IDENTIFY_HADITH",
    "SEARCH_ARABIC_TERMS",
    "RETRIEVE_FATHUL_BARI",
    "BUILD_EVIDENCE",
    "GENERATE_ANSWER"
  ]
}
```

---

# 28.8 Research Plan Types

### Simple Lookup

```text
Question
 ↓
Search
 ↓
Answer
```

### Hadith Explanation

```text
Question
 ↓
Identify Hadith
 ↓
Fathul Bari
 ↓
Evidence
 ↓
Answer
```

### Isnad Research

```text
Question
 ↓
Identify Hadith
 ↓
Extract Isnad
 ↓
Traverse Graph
 ↓
Narrator Evidence
 ↓
Answer
```

### Comparative Research

```text
Question
 ↓
Identify Hadith
 ↓
Find Variants
 ↓
Normalize
 ↓
Diff
 ↓
Compare
 ↓
Answer
```

---

# 28.9 Research Planner Architecture

```text
                QUERY
                  │
                  ▼
             Intent Parser
                  │
                  ▼
            Research Planner
                  │
       ┌──────────┼───────────┐
       ▼          ▼           ▼
    Hadith      Source      Graph
    Search      Search      Search
       │          │           │
       └──────────┼───────────┘
                  ▼
              Evidence
                  │
                  ▼
               Answer
```

---

# 28.10 Research Agent Bukan Autonomous Agent Penuh

Untuk aplikasi ilmiah, hindari agent yang bebas melakukan apa saja.

Gunakan:

```text
Controlled Research Workflow
```

dengan tool yang eksplisit:

```text
search_hadith
get_hadith
search_commentary
get_source_chunk
get_isnad
get_variants
compare_variants
search_narrator
get_citation
```

---

# 28.11 Tool Registry

```python
TOOLS = {
    "search_hadith": search_hadith,
    "get_hadith": get_hadith,
    "search_commentary": search_commentary,
    "get_source_chunk": get_source_chunk,
    "get_isnad": get_isnad,
    "get_variants": get_variants,
    "compare_variants": compare_variants,
    "search_narrator": search_narrator,
    "get_citation": get_citation
}
```

LLM hanya boleh memanggil tool yang terdaftar.

---

# 28.12 Tool Call Audit

Setiap tool call dicatat:

```json
{
  "tool": "search_commentary",
  "arguments": {
    "query": "النية"
  },
  "timestamp": "...",
  "result_count": 14
}
```

Ini masuk Audit Trail Stage 6.

---

# 28.13 Query Translation Layer

Pengguna Indonesia:

```text
"hadis tentang niat"
```

menjadi:

```text
النية
النيات
نية
نوى
الأعمال بالنيات
```

Namun expansion harus diberi sumber:

```text
TERM_EXPANSION
```

---

# 28.14 Bidirectional Search

Sistem mendukung:

```text
Indonesia
 ↓
Arabic
 ↓
Hadith
```

dan:

```text
Arabic
 ↓
Concept
 ↓
Indonesia
```

Contoh:

```text
"kesombongan"
```

→

```text
الكبر
التكبر
```

---

# 28.15 Query Expansion Sources

Expansion dapat berasal dari:

```text
Arabic Lexicon
Hadith Corpus
Knowledge Graph
Previous verified queries
Embedding model
```

Tetapi setiap expansion disimpan.

```json
{
  "term": "kesombongan",
  "expanded_to": "الكبر",
  "method": "LEXICON"
}
```

---

# 28.16 Evidence Retrieval

Buat struktur:

```python
class Evidence:
    id: str

    source_id: str
    document_id: str
    chunk_id: str

    text: str

    evidence_type: str

    score: float
    confidence: float

    metadata: dict
```

---

# 28.17 Evidence Types

```text
PRIMARY_HADITH
PRIMARY_COMMENTARY
SECONDARY_COMMENTARY
NARRATOR_RECORD
ISNAD_RELATION
HADITH_VARIANT
BIBLIOGRAPHIC_REFERENCE
AI_INFERENCE
```

---

# 28.18 Evidence Ranking

Ranking:

```text
Primary Fathul Bari
       ↓
Primary Hadith
       ↓
Verified scholarly source
       ↓
Secondary source
       ↓
Semantic relation
       ↓
AI inference
```

Untuk pertanyaan tertentu urutannya dapat berubah.

---

# 28.19 Evidence Pack

Sebelum LLM menghasilkan jawaban, buat:

```json
{
  "question": "...",
  "intent": "SHARH_LOOKUP",

  "evidence": [
    {
      "id": "ev_001",
      "type": "PRIMARY_COMMENTARY",
      "source": "Fathul Bari",
      "chunk": "FB-P45-C3"
    },
    {
      "id": "ev_002",
      "type": "PRIMARY_HADITH",
      "source": "Sahih al-Bukhari",
      "reference": "..."
    }
  ]
}
```

---

# 28.20 Evidence Budget

Jangan mengirim 100 chunk ke LLM.

Gunakan:

```text
Top 5–15 evidence
```

sesuai kompleksitas.

Contoh:

```text
Simple:
5

Medium:
10

Research:
15–30
```

Tetap dibatasi context window model yang digunakan.

---

# 28.21 Evidence Diversity

Jangan semua evidence berasal dari satu chunk.

Ranking harus mempertimbangkan:

```text
relevance
+
source diversity
+
coverage
```

Contoh:

```text
Fathul Bari chunk 1
Fathul Bari chunk 2
Hadith source
Variant source
Narrator source
```

lebih berguna daripada:

```text
Fathul Bari chunk 1
Fathul Bari chunk 1
Fathul Bari chunk 1
...
```

---

# 28.22 Claim Extraction

Sebelum final answer, LLM diminta menghasilkan:

```json
{
  "claims": [
    {
      "claim": "...",
      "evidence_ids": ["ev_001"]
    }
  ]
}
```

Kemudian citation engine memeriksa.

---

# 28.23 Claim-Evidence Matrix

```text
┌──────────────────────────────┬──────────┐
│ Claim                        │ Evidence │
├──────────────────────────────┼──────────┤
│ Ibn Hajar menjelaskan X      │ EV001    │
│ Hadis diriwayatkan melalui Y │ EV002    │
│ Riwayat lain memiliki Z      │ EV003   │
└──────────────────────────────┴──────────┘
```

---

# 28.24 Unsupported Claim Detector

Jika AI menghasilkan:

```text
"Ibn Hajar berpendapat X."
```

tetapi tidak ada evidence:

```text
CLAIM_UNSUPPORTED
```

Sistem:

```text
REJECT
```

atau:

```text
REGENERATE
```

---

# 28.25 Citation Coverage

Hitung:

```text
Citation Coverage =
supported claims / total factual claims
```

Target internal:

```text
≥ 95%
```

untuk factual claims yang membutuhkan sumber.

Ini adalah target engineering, bukan jaminan otomatis.

---

# 28.26 Citation Types

```text
HADITH_CITATION
COMMENTARY_CITATION
PAGE_CITATION
BOOK_CITATION
ENTITY_CITATION
GRAPH_CITATION
```

---

# 28.27 Citation Object

```json
{
  "id": "cit_001",

  "claim_id": "claim_001",

  "source_id": "source_fb",

  "document_id": "fb",

  "page": 45,

  "chunk_id": "FB-P45-C03",

  "locator": "page 45",

  "confidence": 0.97
}
```

---

# 28.28 Citation Map

Jawaban:

```text
Menurut Ibn Hajar, niat memiliki...
                     [1]

Hadis tersebut diriwayatkan melalui...
                     [2]

Dalam riwayat lain...
                     [3]
```

Panel:

```text
[1] Fathul Bari, vol..., p...
[2] Sahih al-Bukhari...
[3] Riwayat ...
```

---

# 28.29 Click-to-Evidence

User klik `[1]`.

Source Viewer langsung:

```text
Fathul Bari
Page 45

... متن المصدر ...

████████████████
relevant passage
████████████████
```

---

# 28.30 Research Workspace

Buat UI:

```text
/research
```

Layout:

```text
┌────────────────────────────────────────────────────────┐
│ RESEARCH ASSISTANT                                    │
├──────────────────────┬─────────────────────────────────┤
│                      │                                 │
│ QUERY                │ EVIDENCE                        │
│                      │                                 │
│ Apa penjelasan...    │ [1] Fathul Bari                 │
│                      │ [2] Bukhari                     │
│ [Research]           │ [3] Variant                     │
│                      │                                 │
├──────────────────────┴─────────────────────────────────┤
│ ANSWER                                                 │
│                                                        │
│ ...                                                    │
│                                                        │
│ [1] [2] [3]                                            │
└────────────────────────────────────────────────────────┘
```

---

# 28.31 Research Modes

Tambahkan mode:

```text
QUICK
STANDARD
DEEP RESEARCH
```

### Quick

```text
1–5 sources
```

### Standard

```text
5–15 sources
```

### Deep Research

```text
15–50+ evidence
cross-reference
isnad
variants
Fathul Bari
```

Jumlah sebenarnya harus mengikuti query dan context budget.

---

# 28.32 Deep Research Workflow

```text
Question
 ↓
Intent
 ↓
Hadith identification
 ↓
Source discovery
 ↓
Variant discovery
 ↓
Isnad traversal
 ↓
Commentary retrieval
 ↓
Cross-reference
 ↓
Evidence consolidation
 ↓
Claim extraction
 ↓
Citation validation
 ↓
Answer
```

---

# 28.33 Research Session

Simpan setiap penelitian:

```sql
CREATE TABLE research_sessions (
    id UUID PRIMARY KEY,

    user_id UUID,

    title TEXT,

    original_question TEXT,

    intent VARCHAR(50),

    status VARCHAR(30),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    completed_at TIMESTAMPTZ
);
```

---

# 28.34 Research Steps

```sql
CREATE TABLE research_steps (
    id UUID PRIMARY KEY,

    session_id UUID NOT NULL,

    step_order INTEGER,

    step_type VARCHAR(50),

    input JSONB,

    output JSONB,

    status VARCHAR(30),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 28.35 Research Session Example

```text
Session #R-001

Step 1
Intent Detection

Step 2
Hadith Identification

Step 3
Fathul Bari Retrieval

Step 4
Variant Search

Step 5
Isnad Analysis

Step 6
Evidence Ranking

Step 7
Answer Generation

Step 8
Citation Validation
```

---

# 28.36 Research Reproducibility

Simpan:

```text
query
intent
plan
tools
arguments
source versions
NLP version
embedding version
LLM model
prompt version
evidence
answer
citations
```

Dengan demikian penelitian dapat diulang.

---

# 28.37 Prompt Versioning

Jangan menyimpan hanya:

```text
prompt
```

Simpan:

```json
{
  "prompt_template": "hadith_research_v3",
  "system_prompt_version": "3.1",
  "model": "...",
  "temperature": 0.1
}
```

---

# 28.38 Answer Generator

Gunakan format structured generation:

```json
{
  "answer_sections": [
    {
      "title": "Ringkasan",
      "claims": []
    },
    {
      "title": "Sanad",
      "claims": []
    },
    {
      "title": "Penjelasan Fathul Bari",
      "claims": []
    },
    {
      "title": "Variasi Riwayat",
      "claims": []
    }
  ]
}
```

Baru kemudian renderer menghasilkan Markdown/HTML.

---

# 28.39 Kenapa Structured Output?

Supaya:

```text
LLM
 ↓
JSON
 ↓
Claim Validator
 ↓
Citation Engine
 ↓
Renderer
```

bukan:

```text
LLM
 ↓
free-form text
```

yang sulit diaudit.

---

# 28.40 Research Answer Schema

```python
class ResearchAnswer:
    title: str

    summary: str

    sections: list

    claims: list

    citations: list

    uncertainty: list

    related_sources: list
```

---

# 28.41 Uncertainty Section

Jika ada ketidakpastian:

```text
Catatan:

Identifikasi perawi pada bagian ini belum diverifikasi
secara manual.
```

Jangan disembunyikan.

---

# 28.42 Contradiction Detection

Stage 28 juga harus mendeteksi:

```text
Source A:
grade = sahih

Source B:
grade = hasan

Source C:
grade = dhaif
```

Jangan melakukan:

```text
"Hadis ini disepakati sahih."
```

secara otomatis.

Tampilkan:

```text
Ditemukan perbedaan penilaian dalam sumber.
```

---

# 28.43 Contradiction Object

```json
{
  "topic": "grading",
  "positions": [
    {
      "source": "A",
      "position": "SAHIH"
    },
    {
      "source": "B",
      "position": "HASAN"
    }
  ]
}
```

---

# 28.44 Source Conflict Engine

Deteksi konflik pada:

```text
grading
narrator identity
hadith wording
book reference
page reference
chronology
```

---

# 28.45 Conflict UI

```text
┌───────────────────────────────────────────┐
│ ⚠ SOURCE DIFFERENCE                      │
├───────────────────────────────────────────┤
│ Source A                                  │
│ → Sahih                                   │
│                                           │
│ Source B                                  │
│ → Hasan                                   │
│                                           │
│ [Compare Sources]                         │
└───────────────────────────────────────────┘
```

---

# 28.46 Research Answer Quality Score

Internal scoring:

```text
Evidence Coverage
Source Quality
Citation Coverage
Contradiction Handling
Answer Relevance
```

Contoh:

```json
{
  "evidence_coverage": 0.94,
  "citation_coverage": 0.98,
  "source_quality": 0.96,
  "contradiction_handling": 1.0
}
```

Jangan tampilkan sebagai "kebenaran hadis". Ini **quality metric sistem**.

---

# 28.47 Research API

```http
POST /api/v1/research
```

Request:

```json
{
  "question": "Apa penjelasan Ibn Hajar tentang hadis niat?",
  "mode": "DEEP_RESEARCH"
}
```

Response:

```json
{
  "session_id": "R-001",
  "intent": "SHARH_LOOKUP",
  "status": "COMPLETED",

  "answer": {
    "sections": []
  },

  "claims": [],
  "citations": [],
  "evidence": [],
  "uncertainties": []
}
```

---

# 28.48 Streaming Research

Untuk Deep Research, gunakan streaming:

```text
POST /research
       │
       ▼
Research started...
       │
       ▼
Identifying hadith...
       │
       ▼
Searching Fathul Bari...
       │
       ▼
Analyzing isnad...
       │
       ▼
Comparing variants...
       │
       ▼
Validating citations...
       │
       ▼
Completed
```

Frontend menggunakan:

```text
SSE
```

atau WebSocket.

---

# 28.49 Research Event

```json
{
  "event": "RESEARCH_STEP_COMPLETED",
  "step": "VARIANT_SEARCH",
  "progress": 0.65
}
```

---

# 28.50 Safety Layer untuk Hadith Research

Karena ini aplikasi ilmiah/agama, tambahkan:

```text
DO NOT FABRICATE
DO NOT INVENT SOURCE
DO NOT INVENT PAGE
DO NOT INVENT HADITH NUMBER
DO NOT INVENT NARRATOR
DO NOT MERGE VARIANTS SILENTLY
DO NOT ATTRIBUTE UNSOURCED CLAIM TO IBN HAJAR
```

Ini harus menjadi **programmatic validation**, bukan hanya prompt.

---

# 28.51 Hallucination Firewall

Sebelum jawaban keluar:

```text
Generated Answer
      │
      ▼
Claim Extraction
      │
      ▼
Evidence Matching
      │
      ├── supported ──► PASS
      │
      └── unsupported ─► REJECT
                              │
                              ▼
                          Regenerate
```

---

# 28.52 Citation Validator

Pseudo-code:

```python
def validate_claims(answer):
    for claim in answer.claims:

        if not claim.evidence_ids:
            return False

        if not evidence_exists(claim.evidence_ids):
            return False

        if claim.requires_source and not has_primary_source(claim):
            return False

    return True
```

---

# 28.53 Research Answer Renderer

Markdown:

```markdown
## Ringkasan

...

## Sanad

...

## Penjelasan Ibn Hajar

...

## Variasi Riwayat

...

## Catatan

...

## Sumber

1. Fathul Bari...
2. Sahih al-Bukhari...
```

---

# 28.54 Export Research

Karena platform Anda juga diarahkan ke publication workflow, tambahkan:

```text
Export:
├── Markdown
├── PDF
├── DOCX
└── JSON Research Record
```

JSON penting untuk reproducibility.

---

# 28.55 Folder Architecture

Tambahkan:

```text
backend/
└── app/
    ├── research/
    │   ├── intent.py
    │   ├── planner.py
    │   ├── executor.py
    │   ├── tools.py
    │   ├── evidence.py
    │   ├── claims.py
    │   ├── citations.py
    │   ├── conflicts.py
    │   ├── validator.py
    │   ├── answer.py
    │   └── sessions.py
    │
    ├── llm/
    │   ├── client.py
    │   ├── prompts.py
    │   ├── structured.py
    │   └── versions.py
    │
    └── api/
        └── research.py
```

Frontend:

```text
frontend/
└── src/
    ├── pages/
    │   └── ResearchPage/
    │
    ├── components/
    │   ├── ResearchInput/
    │   ├── ResearchProgress/
    │   ├── EvidencePanel/
    │   ├── CitationMap/
    │   ├── ClaimCard/
    │   ├── ConflictPanel/
    │   └── ResearchAnswer/
    │
    └── services/
        └── researchApi.ts
```

---

# 28.56 Database Tambahan

Minimal:

```text
research_sessions
research_steps
research_claims
research_evidence
research_citations
research_conflicts
research_answers
```

---

# 28.57 Research Claims

```sql
CREATE TABLE research_claims (
    id UUID PRIMARY KEY,

    session_id UUID NOT NULL,

    claim_text TEXT NOT NULL,

    claim_type VARCHAR(40),

    confidence NUMERIC(6,5),

    validation_status VARCHAR(30),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 28.58 Research Evidence

```sql
CREATE TABLE research_evidence (
    id UUID PRIMARY KEY,

    session_id UUID NOT NULL,

    claim_id UUID,

    source_id UUID,

    document_id UUID,

    chunk_id UUID,

    evidence_type VARCHAR(50),

    relevance_score NUMERIC(8,5),

    confidence NUMERIC(6,5),

    metadata JSONB DEFAULT '{}'
);
```

---

# 28.59 Research Citation

```sql
CREATE TABLE research_citations (
    id UUID PRIMARY KEY,

    claim_id UUID NOT NULL,

    source_id UUID NOT NULL,

    locator TEXT,

    citation_text TEXT,

    validation_status VARCHAR(30),

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 28.60 Example End-to-End

User:

> **"Jelaskan bagaimana Ibn Hajar menjelaskan hadis إنما الأعمال بالنيات, siapa saja perawinya, dan bandingkan dengan riwayat Muslim."**

### Step 1

Intent:

```text
COMPLEX_HADITH_RESEARCH
```

### Step 2

Identify:

```text
Hadith: إنما الأعمال بالنيات
```

### Step 3

Retrieve:

```text
Bukhari
Muslim
Fathul Bari
```

### Step 4

Isnad:

```text
Malik
 ↓
Nafi'
 ↓
Ibn Umar
...
```

sesuai data sumber yang benar-benar ditemukan.

### Step 5

Variant search:

```text
Bukhari variant
Muslim variant
```

### Step 6

Commentary:

```text
Fathul Bari relevant chunks
```

### Step 7

Evidence:

```text
EV001 Hadith
EV002 Fathul Bari
EV003 Muslim
EV004 Isnad
```

### Step 8

Claim generation:

```text
Claim 1 → EV002
Claim 2 → EV001
Claim 3 → EV003
```

### Step 9

Validation:

```text
Claim coverage = PASS
```

### Step 10

Render:

```text
Jawaban
[1] [2] [3]
```

---

# 28.61 Definition of Done

Stage 28 selesai jika:

```text
[ ] Natural language query
[ ] Intent classification
[ ] Research planner
[ ] Controlled research tools
[ ] Query expansion
[ ] Indonesian → Arabic search
[ ] Hadith identification
[ ] Commentary retrieval
[ ] Isnad retrieval
[ ] Variant retrieval
[ ] Evidence pack
[ ] Claim extraction
[ ] Claim/evidence mapping
[ ] Citation generation
[ ] Citation validation
[ ] Conflict detection
[ ] Uncertainty handling
[ ] Hallucination firewall
[ ] Research session
[ ] Research history
[ ] Deep Research mode
[ ] Streaming progress
[ ] Research export
```

---

# 28.62 Arsitektur Lengkap Setelah Stage 28

Sekarang blueprint aplikasi menjadi:

```text
                         USER
                           │
                           ▼
                 ┌───────────────────┐
                 │ RESEARCH ENGINE   │
                 │                   │
                 │ Intent            │
                 │ Planner           │
                 │ Evidence          │
                 │ Claims            │
                 │ Citations         │
                 └─────────┬─────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       HADITH           FATHUL BARI       GRAPH
      ENGINE             ENGINE           ENGINE
          │                │                │
          ▼                ▼                ▼
       Variants          Syarah          Isnad
       Matn              Commentary      Narrators
       Sources           Linguistic      Relations
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    ARABIC NLP
                           │
                           ▼
                   HYBRID RETRIEVAL
                           │
                           ▼
                         RAG
                           │
                           ▼
                         LLM
                           │
                           ▼
                  CLAIM VALIDATOR
                           │
                           ▼
                  CITATION ENGINE
                           │
                           ▼
                     FINAL ANSWER
```
