# Phase 4.1 — Hugging Face BGE Client — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [architecture-phase-4-embedding.md](../../docs/architecture-phase-4-embedding.md) §7 |
| **Cost** | **$0** on HF free tier (live) · **$0** mock for dev/CI |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `pipeline/embeddings/bge_client.py` | `BgeEmbeddingClient` — `embed_passages`, `embed_query` |
| `pipeline/embeddings/batch_planner.py` | Batch size + 24k char budget |
| `pipeline/embeddings/exceptions.py` | Auth / rate-limit errors |
| `shared/config.py` | `EMBED_*`, `bge_dimension` settings |

## Behavior

- **Model:** `BAAI/bge-large-en-v1.5` via `huggingface_hub.InferenceClient`
- **Prefixes:** `passage: ` for chunks, `query: ` for search (Phase 5)
- **Retries:** 3× exponential backoff on 429 / 503
- **Mock:** `EMBED_MOCK=true` → deterministic 1024-d vectors (no network)

## Tests

| File | Gate |
|------|------|
| `tests/phase4/test_bge_client_mock.py` | 4.6.1 dimension (mock) |
| `tests/phase4/test_bge_live.py` | Optional `@pytest.mark.live` |

```powershell
$env:PYTHONPATH="src"
pytest tests/phase4/ -m "not live" -v
```

## Next

**Phase 4.2** — L2 normalization (`normalize.py`) — **DONE**
