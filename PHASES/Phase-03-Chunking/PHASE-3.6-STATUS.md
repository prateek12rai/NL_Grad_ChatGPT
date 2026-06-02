# Phase 3.6 — Pipeline CLI & Disk Output — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [architecture-phase-3-chunking.md](../../docs/architecture-phase-3-chunking.md) §12 |
| **Cost** | **$0** — local CPU + disk |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `orchestrator.py` | Manifest loop, PII filter, incremental skip, prune cleanup |
| `run.py` | CLI `python -m pipeline.chunking.run` |
| `chunk_log.py` | Append-only `data/chunk_log.jsonl` |
| `writer.py` | Atomic JSONL / index / sidecar writes |

## CLI

```powershell
$env:PYTHONPATH="src"
python -m pipeline.chunking.run --manifest data/manifest.json
python -m pipeline.chunking.run --document-id sha256:897f356f852ac50d
python -m pipeline.chunking.run --incremental
python -m pipeline.chunking.run --force
```

## Outputs

| Path | Content |
|------|---------|
| `data/chunks/*.jsonl` | One `ChunkRecord` per line |
| `data/chunks/*.meta.json` | Sidecar for incremental skip |
| `data/chunks/index.json` | Document index for Phase 4 |
| `data/chunk_log.jsonl` | Audit events |

## Demo run (fixture corpus)

- **2** Nature HTML documents chunked successfully
- **4** mock PDFs logged as `extract_error` (Phase 2 placeholder files, not real PDFs)

## Tests

`tests/phase3/test_chunk_orchestrator.py` — index, incremental, force, PII, prune, CLI

**Full gate:** 89 tests (phase1 + phase2 + phase3) — see [GATE_REPORT.md](./GATE_REPORT.md)

## Next

**Phase 4** — BGE-large embeddings + Chroma ([architecture-phase-4-embedding.md](../../docs/architecture-phase-4-embedding.md))
