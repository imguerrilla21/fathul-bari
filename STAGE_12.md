# Stage 12 — Production Architecture

```text
                         INTERNET
                            │
                            ▼
                    ┌───────────────┐
                    │ Reverse Proxy │
                    │ HTTPS / TLS   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Frontend    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ API Gateway   │
                    │ Auth / Rate   │
                    │ Limit / CORS  │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        FastAPI API      RAG Service    Admin API
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    ┌───────────────┐
                    │ PostgreSQL    │
                    │ + pgvector    │
                    └───────────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Object Storage    Redis        Worker Queue
        PDF / Images      Cache        OCR / Embedding
```

---

# 1. Authentication

Jangan lagi menggunakan endpoint terbuka seperti:

```http
POST /api/v1/review/links/{id}/verify
```

tanpa identitas.

Gunakan:

```text
User
 ↓
Login
 ↓
Access Token
 ↓
API
```

Contoh:

```http
POST /api/v1/auth/login
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Untuk production, gunakan **short-lived access token** dan mekanisme refresh yang aman.

---

# 2. Role-Based Access Control

Minimal empat role:

```text
READER
RESEARCHER
REVIEWER
ADMIN
```

### Reader

Boleh:

```text
✓ Search
✓ Read Hadith
✓ Read Syarah
✓ Ask AI
✓ View sources
```

Tidak boleh:

```text
✗ Verify
✗ Reject
✗ Modify corpus
```

### Researcher

Tambahan:

```text
✓ Research Workspace
✓ Notes
✓ Citations
✓ Export
```

### Reviewer

Tambahan:

```text
✓ Verify
✓ Reject
✓ Annotate
✓ Resolve quality issues
```

### Admin

Tambahan:

```text
✓ User management
✓ Dataset management
✓ System configuration
✓ Model configuration
✓ Audit
```

---

# 3. Authorization Matrix

```text
                     Reader Researcher Reviewer Admin
-------------------------------------------------------
Read Hadith             ✓       ✓          ✓       ✓
Search                  ✓       ✓          ✓       ✓
AI Assistant            ✓       ✓          ✓       ✓
Research Workspace      -       ✓          ✓       ✓
Create Notes            -       ✓          ✓       ✓
Verify Evidence         -       -          ✓       ✓
Reject Evidence         -       -          ✓       ✓
Manage Dataset          -       -          -       ✓
Manage Users            -       -          -       ✓
System Settings         -       -          -       ✓
```

---

# 4. Audit Trail menjadi immutable

Audit Trail Stage 6 sekarang harus diperkuat.

Jangan izinkan:

```text
UPDATE audit_logs
DELETE audit_logs
```

Audit log harus append-only.

```text
Action
  ↓
Audit Event
  ↓
INSERT
  ↓
Never modify
```

Contoh:

```json
{
  "actor_id": "user_123",
  "action": "VERIFY_LINK",
  "entity_type": "hadith_sharh_link",
  "entity_id": "link_1571",
  "before_state": {
    "verified": false
  },
  "after_state": {
    "verified": true
  },
  "timestamp": "...",
  "ip_hash": "...",
  "request_id": "..."
}
```

---

# 5. Audit Event Types

Gunakan enum:

```text
LOGIN
LOGOUT

CREATE_PROJECT
UPDATE_PROJECT

VERIFY_LINK
REJECT_LINK

CREATE_ANNOTATION
UPDATE_ANNOTATION

CREATE_SOURCE
UPDATE_SOURCE

RUN_RETRIEVAL
RUN_RAG

EXPORT_RESEARCH

ADMIN_CHANGE
USER_ROLE_CHANGE
```

Dengan demikian aktivitas penting dapat ditelusuri.

---

# 6. API Security

Tambahkan:

```text
HTTPS
CORS
CSRF protection
Rate limiting
Input validation
Request size limits
Security headers
JWT validation
Password hashing
Secret management
```

FastAPI/Pydantic digunakan untuk memastikan input tidak langsung dipercaya.

Contoh:

```text
User Input
   ↓
Pydantic Schema
   ↓
Validation
   ↓
Business Logic
   ↓
