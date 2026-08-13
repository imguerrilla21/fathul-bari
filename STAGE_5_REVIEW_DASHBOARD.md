# Tahap 5 — Review Dashboard

Dashboard untuk memverifikasi hubungan **Hadis → Syarah Fathul Bari → halaman sumber → confidence**.

## URL

`http://localhost:8000/review/`

## API

- `GET /api/v1/review/queue`
- `GET /api/v1/review/links/{link_id}`
- `POST /api/v1/review/links/{link_id}/verify`
- `POST /api/v1/review/links/{link_id}/reject`

Filter queue: `status=pending|verified|all`, `minimum_confidence`, `maximum_confidence`.

## Alur reviewer

1. Pilih kandidat.
2. Baca matan hadis.
3. Baca syarah.
4. Periksa volume dan halaman.
5. Periksa confidence dan evidence.
6. Verify atau Reject.
7. Copy Citation bila diperlukan.

`confidence` adalah skor mesin; `verified=true` adalah keputusan reviewer manusia.
