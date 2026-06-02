#!/usr/bin/env bash
# Render start command — FastAPI only (Vercel-facing). See docs/deployment-plan.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src"
PORT="${PORT:-8000}"
exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
