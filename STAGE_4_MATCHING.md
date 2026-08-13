# Tahap 4 — Hadith–Sharh Matching Engine

Mesin v1 deterministic dan audit-friendly.

## Formula
`final = number_score*0.50 + text_score*0.35 + context_score*0.15`

Context score masih 0 sampai metadata kitab/bab tersedia.

## Threshold
- >= 0.90: auto_candidate
- 0.75–0.89: review
- 0.50–0.74: weak_match
- < 0.50: reject

`auto_candidate` bukan verifikasi manusia.

## API
- `GET /api/v1/matching/sharh/{sharh_id}/candidates`
- `POST /api/v1/matching/sharh/{sharh_id}/persist`
- `GET /api/v1/matching/links?minimum_confidence=0.75`
- `POST /api/v1/matching/links/{link_id}/verify`
- `POST /api/v1/matching/links/{link_id}/reject`

## CLI
```bash
docker compose exec backend python scripts/run_matching.py --sharh-id UUID --top-k 10
```

Simpan hasil:
```bash
docker compose exec backend python scripts/run_matching.py --sharh-id UUID --top-k 10 --persist
```
