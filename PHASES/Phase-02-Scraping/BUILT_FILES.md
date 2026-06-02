# Phase 2 — Files created (monitoring)

## Scraper code

| File | Purpose |
|------|---------|
| `src/scraper/scheduler.py` | Command to run ingest (`--fixture` or `--live`) |
| `src/scraper/orchestrator.py` | Coordinates all sources, PII, manifest, prune |
| `src/scraper/manifest.py` | `data/manifest.json` read/write |
| `src/scraper/pruner.py` | Keeps max 1000 documents |
| `src/scraper/downloader.py` | Saves PDF/HTML to `data/corpus/` |
| `src/scraper/ingest_log.py` | Writes `data/ingest_log.jsonl` |
| `src/scraper/adapters/dhr.py` | DHR publications parser |
| `src/scraper/adapters/icmr.py` | ICMR reports parser |
| `src/scraper/adapters/nature.py` | Nature search (7-day filter required) |

## Tests

| File | Purpose |
|------|---------|
| `tests/phase2/` | Phase 2 automated tests |
| `tests/fixtures/phase2/*.html` | Sample web pages for offline tests |
| `tests/regression/test_phase1_smoke.py` | Ensures Phase 1 still works |

## Data produced (after you run ingest)

| File | Purpose |
|------|---------|
| `data/manifest.json` | Master list of all documents |
| `data/ingest_log.jsonl` | One log line per action per run |
| `data/corpus/*/` | Actual downloaded files |

## CI

| File | Purpose |
|------|---------|
| `.github/workflows/test-phase2.yml` | Runs Phase 2 tests on GitHub |
