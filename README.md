# CHATGPT Glass (prototype) — Nature-only Medical RAG + HITL

Retrieval-augmented medical research assistant with mandatory human verification before export.  
Architecture: [docs/architecture.md](docs/architecture.md) · Progress: [PHASES/README.md](PHASES/README.md)

## Current status

**Phase 6 — CHATGPT Glass Frontend** complete (see [PHASES/Phase-06-Frontend](PHASES/Phase-06-Frontend/))  
**Phase 5 — Backend** complete · Phases 2–4 for ingest/chunk/embed

### Build Nature-only corpus (recommended)

Single listing URL — [Nature medical research, last 30 days](https://www.nature.com/search?article_type=research&subject=medical-research&date_range=last_30_days&order=relevance). Paginated scrape → chunk → Chroma:

```powershell
$env:PYTHONPATH = "src"
python scripts/build_real_prototype.py --fresh --max-total 20
```

Trim an existing corpus to the 20 newest HTML files:

```powershell
python scripts/trim_corpus.py --keep 20
```

### Run ingest only

```powershell
$env:PYTHONPATH = "src"
python -m scraper.scheduler --max-total 20
```

Offline tests only (fixture HTML, not real publisher content):

```bash
python -m scraper.scheduler --fixture
```

## Local setup

### Python 3.11+

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Environment

Copy `.env.example` to `.env` and add keys when needed:

| Secret | Phase | Where to get |
|--------|-------|----------------|
| `GROQ_API_KEY` | 5 | [console.groq.com](https://console.groq.com/) |
| `HUGGINGFACE_API_TOKEN` | 4 | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |

Phase 1 runs without real API keys.

### Run backend health API

```bash
set PYTHONPATH=src
python -m uvicorn api.main:app --reload --port 8000
```

Open http://localhost:8000/health

### Run Streamlit dashboard

```bash
set PYTHONPATH=src
streamlit run backend/streamlit_app.py
```

### Run frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests (Phase 1 gate)

```bash
set PYTHONPATH=src
pytest tests/phase1/ -v
```

## Folder permissions

| Path | Purpose |
|------|---------|
| `chroma_db/` | Local vector index (created automatically) |
| `data/corpus/` | Downloaded documents (Phase 2+) |

## GitHub Actions secrets (Phase 7+)

| Secret | Purpose |
|--------|---------|
| `HUGGINGFACE_API_TOKEN` | Embeddings in scheduled ingest |
| `GROQ_API_KEY` | Optional LLM steps in pipeline |

## Deployment map

| Component | Platform |
|-----------|----------|
| Scheduler | GitHub Actions |
| Backend + API | Streamlit Cloud |
| HITL UI | Vercel (`frontend/`) |