Database
```

---

# 7. Rate Limiting

AI endpoint biasanya paling mahal.

Misalnya:

```text
/api/v1/assistant/query
```

jangan bebas dipanggil tanpa batas.

Contoh kebijakan:

```text
Reader:
20 AI requests/hour

Researcher:
100 AI requests/hour

Reviewer:
200 AI requests/hour

Admin:
custom
```

Angka ini adalah contoh awal dan harus disesuaikan setelah melihat penggunaan nyata.

---

# 8. AI Cost Control

Setiap request AI dicatat:

```text
user_id
model
input_tokens
output_tokens
latency
retrieval_count
cost_estimate
```

Dashboard:

```text
AI USAGE

Requests today       1,247
Tokens               8.2M
Average latency      2.4s
Failed requests      13
Estimated cost       ...
```

Dengan ini kita dapat mengetahui model mana yang terlalu mahal.

---

# 9. Prompt Versioning

Ini **sangat penting**.

Jangan menyimpan prompt hanya di source code.

Buat:

```text
prompt_templates
```

Contoh:

```json
{
  "name": "fathul_bari_assistant",
  "version": "3.2",
  "system_prompt": "...",
  "active": true
}
```

Setiap jawaban AI mencatat:

```text
model_version
prompt_version
retrieval_version
embedding_version
```

Jadi jika hasil AI berubah enam bulan kemudian, kita tahu **mengapa**.

---

# 10. RAG Versioning

Sama untuk retrieval:

```text
retrieval_v1
retrieval_v2
retrieval_v3
```

Contoh:

```json
{
  "retriever_version": "hybrid-v2",
  "embedding_model": "...",
  "reranker_model": "...",
  "top_k": 10
}
```

Ini sangat penting untuk penelitian reproducibility.

---

# 11. Data Versioning

Dataset Fathul Bari jangan dianggap statis.

Buat:

```text
dataset_versions
```

Contoh:

```text
FATHUL-BARI-2026-08-001
FATHUL-BARI-2026-09-002
```

Setiap version mencatat:

```text
source
edition
import date
OCR version
normalization version
matching version
verified count
```

---

# 12. Source File Storage

Jangan menyimpan PDF besar langsung dalam PostgreSQL.

Gunakan:

```text
PostgreSQL
    │
    └── metadata
          │
          ▼
     Object Storage
          │
     ┌────┼────┐
     ▼    ▼    ▼
    PDF  JPG  OCR
```

Struktur:

```text
sources/
  fathul-bari/
    edition-001/
      volume-01/
        original.pdf
        pages/
        ocr/
      volume-02/
        original.pdf
```

Database hanya menyimpan:

```text
object_key
checksum
mime_type
size
page_count
```

---

# 13. Checksum

Setiap sumber diberi SHA-256:

```text
PDF
 ↓
SHA-256
 ↓
checksum
```

Contoh:

```json
{
  "filename": "fathul-bari-vol-01.pdf",
  "sha256": "...",
  "size": 123456789
}
```

Ini memastikan file sumber dapat diverifikasi.

---

# 14. Background Workers

OCR dan embedding jangan dilakukan dalam request HTTP.

Jangan:

```text
POST /upload
     ↓
OCR 30 menit
     ↓
HTTP response
```

Gunakan:

```text
Upload
  ↓
Job Queue
  ↓
Worker
  ↓
OCR
  ↓
Chunking
  ↓
Embedding
  ↓
Indexing
```

Arsitektur:

```text
FastAPI
   │
   ▼
Redis / Queue
   │
   ├── OCR Worker
   ├── Embedding Worker
   ├── Graph Worker
   └── Evaluation Worker
```

---

# 15. Job Status

Frontend:

```text
IMPORTING FATHUL BARI

██████████████░░░░░░ 72%

OCR                  ✓
Normalization        ✓
Chunking             ✓
Embedding            ███████░░
Indexing             pending
Knowledge Graph      pending
```

API:

```http
GET /api/v1/jobs/{job_id}
```

Response:

```json
{
  "status": "running",
  "progress": 72,
  "stage": "embedding"
}
```

---

# 16. Database Backup

Production wajib memiliki:

```text
Daily backup
Weekly backup
Off-site backup
Backup verification
```

Minimal:

```text
PostgreSQL
   │
   ├── Daily
   ├── Weekly
   └── Monthly
