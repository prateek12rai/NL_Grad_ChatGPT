# Windows: start FastAPI + Streamlit (run from repo root)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = Join-Path $Root "src"

Start-Process -NoNewWindow python -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"
streamlit run backend/streamlit_app.py --server.port 8501
