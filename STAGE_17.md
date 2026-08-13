# Stage 17 — Production Implementation & Deployment Architecture

Sekarang kita masuk ke tahap **mengubah seluruh blueprint Fathul Bari Research AI menjadi sistem production-ready**.

Sampai Stage 16 kita sudah memiliki:

```text
Ahmad Sanusi Hadith API
        ↓
Corpus Ingestion
        ↓
Fathul Bari Processing
        ↓
Arabic NLP
        ↓
Advanced Hadith Matching
        ↓
Knowledge Graph
        ↓
Hybrid RAG
        ↓
Research-Grade RAG
        ↓
Citation + Audit
```

Stage 17 akan menyatukan semuanya menjadi **aplikasi yang bisa dijalankan secara nyata**.

---

# 17.1 Production Architecture

Arsitektur yang saya rekomendasikan:

```text
                         INTERNET
                            │
                            ▼
                    ┌───────────────┐
                    │ NGINX / CADDY │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       ┌──────────────┐            ┌──────────────┐
       │   FRONTEND   │            │   API        │
       │   Next.js    │            │   FastAPI    │
       └──────────────┘            └──────┬───────┘
                                         │
             ┌───────────────────────────┼────────────────────┐
             │                           │                    │
             ▼                           ▼                    ▼
      ┌─────────────┐             ┌─────────────┐     ┌─────────────┐
      │ PostgreSQL  │             │    Redis    │     │ Object      │
      │ + pgvector  │             │             │     │ Storage     │
      └─────────────┘             └──────┬──────┘     └─────────────┘
                                         │
                                         ▼
                                  ┌─────────────┐
                                  │ Worker      │
                                  │ Celery/RQ   │
                                  └──────┬──────┘
                                         │
                  ┌──────────────────────┼──────────────────────┐
                  ▼                      ▼                      ▼
             OCR Worker            NLP Worker            RAG Worker
                  │                      │                      │
                  └──────────────────────┼──────────────────────┘
                                         ▼
                                  External Services
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                       Ahmad Sanusi API       LLM / Embedding
```

---

# 17.2 Technology Stack

Saya sarankan stack berikut:

| Layer         | Teknologi                  |
| ------------- | -------------------------- |
| Frontend      | Next.js + TypeScript       |
| UI            | Tailwind CSS               |
| Backend       | FastAPI                    |
| Language      | Python 3.12+               |
| Database      | PostgreSQL                 |
| Vector        | pgvector                   |
| Cache         | Redis                      |
| Queue         | Celery                     |
| PDF Storage   | S3-compatible storage      |
| Search        | PostgreSQL FTS + pgvector  |
| Auth          | JWT / session-based auth   |
| API Docs      | OpenAPI                    |
| Containers    | Docker                     |
| Reverse Proxy | Caddy/Nginx                |
| Monitoring    | OpenTelemetry + Prometheus |
| Logs          | Structured JSON logging    |

Untuk tahap awal, kita **tidak perlu Elasticsearch/OpenSearch**.

PostgreSQL + pgvector + full-text search sudah cukup untuk MVP sampai skala yang cukup besar.

---

# 17.3 Monorepo

Struktur final:

```text
fathul-bari-ai/
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── hooks/
│   │   └── public/
│   │
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── core/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── repositories/
│       │   ├── workers/
│       │   ├── nlp/
│       │   ├── retrieval/
│       │   ├── matching/
│       │   ├── assistant/
│       │   ├── graph/
│       │   └── citations/
│       │
│       └── tests/
│
├── packages/
│   ├── shared-types/
│   └── ui/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── evaluation/
│
├── infra/
│   ├── docker/
│   ├── nginx/
│   ├── postgres/
│   └── monitoring/
│
├── scripts/
│
├── migrations/
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── Makefile
└── README.md
```

---

# 17.4 Backend Structure

