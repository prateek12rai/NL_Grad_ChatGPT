# Phase 3 — Gate Report

| Field | Value |
|-------|--------|
| **Date** | 2026-06-01 |
| **Decision** | **PASS — PROCEED TO PHASE 4** |
| **Tests** | 89 (phase1 + phase2 + phase3) |

## Deep test summary

| ID | Item | Result |
|----|------|--------|
| 3.6.1 | Token ceiling (≤512) | PASS — `test_token_limits.py` |
| 3.6.2 | Overlap integrity | PASS — `test_overlap_fixture.py` |
| 3.6.3 | Metadata completeness | PASS — `test_chunk_records.py` |
| 3.6.4 | Idempotency | PASS — `test_idempotency.py` |
| 3.6.5 | Regression (Phases 1–2) | PASS — 89 total |
| 3.6.6 | Gate report | PASS — this file + `docs/phase-reports/phase-3-gate.md` |

## Corpus chunking (real manifest)

```
python -m pipeline.chunking.run --manifest data/manifest.json --no-incremental
```

| Outcome | Count |
|---------|-------|
| HTML chunked | 2 (Nature) |
| PDF extract_error | 4 (mock PDFs from Phase 2 fixtures) |
| `index.json` total_chunks | 2 |

## Try it yourself

```powershell
cd C:\Users\Acer\Downloads\NL_Grad_ChatGPT
$env:PYTHONPATH="src"
pytest tests/phase3/ -v
python -m pipeline.chunking.run
```

Sample chunk file: `data/chunks/sha256_897f356f852ac50d.jsonl`