```

Backup tidak dianggap berhasil hanya karena file berhasil dibuat.

Harus ada:

```text
Backup
 ↓
Restore test
 ↓
Verify
```

---

# 17. Disaster Recovery

Dokumentasikan:

```text
RPO
RTO
```

Contoh target awal:

```text
RPO: 24 jam
RTO: 4 jam
```

Kemudian bisa ditingkatkan sesuai kebutuhan.

---

# 18. Observability

Tambahkan tiga lapisan:

```text
Logs
Metrics
Traces
```

### Logs

```text
ERROR
WARNING
INFO
```

### Metrics

```text
API latency
DB latency
RAG latency
Queue length
Error rate
CPU
RAM
Storage
```

### Tracing

Satu request:

```text
Request
 ↓
API
 ↓
Retriever
 ↓
PostgreSQL
 ↓
Reranker
 ↓
LLM
 ↓
Response
```

Kita bisa mengetahui bottleneck.

---

# 19. Health Checks

Tambahkan:

```http
GET /health
GET /ready
```

Contoh:

```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "vector_store": "ok",
  "storage": "ok"
}
```

Khusus `/ready`, service hanya dianggap siap jika dependency penting tersedia.

---

# 20. Production Docker

Development:

```text
docker-compose.yml
```

Production:

```text
docker-compose.production.yml
```

Service:

```text
frontend
backend
worker
scheduler
postgres
redis
reverse-proxy
```

---

# 21. CI/CD

Pipeline:

```text
Git Push
   │
   ▼
CI
   │
   ├── Lint
   ├── Unit Tests
   ├── Integration Tests
   ├── Security Scan
   └── Build
          │
          ▼
       Docker Image
          │
          ▼
      Staging
          │
       Approval
          │
          ▼
     Production
```

Jangan deploy langsung dari laptop ke production.

---

# 22. Testing Strategy

Minimal:

```text
tests/
├── unit/
├── integration/
├── retrieval/
├── rag/
├── security/
└── e2e/
```

### Unit

```text
normalization
confidence
citation
graph
```

### Integration

```text
API + DB
API + Redis
RAG + retrieval
```

### Retrieval

```text
Recall@5
MRR
NDCG
```

### RAG

```text
groundedness
citation correctness
```

### E2E

```text
Login
 → Search
 → Ask AI
 → Open citation
 → Source Viewer
```

---

# 23. Security Testing

Tambahkan pengujian:

```text
SQL injection
XSS
CSRF
Broken authorization
JWT manipulation
File upload abuse
Path traversal
Rate-limit bypass
Prompt injection
```

Khusus RAG, kita harus mengantisipasi **prompt injection dari dokumen**.

Misalnya teks sumber mengandung instruksi seperti:

> Ignore previous instructions...

LLM harus memperlakukannya sebagai **data**, bukan instruksi.

---

# 24. RAG Security Boundary

Arsitektur:

```text
                  SOURCE DOCUMENT
                         │
                         ▼
                   UNTRUSTED DATA
                         │
                         ▼
                    RETRIEVER
                         │
                         ▼
                   EVIDENCE BLOCK
                         │
                         ▼
                      LLM
                         │
                  SYSTEM RULES
                         │
                         ▼
                       ANSWER
```

System prompt harus selalu memiliki prioritas lebih tinggi daripada isi dokumen.

---

# 25. Admin Dashboard

Stage 12 menambahkan:

```text
/admin
```

Menu:

```text
Dashboard
Users
Roles
Datasets
Sources
Jobs
RAG Models
Prompts
Evaluation
Audit Logs
System Health
```

---

# 26. Security Dashboard

```text
┌────────────────────────────────────────────┐
│ SECURITY                                   │
├────────────────────────────────────────────┤
│ Failed login attempts        17            │
│ Rate limit violations         4            │
│ Suspicious requests           2            │
│ Unauthorized API attempts     3            │
│ Active sessions             184            │
├────────────────────────────────────────────┤
│ ✓ Database encryption                       │
│ ✓ HTTPS                                     │
│ ✓ Audit logging                             │
│ ✓ RBAC                                      │
└────────────────────────────────────────────┘
```

---

# 27. Production Environment

Pisahkan:

```text
.env.development
.env.staging
.env.production
```

Jangan commit secret ke Git.

Contoh:

```text
DATABASE_URL
JWT_SECRET
OPENAI_API_KEY
STORAGE_SECRET
REDIS_URL
```

Production secret sebaiknya disediakan melalui secret manager/environment platform, bukan ditulis dalam repository.

---

# 28. Deployment Architecture

Untuk deployment awal:

```text
                 Cloud VPS
                    │
             ┌──────┴──────┐
             │             │
          Reverse       Firewall
           Proxy
             │
             ▼
        Docker Network
             │
    ┌────────┼──────────┐
    ▼        ▼          ▼
 Frontend  Backend    Worker
              │
       ┌──────┴──────┐
       ▼             ▼
   PostgreSQL      Redis
       │
       ▼
 Object Storage
