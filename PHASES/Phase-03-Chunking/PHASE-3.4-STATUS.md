# Phase 3.4 — Token Cap & Overlap — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [architecture-phase-3-chunking.md](../../docs/architecture-phase-3-chunking.md) §10 |
| **Cost** | **$0** — local `tiktoken` only |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `tokenization/overlap.py` | 80-token tail prefix between chunks |
| `tokenization/chunk_enforcer.py` | 512 hard cap + bounded overlap |
| `ChunkDraft` model | `exact_context` + `token_count` per chunk |
| `units_to_chunk_drafts()` | TextUnits → final chunk texts |

## Rules enforced

- **Max 512 tokens** per `exact_context` (including overlap prefix)
- **80-token overlap** from previous chunk
- Sentence-boundary splits; token-window fallback for huge sentences

## Tests

| File | Purpose |
|------|---------|
| `tests/phase3/test_token_limits.py` | 512 cap, multi-chunk split, PDF pipeline |
| `tests/phase3/test_overlap_fixture.py` | 80-token overlap + Bedaquiline phrase |
| `tests/fixtures/phase3/contraindication_overlap.txt` | Overlap fixture text |

**Result:** 42/42 `tests/phase3/` passed (2026-06-01).

## Verify

```powershell
$env:PYTHONPATH="src"
pytest tests/phase3/ -v
python scripts/chunk_preview.py
```

## Next

**Phase 3.5** — `chunk_id`, manifest fields, `verification_status`