```text
apps/api/app/
│
├── main.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── logging.py
│   ├── database.py
│   └── storage.py
│
├── api/
│   └── v1/
│       ├── auth.py
│       ├── hadith.py
│       ├── corpus.py
│       ├── source.py
│       ├── review.py
│       ├── matching.py
│       ├── graph.py
│       ├── assistant.py
│       └── research.py
│
├── models/
│
├── schemas/
│
├── repositories/
│
├── services/
│
├── workers/
│
├── nlp/
│
├── retrieval/
│
├── matching/
│
├── assistant/
│
├── graph/
│
└── citations/
```

Prinsip:

```text
API
 ↓
Service
 ↓
Repository
 ↓
Database
```

Jangan menaruh business logic langsung di endpoint.

---

# 17.5 Database Architecture

Database utama:

```text
PostgreSQL
```

Extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Kemudian:

```text
PostgreSQL
├── relational data
├── full-text search
├── JSONB metadata
└── vector embeddings
```

Ini mengurangi kompleksitas infrastruktur.

---

# 17.6 Database Schema Utama

```text
users
roles
permissions

sources
source_files
source_pages

books
volumes
chapters
sections

hadiths
hadith_variants
hadith_concepts

narrators
narrator_aliases
sanad_chains
sanad_links

hadith_mentions
hadith_matches

sharh_chunks
embeddings

cross_references
scholar_mentions

review_tasks
review_decisions

research_queries
research_runs
evidence_units
claims
claim_citations

audit_events
system_jobs
```

---

# 17.7 Source Tables

```text
sources
```

Contoh:

```text
id
name
type
language
publisher
edition
metadata
created_at
```

Contoh:

```json
{
  "name": "Fath al-Bari",
  "type": "BOOK",
  "language": "ar"
}
```

---

# 17.8 Source File

```text
source_files
```

Field:

```text
id
source_id
filename
storage_key
mime_type
size
checksum
page_count
status
```

Checksum penting:

```text
SHA-256
```

sehingga kita dapat memastikan PDF yang diproses tidak berubah.

---

# 17.9 Page Table

```text
source_pages
```

```text
id
source_file_id
page_number
image_key
raw_text
normalized_text
search_text
ocr_confidence
quality_score
```

---

# 17.10 Hadith Model

```text
hadiths
```

Minimal:

```text
id
external_id
collection
hadith_number
arabic_text
normalized_text
search_text
narrator_text
metadata
```

Untuk Ahmad Sanusi API, `external_id` menjadi kunci penting.

Misalnya:

```text
external_id =
ahmad-sanusi:bukhari:1
```

Dengan begitu kita tidak bergantung pada integer ID internal.

---

# 17.11 Sharh Chunk

```text
sharh_chunks
```

```text
id
section_id
source_page_id
hadith_id
text
normalized_text
token_count
embedding
metadata
```

Metadata:

```json
{
  "volume": 1,
  "page": 45,
  "section": "باب بدء الوحي"
}
```

---

# 17.12 Vector Index

Untuk PostgreSQL + pgvector:

```text
embedding vector(...)
```

Kemudian index sesuai kebutuhan skala.

Untuk tahap awal:

```text
HNSW
```

lebih praktis untuk retrieval vector.

---

# 17.13 Full Text Search

Buat generated search representation:

```text
search_document
```

yang menggabungkan:

```text
title
section
Arabic text
normalized text
metadata
```

Kemudian:

```text
GIN index
```

untuk pencarian lexical.

---

# 17.14 Hybrid Search

Query:

```text
"إنما الأعمال بالنيات"
```

menjalankan:

```text
              QUERY
                │
       ┌────────┴────────┐
       ▼                 ▼
 PostgreSQL FTS      pgvector
       │                 │
       └────────┬────────┘
                ▼
             RRF
                │
                ▼
             Reranker
```

---

# 17.15 Reciprocal Rank Fusion

Untuk menggabungkan:

