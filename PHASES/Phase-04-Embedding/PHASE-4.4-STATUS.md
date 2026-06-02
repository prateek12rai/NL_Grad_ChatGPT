# Phase 4.4 — Upsert, Delete & Prune Cascade — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [architecture-phase-4-embedding.md](../../docs/architecture-phase-4-embedding.md) §10 |
| **Cost** | **$0** mock / HF free tier live |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `index/orchestrator.py` | Load chunks, hash skip, embed, upsert, stats |
| `index/delete.py` | Prune cascade by `document_id` prefix |
| `index/loader.py` | Read `data/chunks/index.json` + JSONL |
| `index/embed_log.py` | `data/embed_log.jsonl` audit |
| `index/chroma_upsert.py` | CLI entry point |

## CLI

```powershell
$env:PYTHONPATH="src"
$env:EMBED_MOCK="true"
python -m pipeline.index.chroma_upsert
python -m pipeline.index.chroma_upsert --dry-run
python -m pipeline.index.chroma_upsert --prune-only
```

## Outputs

| File | Content |
|------|---------|
| `chroma_db/` | Upserted vectors + metadata |
| `data/chroma_stats.json` | Counts, last run, skip/embed/delete stats |
| `data/embed_log.jsonl` | Per-chunk / prune events |

## Rules

- Skip re-embed when stored `content_hash` matches Phase 3 chunk
- Reset `verification_status` to `unverified` when text changes
- Delete all `chunk_id` with prefix `{document_id}::` for pruned docs

## Tests

| File | Gate |
|------|------|
| `tests/phase4/test_chroma_upsert.py` | upsert, skip, dry-run, CLI |
| `tests/phase4/test_prune_cascade.py` | 4.6.5 prune cascade |

## Next

**Phase 4.5** — `scripts/verify_chroma.py` + operational checks — **DONE**
