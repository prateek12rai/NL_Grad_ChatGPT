# Phase 2 — Gate Report

| Field | Value |
|-------|--------|
| **Date** | 2026-06-01 |
| **Decision** | **PASS — PROCEED TO PHASE 3** |
| **Tests** | 10 phase2 + 1 regression (Phase 1) |

## Deep test summary

| # | Item | Result |
|---|------|--------|
| 2.7.1 | Adapter tests (HTML fixtures) | PASS |
| 2.7.2 | Ingest demo (fixture) | PASS — 6 documents |
| 2.7.3 | 1000 document cap | PASS |
| 2.7.4 | Nature 7-day URL in log | PASS |
| 2.7.5 | PII block | PASS |
| 2.7.6 | Phase 1 regression | PASS |
| 2.7.7 | Gate report | PASS |

## Sample data in your project

After fixture ingest you should see:

- `data/manifest.json` — catalog of downloaded items
- `data/ingest_log.jsonl` — audit log (includes Nature `last_7_days`)
- `data/corpus/dhr/`, `icmr/`, `nature/` — saved files

## Try it yourself (offline)

```powershell
cd C:\Users\Acer\Downloads\NL_Grad_ChatGPT
$env:PYTHONPATH="src"
python -m scraper.scheduler --fixture
```

For real websites (needs internet):

```powershell
python -m scraper.scheduler --live --max-per-source 3
```