```text
BM25 rank
Vector rank
Graph rank
```

gunakan RRF.

Konsep:

```text
score =
Σ 1 / (k + rank)
```

Nilai `k` perlu dikalibrasi lewat evaluasi.

---

# 17.16 Job Queue

Jangan memproses PDF besar di HTTP request.

Salah:

```text
POST /upload
    ↓
OCR 500 pages
    ↓
HTTP request menunggu
```

Benar:

```text
POST /upload
    ↓
Create Job
    ↓
Return job_id
    ↓
Worker
    ↓
OCR
    ↓
NLP
    ↓
Matching
```

---

# 17.17 Job States

```text
QUEUED
RUNNING
PAUSED
FAILED
COMPLETED
CANCELLED
```

---

# 17.18 Pipeline Job

```text
INGEST
  ↓
EXTRACT
  ↓
OCR
  ↓
NORMALIZE
  ↓
SECTION_DETECT
  ↓
HADITH_DETECT
  ↓
MATCH
  ↓
EMBED
  ↓
GRAPH_UPDATE
  ↓
QUALITY_CHECK
```

Setiap tahap dapat diulang secara independen.

---

# 17.19 Idempotency

Ini wajib.

Jika job:

```text
MATCH_VOLUME_1
```

dijalankan dua kali, jangan menghasilkan duplikat.

Gunakan:

```text
job_key
source_checksum
pipeline_version
```

Contoh:

```text
SHA256(PDF)
+
pipeline_version=15.2
```

---

# 17.20 Pipeline Versioning

Simpan:

```text
pipeline_version
normalizer_version
matcher_version
embedding_version
```

Karena jika kita memperbaiki Arabic NLP:

```text
v1 → v2
```

kita dapat mengetahui chunk mana yang dibuat dengan pipeline lama.

---

# 17.21 API Layer

Endpoint utama:

```text
/api/v1/auth
/api/v1/hadith
/api/v1/corpus
/api/v1/source
/api/v1/matching
/api/v1/review
/api/v1/graph
/api/v1/search
/api/v1/assistant
/api/v1/research
```

---

# 17.22 Hadith API

```http
GET /api/v1/hadith/{id}
```

Response:

```json
{
  "id": "...",
  "collection": "bukhari",
  "number": 1,
  "arabic": "...",
  "source": {
    "provider": "Ahmad Sanusi"
  }
}
```

---

# 17.23 Search API

```http
POST /api/v1/search
```

Request:

```json
{
  "query": "إنما الأعمال بالنيات",
  "mode": "HYBRID",
  "limit": 10
}
```

Response:

```json
{
  "results": [],
  "search_id": "..."
}
```

---

# 17.24 Assistant API

```http
POST /api/v1/assistant/query
```

Request:

```json
{
  "question": "Apa penjelasan Ibnu Hajar tentang niat?",
  "mode": "DEEP",
  "source_scope": ["FATH_AL_BARI"]
}
```

---

# 17.25 Streaming Assistant

Gunakan:

```text
Server-Sent Events
```

atau WebSocket jika diperlukan.

Untuk awal saya memilih:

> **SSE**

karena lebih sederhana untuk response streaming satu arah.

---

# 17.26 Review API

```http
GET /api/v1/review/tasks
```

```http
POST /api/v1/review/{id}/verify
```

```http
POST /api/v1/review/{id}/reject
```

Reject harus menyimpan:

```text
reason
note
reviewer
timestamp
```

---

# 17.27 Source API

```http
GET /api/v1/source/{id}
GET /api/v1/source/{id}/pages/{page}
GET /api/v1/source/{id}/pages/{page}/image
```

Source Viewer dapat mengambil:

```text
PDF image
OCR text
normalized text
highlight spans
```

---

# 17.28 Authentication

Minimal role:

```text
ADMIN
RESEARCHER
REVIEWER
USER
```

Permission:

