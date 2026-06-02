# Phase 6 — Deep Test Gate Report

**Date:** 2026-06-01  
**Reference:** [docs/architecture.md](../../docs/architecture.md) §12.3

| # | Test | Result | Evidence |
|---|------|--------|----------|
| 6.6.1 | Playwright E2E — query → verify → export | PASS | `frontend/e2e/hitl.spec.ts` |
| 6.6.2 | Export lock E2E | PASS | same |
| 6.6.3 | Highlight on click | PASS | `mark.context-highlight` < 200ms perceived (mock) |
| 6.6.4 | Vercel preview deploy | MANUAL | Set `VITE_BACKEND_URL` + deploy `frontend/` |
| 6.6.5 | Production deploy + CORS | MANUAL | Add prod URL to `CORS_ORIGINS` |
| 6.6.6 | Accessibility | PASS | `aria-label` on copy/export/verify/citations |
| 6.6.7 | Regression Phases 1–5 | PASS | `pytest -m "not live"` |
| 6.6.8 | Phase report | PASS | `docs/phase-reports/phase-6-gate.md` |

## Run locally

```powershell
# Terminal 1 — API
$env:PYTHONPATH = "src"
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — UI
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## E2E

```bash
cd frontend
npm install
npx playwright install chromium
npm run test:e2e
```
