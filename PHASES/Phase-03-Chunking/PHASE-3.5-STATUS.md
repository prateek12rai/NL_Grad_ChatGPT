# Phase 3.5 — Chunk Identity & Metadata — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [architecture-phase-3-chunking.md](../../docs/architecture-phase-3-chunking.md) §11 |
| **Cost** | **$0** — local SHA-256 + Pydantic only |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `shared/schemas.py` → `ChunkRecord` | Disk JSONL contract (all PRD fields) |
| `pipeline/chunking/metadata.py` | `chunk_id`, `content_hash`, `drafts_to_chunk_records()` |
| `document_to_chunk_records()` | Full 3.1–3.5 chain for one manifest row |

## Rules enforced

- **`chunk_id`:** `{document_id}::p{page:04d}::c{index:04d}` — index resets each page
- **`verification_status`:** always `unverified` at creation
- **`publication_year`:** from manifest `publication_date`
- **`content_hash`:** SHA-256 of verbatim `exact_context`
- **Idempotency:** same inputs → same `chunk_id` set (gate 3.6.4)

## Tests

| File | Gate |
|------|------|
| `tests/phase3/test_chunk_records.py` | 3.6.3 metadata completeness |
| `tests/phase3/test_idempotency.py` | 3.6.4 identical chunk_id set |

## Verify

```powershell
$env:PYTHONPATH="src"
pytest tests/phase3/test_chunk_records.py tests/phase3/test_idempotency.py -v
```

## Next

**Phase 3.6** — CLI `python -m pipeline.chunking.run`, write `data/chunks/*.jsonl` + `index.json`