```text
USER
  search
  ask

RESEARCHER
  search
  research
  export

REVIEWER
  verify
  reject

ADMIN
  everything
```

---

# 17.29 Audit Trail

Setiap perubahan penting menghasilkan:

```text
audit_events
```

Contoh:

```json
{
  "actor_id": "...",
  "action": "VERIFY_MATCH",
  "entity_type": "HADITH_MATCH",
  "entity_id": "...",
  "before": {},
  "after": {},
  "timestamp": "..."
}
```

Audit log jangan dapat diedit oleh reviewer biasa.

---

# 17.30 Security Boundary

```text
Internet
   │
   ▼
Reverse Proxy
   │
   ▼
API
   │
   ├── Auth
   ├── Rate Limit
   ├── Validation
   └── Authorization
   │
   ▼
Service
   │
   ▼
Database
```

---

# 17.31 Rate Limiting

Endpoint mahal:

```text
/assistant/query
/research
/search
```

perlu rate limit.

Contoh konseptual:

```text
anonymous:
10 requests/minute

authenticated:
60 requests/minute

researcher:
higher quota
```

Angka final sebaiknya disesuaikan dengan biaya infrastruktur.

---

# 17.32 External API Adapter

Ahmad Sanusi tidak boleh dipanggil langsung dari UI.

Salah:

```text
Browser
   ↓
Ahmad Sanusi API
```

Benar:

```text
Browser
   ↓
Our API
   ↓
Ahmad Sanusi Adapter
   ↓
Ahmad Sanusi API
```

Dengan begitu kita dapat:

```text
cache
retry
logging
validation
rate limiting
fallback
```

---

# 17.33 Ahmad Sanusi Cache

Gunakan Redis:

```text
hadith:
ahmad-sanusi:bukhari:1
```

Flow:

```text
Request
 ↓
Redis?
 ├── YES → return
 └── NO
       ↓
 Ahmad Sanusi
       ↓
 Validate
       ↓
 Redis
       ↓
 PostgreSQL
```

---

# 17.34 External API Failure

Jika Ahmad Sanusi API tidak tersedia:

```text
API DOWN
   ↓
Cached data?
 ├── YES → serve cached
 └── NO → graceful error
```

Jangan membuat data hadis dari LLM sebagai fallback.

---

# 17.35 Object Storage

PDF tidak disimpan sebagai blob besar di PostgreSQL.

Gunakan:

```text
S3-compatible storage
```

Contoh struktur:

```text
sources/
    fath-al-bari/
        vol-01.pdf
        vol-02.pdf

pages/
    fb/
        v01/
            0001.webp
            0002.webp
```

---

# 17.36 Thumbnail/Page Rendering

Untuk Source Viewer:

```text
PDF
 ↓
PDF Renderer
 ↓
WebP/JPEG page image
 ↓
Object Storage
```

Browser tidak perlu mengunduh seluruh PDF.

---

# 17.37 Docker Compose

Development:

```yaml
services:

  postgres:
    image: pgvector/pgvector:pg16

  redis:
    image: redis:7

  api:
    build: ./apps/api

  worker:
    build: ./apps/api

  web:
    build: ./apps/web
```

Untuk development ini sudah cukup.

---

# 17.38 Environment Variables

`.env.example`:

```env
APP_ENV=development

DATABASE_URL=postgresql://...
REDIS_URL=redis://...

STORAGE_ENDPOINT=...
STORAGE_BUCKET=...

AHMAD_SANUSI_API_URL=...
AHMAD_SANUSI_API_KEY=...

LLM_API_KEY=...
EMBEDDING_API_KEY=...

JWT_SECRET=...

SENTRY_DSN=
```

**API key tidak pernah ditaruh di frontend.**

---

# 17.39 Configuration Layer

Gunakan satu configuration object.

```python
class Settings:
    app_env: str
    database_url: str
    redis_url: str
    ahmad_sanusi_api_url: str
    llm_api_key: str
```

