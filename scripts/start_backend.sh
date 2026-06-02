#!/usr/bin/env bash
# Start FastAPI (Vercel-facing) + Streamlit (ops UI) — architecture §3.1
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src"

uvicorn api.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

streamlit run backend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

kill $UVICORN_PID 2>/dev/null || true
