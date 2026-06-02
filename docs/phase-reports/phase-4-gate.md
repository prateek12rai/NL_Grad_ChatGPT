# Phase 4 — Deep Test Gate Report

| Field | Value |
|-------|--------|
| **Date** | 2026-06-01 |
| **Decision** | **PROCEED TO PHASE 5** |
| **Phase 4 tests** | 38 (36 unit + 2 deselected live) |
| **Regression (Phases 1–3)** | PASS |
| **Combined** | 127 passed (`-m "not live"`) |

## Checklist

- [x] **4.6.1** — Embedding dimensions consistent (1024 in mock / configurable live)
- [x] **4.6.2** — L2 normalized vectors (`|norm - 1| < 1e-5`)
- [x] **4.6.3** — Offline top-k retrieval (no remote vector DB)
- [x] **4.6.4** — Persistence after client reopen
- [x] **4.6.5** — Prune cascade deletes document vectors
- [x] **4.6.6** — Phases 1–3 regression pass
- [x] **4.6.7** — Gate reports committed

## Indexing pipeline

```powershell
set PYTHONPATH=src
set EMBED_MOCK=true
python -m pipeline.index.chroma_upsert
python scripts/verify_chroma.py
```

## Free & fast alignment

- **Chroma:** local disk only at query time  
- **HF Inference:** embed-time only (skipped via `content_hash`)  
- **Mock mode:** full offline dev without API keys  

## Handoff to Phase 5

- Import `retrieve` from `pipeline.index.retriever`  
- Groq answers on Streamlit using retrieved `exact_context` chunks  
- See [architecture.md](../architecture.md) §11