Jangan membaca environment variable secara acak di seluruh codebase.

---

# 17.40 Database Migration

Gunakan:

```text
Alembic
```

Flow:

```text
Model change
 ↓
Migration
 ↓
Review
 ↓
Apply
```

Jangan mengubah production schema secara manual.

---

# 17.41 Backup Strategy

Minimal:

```text
PostgreSQL
 ├── daily backup
 └── weekly full backup

Object Storage
 ├── versioning
 └── replication/backup
```

Database backup dan PDF backup harus diperlakukan berbeda.

---

# 17.42 Disaster Recovery

Target awal:

```text
RPO ≤ 24 jam
RTO ≤ 4 jam
```

Kemudian bisa ditingkatkan setelah production stabil.

---

# 17.43 Observability

Tiga layer:

```text
Logs
Metrics
Traces
```

Contoh metrics:

```text
api_requests_total
api_request_duration
rag_retrieval_latency
embedding_latency
llm_latency
worker_jobs_total
worker_failures_total
citation_validation_failures
```

---

# 17.44 Research Metrics

Kita juga monitor kualitas:

```text
retrieval_recall_at_5
retrieval_mrr
citation_validity
unsupported_claim_rate
review_acceptance_rate
hadith_match_precision
```

Ini sangat penting.

Karena:

> Sistem AI tidak cukup hanya "up".

Kita juga harus mengetahui apakah **jawabannya benar-benar semakin baik**.

---

# 17.45 Error Monitoring

Kategori:

```text
OCR_ERROR
NLP_ERROR
MATCHING_ERROR
RETRIEVAL_ERROR
LLM_ERROR
CITATION_ERROR
EXTERNAL_API_ERROR
DATABASE_ERROR
```

---

# 17.46 CI/CD

Pipeline:

```text
git push
   │
   ▼
Lint
   │
   ▼
Unit Tests
   │
   ▼
Integration Tests
   │
   ▼
Retrieval Tests
   │
   ▼
Golden Corpus
   │
   ▼
Build Docker
   │
   ▼
Security Scan
   │
   ▼
Deploy Staging
   │
   ▼
Smoke Test
   │
   ▼
Production
```

---

# 17.47 Quality Gate

Deployment **ditolak** jika:

```text
Unit tests fail
```

atau:

```text
Citation validity turun drastis
```

atau:

```text
Recall@5 turun melewati threshold
```

atau:

```text
security scan critical vulnerability
```

---

# 17.48 Staging Environment

Pisahkan:

```text
development
staging
production
```

Database juga harus terpisah.

Jangan:

```text
developer laptop
       ↓
production database
```

---

# 17.49 Production Topology

Untuk deployment awal:

```text
                    VPS / Cloud
                         │
              ┌──────────┴──────────┐
              │                     │
           Web/API                Worker
              │                     │
              └──────────┬──────────┘
                         │
                   Managed DB
                         │
                    PostgreSQL
                         │
                    Object Store
```

Kemudian ketika traffic meningkat:

```text
Load Balancer
      │
 ┌────┼────┐
 ▼    ▼    ▼
API1 API2 API3
 │    │    │
 └────┼────┘
      │
    Redis
      │
 Workers
```

---

# 17.50 Jangan gunakan Kubernetes dulu

Untuk tahap awal:

> **Docker Compose / single-server deployment lebih masuk akal.**

Kubernetes baru diperlukan ketika kompleksitas dan kebutuhan scaling memang membenarkannya.

Jangan membuat:

```text
Kubernetes
Kafka
Elasticsearch
Neo4j
Airflow
Ray
```

sekaligus sejak hari pertama.

Itu akan meningkatkan operational burden secara drastis.

---

# 17.51 MVP Production Stack

Saya sarankan:

```text
Next.js
+
FastAPI
+
PostgreSQL
+
pgvector
+
Redis
+
Celery
+
S3
+
Docker
+
Caddy
```

