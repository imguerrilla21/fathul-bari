# Stage 45 — Production Reliability, Evaluation & Quality Control

Stage 45 adalah **lapisan pengendalian mutu dan reliability** untuk seluruh aplikasi Syarah *Fathul Bari* yang sudah kita bangun.

Tujuan utamanya bukan menambah fitur baru, tetapi memastikan:

> **Setiap jawaban AI dapat dievaluasi, setiap citation dapat diverifikasi, setiap perubahan model/prompt dapat dilacak, dan sistem dapat diketahui kapan mengalami penurunan kualitas.**

---

# 45.1 Arsitektur Stage 45

```text
                         PRODUCTION SYSTEM
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        APPLICATION          AI/RAG           DATABASE
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                     OBSERVABILITY LAYER
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
      Evaluation            Monitoring             Audit
          │                     │                     │
          ▼                     ▼                     ▼
      Quality Score        Metrics/Alerts        Trace Log
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                       QUALITY DASHBOARD
```

---

# 45.2 Prinsip Utama

Stage 45 menggunakan prinsip:

```text
SOURCE
  ↓
RETRIEVAL
  ↓
GENERATION
  ↓
CITATION
  ↓
ATTRIBUTION
  ↓
VALIDATION
  ↓
OBSERVABILITY
```

Setiap tahap harus bisa diperiksa.

---

# 45.3 Lima Dimensi Kualitas

Gunakan lima kelompok utama:

```text
1. Retrieval Quality
2. Answer Quality
3. Citation Quality
4. Attribution Quality
5. System Reliability
```

---

# 45.4 Retrieval Quality

Evaluasi apakah sistem menemukan sumber yang benar.

Metric:

```text
Recall@K
Precision@K
MRR
nDCG
Evidence Coverage
```

Contoh:

```text
Question:
Apa penjelasan Ibn Hajar mengenai niat?

Top 10 retrieved:
7 relevant
3 irrelevant

Recall@10 = ...
```

---

# 45.5 Answer Quality

Evaluasi:

```text
Faithfulness
Completeness
Relevance
Clarity
Correctness
```

Tetapi untuk aplikasi ilmiah, **Faithfulness terhadap sumber** harus menjadi prioritas.

---

# 45.6 Citation Quality

Metric:

```text
Citation Precision
Citation Recall
Citation Completeness
Citation Correctness
Citation Entailment
```

Contoh:

```text
AI claim
   ↓
Citation
   ↓
Does citation actually support claim?
```

---

# 45.7 Attribution Quality

Metric:

```text
Speaker Accuracy
Quote Attribution Accuracy
Nested Attribution Accuracy
Scholar Resolution Accuracy
False Attribution Rate
```

Metric paling kritis:

```text
FALSE_ATTRIBUTION_RATE
```

---

# 45.8 Reliability Metrics

Pantau:

```text
API latency
Error rate
Timeout rate
Database latency
Queue latency
LLM latency
Embedding latency
Vector search latency
```

---

# 45.9 Observability Architecture

Gunakan tiga pilar:

```text
LOGS
METRICS
TRACES
```

```text
Logs
 ↓
Apa yang terjadi?

Metrics
 ↓
Seberapa sering?

Traces
 ↓
Mengapa terjadi?
```

---

# 45.10 Request Trace

Setiap pertanyaan user mendapatkan:

```text
trace_id
```

Contoh:

```text
TRACE-20260813-8F3A
```

Flow:

```text
User Question
     │
     ▼
API
     │
     ▼
Query Analyzer
     │
     ▼
Retriever
     │
     ▼
Reranker
     │
     ▼
Context Builder
     │
     ▼
LLM
     │
     ▼
Citation Validator
     │
     ▼
Final Answer
```

Semua memiliki trace yang sama.

---

# 45.11 Request Log

