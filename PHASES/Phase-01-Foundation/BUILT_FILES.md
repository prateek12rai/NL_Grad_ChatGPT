# Phase 1 — Files created (monitoring)

## Python backend

| File | Purpose |
|------|---------|
| `requirements.txt` | Python packages |
| `src/shared/schemas.py` | Data shapes for documents & chunks |
| `src/shared/pii_filter.py` | Blocks Aadhaar, PAN, phone, email |
| `src/shared/chroma_client.py` | Local database helper |
| `src/shared/config.py` | Settings from `.env` |
| `src/api/main.py` | Health API (`/health`) |
| `backend/streamlit_app.py` | Health dashboard (Streamlit) |

## Frontend (Vercel later)

| File | Purpose |
|------|---------|
| `frontend/package.json` | React + Vite project |
| `frontend/src/App.tsx` | Placeholder home page |
| `frontend/vercel.json` | Vercel deploy settings |

## Tests & automation

| File | Purpose |
|------|---------|
| `tests/phase1/` | Phase 1 automated tests |
| `.github/workflows/test-phase1.yml` | Runs tests on GitHub |
| `.github/workflows/daily-ingest.yml` | Placeholder until Phase 7 |

## Configuration templates

| File | Purpose |
|------|---------|
| `.env.example` | API keys template (do not put real keys in git) |
| `secrets.toml.example` | Streamlit Cloud secrets template |
| `README.md` | How to run the project |