Ini sudah sangat kuat untuk versi pertama.

---

# 17.52 Deployment Flow

```text
Developer
    │
    ▼
Git Repository
    │
    ▼
CI
    │
    ▼
Docker Image
    │
    ▼
Container Registry
    │
    ▼
Production Server
    │
    ├── Web
    ├── API
    ├── Worker
    ├── Redis
    └── Monitoring
```

---

# 17.53 Health Checks

API:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

Tetapi buat juga:

```http
GET /ready
```

yang memeriksa:

```text
PostgreSQL
Redis
Object Storage
```

---

# 17.54 Job Monitoring

Dashboard:

```text
CORPUS PROCESSING

Volume 1
██████████████████░░ 92%

OCR
✓ 520/520

Normalization
✓ 520/520

Section detection
✓ 520/520

Hadith matching
████████████░░ 390/520

Embedding
queued
```

---

# 17.55 Admin Dashboard

Menu:

```text
Dashboard

Corpus
 ├── Books
 ├── Volumes
 ├── Pages
 └── Processing Jobs

Hadith
 ├── Collections
 ├── Hadith
 └── Variants

Fathul Bari
 ├── Sections
 ├── Sharh
 └── References

Matching
 ├── Candidates
 ├── Review Queue
 └── Verified

Knowledge Graph

Research
 ├── Queries
 ├── Runs
 └── Evaluations

System
 ├── Users
 ├── Audit
 ├── Jobs
 └── Health
```

---

# 17.56 User Dashboard

Untuk pengguna biasa:

```text
┌────────────────────────────────────────────┐
│ FATHUL BARI RESEARCH AI                   │
├────────────────────────────────────────────┤
│                                            │
│ Apa yang ingin Anda teliti?                │
│                                            │
│ [_______________________________] 🔍       │
│                                            │
│ ○ Ringkas                                  │
│ ○ Syarah Mendalam                          │
│ ● Research                                 │
│                                            │
│ Sumber: Fathul Bari                       │
│                                            │
└────────────────────────────────────────────┘
```

---

# 17.57 Research Result UI

```text
┌──────────────────────────────────────────────┐
│ HASIL PENELITIAN                            │
├──────────────────────────────────────────────┤
│                                              │
│ Jawaban                                      │
│                                              │
│ ...                                          │
│                                              │
│ [FB 1:45] [FB 1:46]                          │
│                                              │
├──────────────────────────────────────────────┤
│ Evidence                                     │
│                                              │
│ ✓ Direct Sharh                               │
│ ✓ Hadith                                    │
│ ✓ Cross Reference                           │
│                                              │
├──────────────────────────────────────────────┤
│ Confidence: HIGH                            │
└──────────────────────────────────────────────┘
```

---

# 17.58 Source Viewer

Klik:

```text
[FB 1:45]
```

membuka:

```text
┌───────────────────────┬──────────────────────┐
│ PAGE 45               │ EXTRACTED TEXT       │
├───────────────────────┼──────────────────────┤
│                       │                      │
│     PDF IMAGE         │ قال الحافظ...        │
│                       │                      │
│      █████            │ [highlight]          │
│                       │                      │
└───────────────────────┴──────────────────────┘
```

---

# 17.59 Production Security Checklist

```text
[ ] HTTPS
[ ] Secure cookies
[ ] Password hashing
[ ] JWT/session expiration
[ ] RBAC
[ ] Rate limiting
[ ] CORS restriction
[ ] CSRF protection where applicable
[ ] Input validation
[ ] SQL injection protection
[ ] File upload validation
[ ] Maximum PDF size
[ ] Malware scanning
[ ] Secrets outside repository
[ ] Database encryption at rest
[ ] Backup
[ ] Audit logs
```

---

# 17.60 File Upload Security

Karena aplikasi menerima PDF:

