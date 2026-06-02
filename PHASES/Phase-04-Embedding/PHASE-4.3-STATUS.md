# Phase 4.3 — Chroma PersistentClient — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [architecture-phase-4-embedding.md](../../docs/architecture-phase-4-embedding.md) §9 |
| **Cost** | **$0** — local `chroma_db/` on disk |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `pipeline/index/chroma_store.py` | `PersistentClient`, `get_medical_collection`, `ChromaStore` |
| `pipeline/index/mapper.py` | `ChunkRecord` → Chroma `ids` / `embeddings` / `metadatas` |
| `shared/chroma_client.py` | Thin wrapper for Phase 1 API health check |

## Collection

- **Name:** `india_medical_local` (`CHROMA_COLLECTION`)
- **Path:** `./chroma_db` (`CHROMA_PATH`)
- **Metadata:** `hnsw:space=cosine`, `schema_version=1`, `embedding_model=BAAI/bge-large-en-v1.5`
- **Upsert rule:** embeddings must be L2-normalized (Phase 4.2)

## Tests

| File | Covers |
|------|--------|
| `tests/phase4/test_chroma_store.py` | metadata, upsert, persistence, offline query |
| `tests/phase1/test_chroma_init.py` | regression (shared client) |

```powershell
$env:PYTHONPATH="src"
pytest tests/phase4/test_chroma_store.py tests/phase1/test_chroma_init.py -v
```

## Next

**Phase 4.4** — full indexer: read `data/chunks/`, upsert, prune cascade — **DONE**
