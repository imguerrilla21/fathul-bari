# Fathul Bari Research — Starter Project

Starter project untuk membangun aplikasi penelitian hadis dan syarah Fathul Bari.

## Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- httpx
- Ahmad Sanusi Hadits API
- Docker Compose
- HTML/JS frontend sederhana (tanpa build tool)

## Fitur starter

- Health check
- Hadis dari database lokal
- Proxy sync ke Ahmad Sanusi API
- Import hadis per nomor
- Retry + exponential backoff
- Content hash
- Sync run logging
- Data quality report
- Search hadis lokal
- Struktur database siap dikembangkan untuk Fathul Bari

## 1. Setup

Copy environment:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` dan masukkan API key Ahmad Sanusi milik Anda.

## 2. Start

```bash
docker compose up --build -d
```

## 3. Migration + seed

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed.py
```

## 4. Import test

Import 10 hadis:

```bash
docker compose exec backend python scripts/sync_bukhari.py --start 1 --end 10
```

Validasi:

```bash
docker compose exec backend python scripts/validate_bukhari.py
```

## 5. API

- http://localhost:8000
- http://localhost:8000/health
- http://localhost:8000/docs
- http://localhost:8000/api/v1/hadith/shahih_bukhari/1
- http://localhost:8000/api/v1/hadith/search?q=niat
- http://localhost:8000/api/v1/admin/data-quality

## 6. Frontend

Buka:

http://localhost:8000/ui/

## 7. Import seluruh Bukhari

Setelah pengujian berhasil:

```bash
docker compose exec backend python scripts/sync_bukhari.py --start 1 --end 7008
```

Jangan melakukan paralel request besar-besaran. Sync engine memakai delay dan retry.

## Arsitektur

```text
Browser
   |
   v
FastAPI
   |
   +------> PostgreSQL
   |
   +------> Ahmad Sanusi API
                |
                v
          Sync / Import
                |
                v
            PostgreSQL

Fathul Bari PDF
       |
       v
[future extraction pipeline]
       |
       v
sharh_sections
       |
       v
hadith_sharh_links
       |
       v
hadiths
```

## Roadmap

1. Import + validation Bukhari
2. Fathul Bari PDF extraction
3. Arabic OCR/text normalization
4. Hadith reference detection
5. Hadith–Sharh linking
6. Full-text search
7. RAG/research assistant
8. Citation/provenance viewer
9. User accounts and annotations
