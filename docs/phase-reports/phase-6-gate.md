# Phase 6 Gate — HITL Frontend (Vercel)

**Status:** PASS (automated); Vercel deploy manual  
**Architecture:** §12

## Summary

- Vite + React two-pane console
- Wired to Phase 5 REST API
- Export/copy gated per `session_id` via `GET .../export-gate`
- Out-of-corpus: Pinky Promise + `suggested_queries` chips
- Playwright E2E with mocked backend routes

## Verification commands

```bash
pytest tests/phase6 tests/phase1/test_frontend_structure.py -q
cd frontend && npm run build
cd frontend && npm run test:e2e
```