```sql
CREATE TABLE request_logs (
    id UUID PRIMARY KEY,

    trace_id TEXT NOT NULL,

    user_id UUID,

    endpoint TEXT,

    request_type VARCHAR(50),

    status VARCHAR(30),

    latency_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 45.12 AI Generation Log

```sql
CREATE TABLE ai_generation_logs (
    id UUID PRIMARY KEY,

    trace_id TEXT,

    model_name TEXT,

    model_version TEXT,

    prompt_version TEXT,

    retrieval_version TEXT,

    input_tokens INTEGER,

    output_tokens INTEGER,

    latency_ms INTEGER,

    finish_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 45.13 RAG Trace

Simpan:

```json
{
  "trace_id": "TRACE-001",

  "query": "Apa penjelasan Ibn Hajar?",

  "retrieval": {
    "method": "hybrid",
    "top_k": 20
  },

  "reranking": {
    "top_k": 8
  },

  "context": [
    "P001",
    "P009",
    "P012"
  ]
}
```

---

# 45.14 Tidak Menyimpan Data Sensitif Berlebihan

Log sebaiknya menyimpan:

```text
IDs
metadata
metrics
source IDs
trace
```

bukan seluruh isi percakapan jika tidak diperlukan.

---

# 45.15 Evaluation Dataset

Buat dataset khusus:

```text
evaluation/
├── retrieval/
├── citation/
├── attribution/
├── qa/
├── hallucination/
└── regression/
```

---

# 45.16 Golden Questions

Buat pertanyaan yang jawabannya telah diverifikasi.

Contoh:

```json
{
  "id": "Q001",

  "question":
  "Apa penjelasan Ibn Hajar mengenai hadits niat?",

  "expected_sources": [
    "P88421",
    "P88422"
  ],

  "expected_scholars": [
    "Ibn Hajar"
  ]
}
```

---

# 45.17 Golden Answer

Tidak harus menyimpan satu jawaban literal.

Lebih baik menyimpan:

```text
Expected Claims
Expected Sources
Expected Scholars
Expected Relations
Forbidden Claims
```

Karena jawaban AI dapat memiliki banyak bentuk yang benar.

---

# 45.18 Evaluation Schema

```sql
CREATE TABLE evaluation_cases (
    id UUID PRIMARY KEY,

    case_id TEXT UNIQUE,

    category VARCHAR(50),

    question TEXT NOT NULL,

    expected JSONB,

    metadata JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 45.19 Evaluation Run

```sql
CREATE TABLE evaluation_runs (
    id UUID PRIMARY KEY,

    name TEXT,

    model_version TEXT,

    prompt_version TEXT,

    retrieval_version TEXT,

    dataset_version TEXT,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    results JSONB
);
```

---

# 45.20 Evaluation Result

```sql
CREATE TABLE evaluation_results (
    id UUID PRIMARY KEY,

    run_id UUID,

    case_id TEXT,

    score NUMERIC,

    passed BOOLEAN,

    metrics JSONB,

    failure_reason TEXT
);
```

---

# 45.21 Regression Testing

Setiap perubahan pada:

```text
LLM
Prompt
Retriever
Reranker
Embedding
OCR
Database
Knowledge Graph
```

harus menjalankan evaluation suite.

---

# 45.22 Regression Pipeline

```text
Code Change
     ↓
Unit Tests
     ↓
Integration Tests
     ↓
RAG Tests
     ↓
Citation Tests
     ↓
Attribution Tests
     ↓
Golden Dataset
     ↓
Quality Gate
```

---

# 45.23 Quality Gate

Contoh:

```text
Retrieval Recall ≥ 90%
Citation Precision ≥ 95%
Attribution Accuracy ≥ 98%
False Attribution ≤ 1%
API Error Rate ≤ 1%
```

Angka ini adalah **initial engineering targets**, bukan klaim performa sistem Anda saat ini.

---

# 45.24 Build Failure

Jika hasil:

```text
Citation Precision
95.8% → 91.2%
```

maka:

```text
QUALITY GATE FAILED
```

Deployment ditahan.

---

# 45.25 Model Versioning

Jangan hanya menyimpan:

```text
model = GPT-X
```

Gunakan:

```text
model_provider
model_name
model_version
configuration
temperature
max_tokens
```

---

# 45.26 Prompt Versioning

Setiap system prompt:

```text
research-v1
research-v2
research-v3
```

Disimpan.

Contoh:

```json
{
  "prompt_id": "research-answer",
  "version": "3",
  "hash": "..."
}
```

---

# 45.27 Retrieval Version

Retrieval pipeline juga diberi versi:

```text
retrieval-v1
retrieval-v2
retrieval-v3
```

Karena perubahan:

```text
chunk size
embedding model
reranker
filters
```

dapat mengubah jawaban.

---

# 45.28 Dataset Versioning

Gunakan:

```text
dataset-v1
dataset-v2
dataset-v3
```

Contoh:

```text
hadith-corpus-v4
fath-bari-corpus-v7
evaluation-set-v3
```

---

# 45.29 Reproducibility

Sebuah jawaban harus bisa direkonstruksi:

```text
Question
+
Model version
+
Prompt version
+
Retrieval version
+
Corpus version
+
Citation data
=
Reproducible Result
```

---

# 45.30 Research Snapshot

Kita lanjutkan fitur snapshot Stage 44.

```json
{
  "snapshot_id": "SNAP-001",

  "corpus": "fath-bari-v7",

  "model": "MODEL-X",

  "prompt": "research-v3",

  "retrieval": "rag-v8",

  "dataset": "eval-v4"
}
```

---

# 45.31 Hallucination Detection

Buat validator:

```text
Generated Claim
       ↓
Search Evidence
       ↓
Evidence Found?
    /       \
  YES       NO
   ↓         ↓
SUPPORTED  UNSUPPORTED
```

---

# 45.32 Hallucination Types

```text
FABRICATED_CITATION
FABRICATED_QUOTE
FALSE_ATTRIBUTION
UNSUPPORTED_CLAIM
SOURCE_MISMATCH
CONTEXT_DISTORTION
```

---

# 45.33 Fabricated Citation

Jika AI menghasilkan:

> Fathul Bari 5/231

tetapi halaman tersebut tidak ditemukan:

```text
FABRICATED_CITATION
```

---

# 45.34 Fabricated Quote

Jika AI menggunakan tanda kutip:

> "..."

tetapi string tidak ditemukan pada corpus:

```text
FABRICATED_QUOTE
```

atau:

```text
QUOTE_VARIANT
```

jika hanya berbeda karena normalisasi/OCR.

---

# 45.35 Citation Entailment

Pertanyaan validator:

> Apakah sumber benar-benar mendukung klaim?

Contoh:

```text
Claim:
Ibn Hajar memilih pendapat A.

Citation:
Passage P001

Evidence:
Ibn Hajar hanya menyebut pendapat A.

Result:
PARTIAL_SUPPORT
```

---

# 45.36 Support Levels

```text
FULL_SUPPORT
PARTIAL_SUPPORT
WEAK_SUPPORT
NO_SUPPORT
CONTRADICTS
```

---

# 45.37 Claim-Evidence Matrix

```text
┌───────────────────────┬──────────────┬───────────┐
│ Claim                 │ Evidence     │ Support   │
├───────────────────────┼──────────────┼───────────┤
│ Claim 1               │ P001         │ FULL      │
│ Claim 2               │ P005         │ PARTIAL   │
│ Claim 3               │ P008         │ NONE      │
└───────────────────────┴──────────────┴───────────┘
```

---

# 45.38 Citation Coverage

Formula sederhana:

```text
Citation Coverage =
supported claims / total factual claims
```

Misalnya:

```text
8 / 10 = 80%
```

Target dapat ditetapkan sesuai mode aplikasi.

---

# 45.39 Scholarly Mode

Untuk mode:

```text
RESEARCH
```

gunakan threshold lebih ketat daripada:

```text
GENERAL
```

Contoh:

```text
General:
citation optional

Research:
citation required

Academic:
citation + attribution + evidence required
```

---

# 45.40 Three AI Modes

Tambahkan:

```text
QUICK
RESEARCH
SCHOLARLY
```

### QUICK

Jawaban singkat.

### RESEARCH

Evidence + citation.

### SCHOLARLY

Evidence + citation + attribution + uncertainty.

---

# 45.41 Scholarly Response Format

```text
Jawaban
──────────────

Dalil:
...

Penjelasan Ibn Hajar:
...

Pendapat ulama lain:
...

Analisis:
...

Sumber:
[1] ...
[2] ...

Catatan:
Bagian terakhir merupakan inferensi berdasarkan sumber.
```

---

# 45.42 Uncertainty Layer

AI harus dapat mengatakan:

```text
HIGH CONFIDENCE
MODERATE CONFIDENCE
LOW CONFIDENCE
INSUFFICIENT EVIDENCE
```

---

# 45.43 Confidence Decomposition

Jangan hanya:

```text
confidence = 0.92
```

Gunakan:

```json
{
  "retrieval_confidence": 0.96,
  "attribution_confidence": 0.99,
  "citation_confidence": 0.95,
  "answer_confidence": 0.88
}
```

---

# 45.44 Overall Quality

Jangan sekadar mengambil rata-rata.

Gunakan **weakest-link principle**:

```text
Overall =
minimum(
  retrieval,
  citation,
  attribution,
  evidence
)
```

Karena:

```text
Retrieval = 99%
Attribution = 50%
```

jawaban tetap berisiko.

---

# 45.45 OCR Quality Monitoring

Karena sumber Fathul Bari dapat berasal dari OCR:

pantau:

```text
OCR confidence
Arabic character error
missing words
line order
page alignment
```

---

# 45.46 OCR Flags

```text
LOW_OCR
SUSPECTED_MISSING_TEXT
SUSPECTED_DUPLICATION
PAGE_ORDER_ERROR
ARABIC_NORMALIZATION_ISSUE
```

---

# 45.47 Source Health

Dashboard:

```text
Fathul Bari
────────────────────────
Pages indexed       8,421
OCR quality         97.4%
Embeddings          100%
Metadata             99%
Broken pages          3
```

---

# 45.48 Corpus Integrity Check

Secara periodik:

```text
Source
 ↓
Page count
 ↓
Hash
 ↓
OCR
 ↓
Embedding
 ↓
Index
```

Jika source berubah:

```text
CORPUS VERSION CHANGED
```

---

# 45.49 Hashing

Setiap passage:

```text
content_hash
```

Setiap source:

```text
source_hash
```

Setiap dataset:

```text
dataset_hash
```

---

# 45.50 Integrity Chain

```text
BOOK
 ↓
VOLUME
 ↓
PAGE
 ↓
PASSAGE
 ↓
HASH
```

Dengan demikian kita bisa mengetahui apakah evidence yang digunakan AI berubah.

---

# 45.51 Monitoring Dashboard

```text
┌──────────────────────────────────────────────────┐
│ PRODUCTION QUALITY                               │
├──────────────────────────────────────────────────┤
│                                                  │
│ Retrieval Recall              94.7%              │
│ Citation Precision            97.1%              │
│ Attribution Accuracy          99.0%              │
│ Unsupported Claims             1.8%              │
│                                                  │
│ API Error Rate                 0.3%              │
│ P95 Latency                  2.8 sec             │
│                                                  │
│ RAG Cost / Query             $0.00X              │
│                                                  │
└──────────────────────────────────────────────────┘
```

Angka di atas hanya contoh tampilan.

---

# 45.52 Alert System

Alert ketika:

```text
Citation precision ↓
False attribution ↑
API error ↑
Latency ↑
LLM cost ↑
OCR quality ↓
Database storage ↑
```

---

# 45.53 Alert Severity

```text
INFO
WARNING
ERROR
CRITICAL
```

Contoh:

```text
CRITICAL:
False Attribution Rate > threshold
```

---

# 45.54 Cost Monitoring

Untuk setiap AI request:

```text
input_tokens
output_tokens
embedding_tokens
reranker_cost
model_cost
```

Hitung:

```text
cost_per_request
cost_per_project
cost_per_user
cost_per_day
```

---

# 45.55 Cost Dashboard

```text
Today
────────────────────
Queries             1,240
AI generation       ...
Embeddings          ...
Total               ...

Average/query       ...
```

---

# 45.56 Budget Guard

Tambahkan:

```text
DAILY_LIMIT
MONTHLY_LIMIT
PROJECT_LIMIT
```

Jika melewati:

```text
SOFT_LIMIT
```

beri peringatan.

Jika melewati:

```text
HARD_LIMIT
```

blokir AI generation sampai diotorisasi.

---

# 45.57 Latency Budget

Target internal:

```text
API                 < 300ms
Retrieval           < 500ms
Reranking           < 500ms
LLM                 variable
Citation validation < 500ms
```

LLM tetap menjadi komponen paling variable.

---

# 45.58 Trace Example

```text
TRACE-001

API                40 ms
Query Analysis     80 ms
Vector Search     180 ms
BM25                40 ms
Reranking          220 ms
Context Build       30 ms
LLM               1800 ms
Citation Check     240 ms
────────────────────────
Total             2630 ms
```

Ini memungkinkan bottleneck ditemukan dengan cepat.

---

# 45.59 Error Taxonomy

Gunakan error code:

```text
RAG-001 Retrieval Failure
RAG-002 Empty Context

LLM-001 Generation Failure
LLM-002 Timeout

CIT-001 Citation Missing
CIT-002 Citation Invalid

ATTR-001 Attribution Failure
ATTR-002 False Attribution

OCR-001 OCR Failure

DB-001 Database Failure
```

---

# 45.60 Incident Record

```sql
CREATE TABLE incidents (
    id UUID PRIMARY KEY,

    incident_code TEXT,

    severity VARCHAR(20),

    component VARCHAR(50),

    description TEXT,

    trace_id TEXT,

    status VARCHAR(30),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    resolved_at TIMESTAMPTZ
);
```

---

# 45.61 Incident Workflow

```text
Detected
   ↓
Triaged
   ↓
Investigating
   ↓
Resolved
   ↓
Postmortem
```

---

# 45.62 Automatic Fallback

Jika vector search gagal:

```text
Vector
 ↓ FAIL
BM25
 ↓ FAIL
Exact Search
 ↓ FAIL
Graceful Error
```

Jangan menghasilkan jawaban berdasarkan tebakan jika evidence tidak tersedia.

---

# 45.63 LLM Fallback

Jika model utama gagal:

```text
Primary Model
     ↓
   FAIL
     ↓
Fallback Model
     ↓
Validation
```

Tetapi **model fallback tidak boleh melewati citation/attribution validation**.

---

# 45.64 Database Backup

Minimal:

```text
Daily Full Backup
+
Point-in-Time Recovery
```

Backup:

```text
Database
Research Projects
Annotations
Claims
Citations
Audit Trail
```

---

# 45.65 Vector Index Backup

Vector database/index juga perlu dipulihkan.

Simpan:

```text
embedding_model
embedding_dimension
corpus_version
index_version
```

---

# 45.66 Disaster Recovery

Tetapkan:

```text
RPO
RTO
```

Contoh target awal:

```text
RPO: 24 hours
RTO: 4 hours
```

Angka tersebut dapat diperketat setelah kebutuhan produksi diketahui.

---

# 45.67 Backup Verification

Backup yang tidak pernah diuji bukan backup yang dapat diandalkan.

Secara berkala:

```text
Backup
 ↓
Restore test
 ↓
Integrity check
 ↓
PASS / FAIL
```

---

# 45.68 Automated Health Check

Endpoint:

```http
GET /health
```

Response:

```json
{
  "status": "healthy",

  "database": "ok",
  "vector_store": "ok",
  "search": "ok",
  "llm": "ok",
  "storage": "ok"
}
```

---

# 45.69 Readiness Check

```http
GET /ready
```

Berbeda dengan `/health`.

```text
/health
→ service hidup

/ready
→ service siap menerima traffic
```

---

# 45.70 Evaluation API

Tambahkan:

```http
POST /api/v1/evaluation/run

GET /api/v1/evaluation/runs

GET /api/v1/evaluation/runs/{id}

GET /api/v1/evaluation/metrics

GET /api/v1/evaluation/regressions
```

---

# 45.71 Quality Gate API

```http
GET /api/v1/quality/gate
```

Response:

```json
{
  "status": "PASS",

  "checks": {
    "retrieval": true,
    "citation": true,
    "attribution": true,
    "hallucination": true
  }
}
```

---

# 45.72 Automated Evaluation Pipeline

```text
                     CODE
                       │
                       ▼
                 BUILD TEST
                       │
                       ▼
                UNIT TESTS
                       │
                       ▼
             INTEGRATION TESTS
                       │
                       ▼
               RAG EVALUATION
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
         Citation   Attribution  QA
             │         │         │
             └─────────┼─────────┘
                       ▼
                  QUALITY GATE
                   /       \
                PASS       FAIL
                 │           │
                 ▼           ▼
              DEPLOY       BLOCK
```

---

# 45.73 Canary Deployment

Untuk perubahan besar:

```text
New Version
     ↓
5% traffic
     ↓
Evaluation
     ↓
PASS?
     ↓
25%
     ↓
50%
     ↓
100%
```

---

# 45.74 Model A/B Testing

Contoh:

```text
Model A
vs
Model B
```

Bandingkan:

```text
Citation Precision
Attribution Accuracy
Latency
Cost
User Rating
```

Bukan hanya berdasarkan kualitas bahasa.

---

# 45.75 Human Evaluation

AI evaluation saja tidak cukup.

Reviewer dapat memberikan:

```text
Correct
Mostly Correct
Partially Correct
Incorrect
Unsupported
```

---

# 45.76 Reviewer Feedback

Simpan:

```sql
CREATE TABLE human_evaluations (
    id UUID PRIMARY KEY,

    trace_id TEXT,

    reviewer_id UUID,

    overall_rating INTEGER,

    factuality INTEGER,

    citation_quality INTEGER,

    attribution_quality INTEGER,

    comments TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 45.77 Human-in-the-Loop

Kasus yang otomatis diarahkan ke reviewer:

```text
HIGH_RISK
LOW_CONFIDENCE
FALSE_ATTRIBUTION
NO_EVIDENCE
CONFLICTING_EVIDENCE
```

---

# 45.78 Risk Score

```text
risk =
  attribution_risk
+ citation_risk
+ evidence_risk
+ generation_risk
```

Jika:

```text
risk > threshold
```

→ `REVIEW_REQUIRED`.

---

# 45.79 High-Risk Topics

Untuk aplikasi hadis, perlakukan lebih ketat:

```text
Aqidah
Halal/Haram
Fatwa
Nasab
Status hadis
Perkataan Nabi ﷺ
Perkataan Sahabat
Perbedaan pendapat ulama
```

---

# 45.80 Answer Policy

Untuk pertanyaan ilmiah:

```text
Evidence found
→ answer

Evidence partial
→ qualified answer

Evidence conflicting
→ present disagreement

Evidence absent
→ say insufficient evidence
```

---

# 45.81 Research Mode Output

Struktur final:

```text
## Jawaban

...

## Sumber Utama

1. Fathul Bari ...
2. ...

## Atribusi

- Ibn Hajar
- al-Nawawi

## Evidence

...

## Tingkat Kepastian

Moderate

## Catatan

Bagian X merupakan inferensi.
```

---

# 45.82 Quality Dashboard — Full

```text
┌─────────────────────────────────────────────────────┐
│             SCHOLARLY AI CONTROL CENTER              │
├─────────────────────────────────────────────────────┤
│                                                     │
│ RETRIEVAL                                          │
│ Recall@10                 94.7%                     │
│                                                     │
│ CITATION                                          │
│ Precision                 97.1%                     │
│ Coverage                  98.4%                     │
│                                                     │
│ ATTRIBUTION                                        │
│ Accuracy                  99.0%                     │
│ False Attribution         0.4%                      │
│                                                     │
│ HALLUCINATION                                      │
│ Unsupported Claims        1.2%                      │
│                                                     │
│ RELIABILITY                                        │
│ Error Rate                0.3%                      │
│ P95 Latency               2.8 sec                   │
│                                                     │
│ COST                                               │
│ Avg / Query               ...                       │
│                                                     │
│ SYSTEM STATUS             ● HEALTHY                │
└─────────────────────────────────────────────────────┘
```

---

# 45.83 Minimum Production Stack

Untuk implementasi, stack dapat tetap sederhana:

```text
Frontend
├── Next.js
└── TypeScript

Backend
├── FastAPI
├── Python
└── Pydantic

Database
└── PostgreSQL

Vector Search
└── pgvector

Search
└── PostgreSQL FTS / BM25-compatible layer

Cache
└── Redis

Queue
└── Redis + worker

Object Storage
└── S3-compatible

Observability
├── structured logs
├── metrics
└── tracing

Evaluation
└── custom evaluation pipeline
```

Tidak perlu menambahkan terlalu banyak infrastructure sebelum traffic menuntutnya.

---

# 45.84 Folder Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── evaluation.py
│   │   ├── quality.py
│   │   └── monitoring.py
│   │
│   ├── evaluation/
│   │   ├── retrieval.py
│   │   ├── citation.py
│   │   ├── attribution.py
│   │   ├── hallucination.py
│   │   └── runner.py
│   │
│   ├── observability/
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   ├── tracing.py
│   │   └── alerts.py
│   │
│   ├── quality/
│   │   ├── gates.py
│   │   ├── thresholds.py
│   │   └── scoring.py
│   │
│   └── recovery/
│       ├── backup.py
│       └── restore.py
│
├── evaluation/
│   ├── golden/
│   ├── regression/
│   ├── citation/
│   └── attribution/
│
└── scripts/
    ├── run_eval.py
    ├── quality_gate.py
    └── restore_test.py
```

---

# 45.85 Environment Configuration

```env
APP_ENV=production

DATABASE_URL=...

REDIS_URL=...

VECTOR_DATABASE_URL=...

LLM_PROVIDER=...

LLM_MODEL=...

EMBEDDING_MODEL=...

PROMPT_VERSION=research-v3

RETRIEVAL_VERSION=rag-v8

CORPUS_VERSION=fath-bari-v7

EVALUATION_DATASET_VERSION=eval-v4

DAILY_AI_BUDGET=...

MONTHLY_AI_BUDGET=...
```

---

# 45.86 Definition of Done

Stage 45 selesai jika:

```text
[ ] Structured Logging
[ ] Request Tracing
[ ] Metrics
[ ] Error Taxonomy
[ ] Health Check
[ ] Readiness Check
[ ] Evaluation Dataset
[ ] Golden Questions
[ ] Retrieval Evaluation
[ ] Citation Evaluation
[ ] Attribution Evaluation
[ ] Hallucination Detection
[ ] Regression Testing
[ ] Quality Gate
[ ] Model Versioning
[ ] Prompt Versioning
[ ] Retrieval Versioning
[ ] Dataset Versioning
[ ] Corpus Hashing
[ ] Cost Monitoring
[ ] Latency Monitoring
[ ] Alert System
[ ] Human Evaluation
[ ] Incident Management
[ ] Backup
[ ] Restore Testing
[ ] Disaster Recovery
[ ] Canary Deployment
[ ] Research Snapshot
[ ] Reproducibility
[ ] Production Dashboard
```

---

# 45.87 Status Arsitektur Setelah Stage 45

Kini keseluruhan platform dapat digambarkan:

```text
┌──────────────────────────────────────────────────────────┐
│                    USER / RESEARCHER                     │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  RESEARCH WORKSPACE                      │
│              Stage 44 — Annotation/Notes                 │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  RAG / SYARAH AI                          │
│                    Stage 40+                              │
└──────────────────────────┬───────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     RETRIEVAL        ATTRIBUTION       KNOWLEDGE GRAPH
          │                │                │
          └────────────────┼────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────┐
│             CITATION / EVIDENCE VALIDATION               │
│                       Stage 42                            │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             QUALITY & RELIABILITY LAYER                   │
│                       Stage 45                            │
│                                                          │
│ Evaluation │ Monitoring │ Audit │ Cost │ Backup          │
└──────────────────────────────────────────────────────────┘
```

## Hasil penting Stage 45

Dengan Stage 45, aplikasi Anda tidak lagi sekadar memiliki:

**Hadis → Fathul Bari → RAG → AI.**

Tetapi menjadi:

**Hadis → sumber → evidence → attribution → citation → AI → validation → audit → evaluation → reproducible research.**

Itulah fondasi yang diperlukan sebelum sistem mulai digunakan untuk **penelitian syarah dalam skala besar**.