```

Kemudian ketika traffic meningkat:

```text
Load Balancer
      │
 ┌────┼────┐
 ▼    ▼    ▼
API  API  API
 │
 └──────► PostgreSQL
```

---

# 29. Final Production Flow

Setelah Stage 12:

```text
                         USER
                          │
                          ▼
                     HTTPS/TLS
                          │
                          ▼
                     FRONTEND
                          │
                          ▼
                  AUTH + RBAC
                          │
                          ▼
                    API GATEWAY
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       SEARCH          RAG AI          RESEARCH
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                  KNOWLEDGE GRAPH
                          │
                          ▼
                    VERIFIED DATA
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         PostgreSQL             Object Storage
              │                       │
              ▼                       ▼
          Audit Trail            PDF / Images
```

---

# 30. Governance Layer

Ada satu lapisan tambahan yang saya rekomendasikan untuk aplikasi ini:

```text
                 CONTENT GOVERNANCE
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Source Policy    AI Policy       Reviewer Policy
```

### Source Policy

Menentukan:

```text
sumber mana yang authoritative
edisi mana yang digunakan
bagaimana perbedaan edisi dicatat
```

### AI Policy

Menentukan:

```text
kapan AI boleh menjawab
kapan harus mengatakan "tidak ditemukan"
bagaimana citation diwajibkan
```

### Reviewer Policy

Menentukan:

```text
kapan VERIFY
kapan REJECT
kapan membutuhkan second reviewer
```

Ini sangat penting karena aplikasi menyangkut **teks keagamaan dan karya ulama**.

---

# 31. Definition of Done — Stage 12

Stage 12 dianggap selesai apabila:

```text
[ ] HTTPS aktif
[ ] Authentication aktif
[ ] RBAC aktif
[ ] API rate limiting aktif
[ ] Audit log immutable
[ ] Database backup otomatis
[ ] Restore test berhasil
[ ] Object storage aktif
[ ] Background worker aktif
[ ] Health check aktif
[ ] Monitoring aktif
[ ] Error tracking aktif
[ ] Prompt versioning aktif
[ ] RAG versioning aktif
[ ] Dataset versioning aktif
[ ] CI/CD aktif
[ ] Security tests berjalan
[ ] Retrieval evaluation berjalan
[ ] RAG evaluation berjalan
[ ] Production Docker image berhasil
[ ] Staging environment tersedia
[ ] Disaster recovery procedure terdokumentasi
```

## Roadmap besar kita sekarang

```text
01 Foundation
        ↓
02 Ahmad Sanusi Hadits API
        ↓
03 Hadith + Sharh Data Model
        ↓
04 Matching Engine
        ↓
05 Review Dashboard
        ↓
06 Source Viewer + Audit Trail
        ↓
07 RAG / Syarah AI Assistant
        ↓
08 Arabic Hybrid Search
        ↓
09 Knowledge Graph
        ↓
10 Multi-Volume + Research Workspace
        ↓
11 Research Analytics + Quality Control
        ↓
12 Production Hardening
        ↓
        ┌─────────────────────────────┐
        │ FATHUL BARI RESEARCH AI    │
        │                             │
        │ Search                     │
        │ Syarah AI                  │
        │ Knowledge Graph            │
        │ Source Verification        │
        │ Research Workspace         │
        │ Citation                   │
        │ Audit Trail                │
        │ Analytics                  │
        └─────────────────────────────┘
```
