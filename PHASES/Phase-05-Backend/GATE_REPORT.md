# Phase 5 — Gate Report

| Field | Value |
|-------|--------|
| **Date** | 2026-06-01 |
| **Decision** | **PASS — PROCEED TO PHASE 6** |
| **Tests** | 137 (phases 1–5, excl. live) |

## Deep test summary

| ID | Item | Result |
|----|------|--------|
| 5.7.1 | Groq integration | PASS — mock client + optional live |
| 5.7.2 | Refusal test | PASS — empty Chroma → no fabricated answer |
| 5.7.3 | Model fallback | PASS — simulated 429 → second model |
| 5.7.4 | Retrieval latency | PASS — &lt; 500 ms on demo index |
| 5.7.5 | Export gate API | PASS — blocked until all citations verified |
| 5.7.6 | Streamlit Cloud deploy | MANUAL — run `streamlit run backend/streamlit_app.py` |
| 5.7.7 | CORS | PASS — localhost:5173 allowed |
| 5.7.8 | Regression | PASS — 137 tests |
| 5.7.9 | Gate report | PASS — this file + `docs/phase-reports/phase-5-gate.md` |

## REST API

| Method | Path |
|--------|------|
| `POST` | `/api/v1/query` |
| `GET` | `/api/v1/chunks/{chunk_id}` |
| `PATCH` | `/api/v1/sessions/{session_id}/verify/{chunk_id}` |
| `GET` | `/api/v1/sessions/{session_id}/export-gate` |
| `GET` | `/health` |

## Run locally

```powershell
cd C:\Users\Acer\Downloads\NL_Grad_ChatGPT
$env:PYTHONPATH="src"
$env:EMBED_MOCK="true"
$env:GROQ_MOCK="true"
uvicorn api.main:app --reload --port 8000
# separate terminal:
streamlit run backend/streamlit_app.py
```

Live Groq: set `GROQ_API_KEY`, `GROQ_MOCK=false`.

## Handoff to Phase 6

Point Vercel `NEXT_PUBLIC_BACKEND_URL` at this API for the HITL two-pane UI.