```text
Upload
 ↓
Validate MIME
 ↓
Validate extension
 ↓
Size limit
 ↓
Checksum
 ↓
Malware scan
 ↓
Object storage
 ↓
Processing queue
```

Jangan langsung menjalankan parser terhadap file upload yang belum divalidasi.

---

# 17.61 Data Integrity

Setiap sumber:

```text
SHA256
```

Setiap page:

```text
source_file_id
+
page_number
```

Setiap chunk:

```text
source_page_id
+
character span
```

Sehingga:

```text
Answer
 ↓
Claim
 ↓
Evidence
 ↓
Chunk
 ↓
Page
 ↓
PDF
```

selalu dapat ditelusuri kembali.

---

# 17.62 Reproducibility

Research run harus dapat direproduksi.

Simpan:

```text
query
source scope
retrieval version
embedding version
reranker version
prompt version
model version
evidence IDs
```

Dengan begitu:

```text
Research Run #123
```

tetap dapat diaudit meskipun model AI berubah di masa depan.

---

# 17.63 Definition of Done — Stage 17

```text
[ ] Monorepo
[ ] Next.js frontend
[ ] FastAPI backend
[ ] PostgreSQL
[ ] pgvector
[ ] Redis
[ ] Worker queue
[ ] Object storage
[ ] Database migrations
[ ] Ahmad Sanusi adapter
[ ] Corpus processing jobs
[ ] RAG API
[ ] Research API
[ ] Review API
[ ] Source Viewer API
[ ] Authentication
[ ] RBAC
[ ] Audit logging
[ ] Rate limiting
[ ] Health checks
[ ] Structured logging
[ ] Metrics
[ ] Docker development
[ ] Docker production
[ ] CI/CD
[ ] Backup
[ ] Staging
[ ] Production deployment
[ ] Security hardening
```

---

# 17.64 Milestone setelah Stage 17

Pada titik ini arsitektur kita sudah berubah dari konsep menjadi:

```text
                 ┌────────────────────┐
                 │      FRONTEND      │
                 │      Next.js       │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │      FASTAPI       │
                 │     REST + SSE     │
                 └─────────┬──────────┘
                           │
       ┌───────────────────┼────────────────────┐
       ▼                   ▼                    ▼
 PostgreSQL             Redis               Storage
 + pgvector               │                    │
       │                   ▼                    │
       │                Workers                 │
       │                   │                    │
       └──────────┬────────┴────────────────────┘
                  ▼
          RESEARCH ENGINE
                  │
       ┌──────────┼───────────┐
       ▼          ▼           ▼
     NLP       Matching      RAG
       │          │           │
       └──────────┼───────────┘
                  ▼
           KNOWLEDGE GRAPH
                  │
                  ▼
        CITATION / AUDIT LAYER
                  │
                  ▼
         FATHUL BARI AI
```

---

# 17.65 Urutan Implementasi Nyata

Jangan mengimplementasikan semuanya sekaligus.

Urutan coding yang paling aman:

```text
PHASE A
Repository + Docker
        ↓
PHASE B
PostgreSQL + migrations
        ↓
PHASE C
FastAPI foundation
        ↓
PHASE D
Ahmad Sanusi adapter
        ↓
PHASE E
Corpus upload + storage
        ↓
PHASE F
PDF processing worker
        ↓
PHASE G
Hadith matching
        ↓
PHASE H
Search + pgvector
        ↓
PHASE I
Review Dashboard
        ↓
PHASE J
Source Viewer
        ↓
PHASE K
RAG Assistant
        ↓
PHASE L
Research Mode
        ↓
PHASE M
Knowledge Graph
        ↓
PHASE N
Audit + observability
        ↓
PHASE O
Production deployment
```

**Ini yang akan kita gunakan sebagai implementation roadmap**, sehingga kita tidak terjebak membangun Knowledge Graph atau agent yang kompleks sebelum ingestion dan data integrity benar-benar stabil.

---
