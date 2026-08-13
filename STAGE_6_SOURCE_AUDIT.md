# Tahap 6 — Source Viewer & Audit Trail

Tahap ini membuat setiap keputusan penelitian dapat ditelusuri ke sumber primer yang disimpan/ditautkan di server.

## Fitur

- metadata volume, halaman PDF, halaman cetak;
- tautan PDF sumber;
- image viewer untuk halaman PDF yang telah dirender;
- audit trail immutable-style (append-only dari aplikasi);
- actor/reviewer;
- timestamp;
- request ID;
- before/after state;
- catatan keputusan;
- audit API.

## URL

```text
http://localhost:8000/source-viewer/
```

## Menautkan sumber

Isi `sharh_sections.source_document_path` dengan path file di container backend, misalnya:

```text
/app/data/fathul-bari/vol-01.pdf
```

Untuk halaman yang sudah dirender:

```text
/app/data/fathul-bari/vol-01/page-0045.png
```

Pastikan folder tersebut dimount ke container `backend`.

## API

```text
GET /api/v1/source/sharh/{sharh_id}
GET /api/v1/source/sharh/{sharh_id}/document
GET /api/v1/source/sharh/{sharh_id}/page-image
GET /api/v1/source/audit/sharh_section/{sharh_id}
```

Reviewer dapat mengirim:

```text
X-Reviewer: nama-reviewer
X-Request-ID: UUID-request
```

pada Verify/Reject agar audit trail mencatat siapa dan dari request mana keputusan berasal.

## Migration

```bash
docker compose exec backend alembic upgrade head
```

## Catatan integritas

Audit log tidak boleh diedit melalui UI. Jika nanti diperlukan koreksi, buat event baru seperti `CORRECTION`/`SUPERSEDE`, bukan mengubah event lama.
