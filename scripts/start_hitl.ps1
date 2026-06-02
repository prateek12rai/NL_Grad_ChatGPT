# Start FastAPI backend + Vite HITL frontend (run from repo root)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = Join-Path $Root "src"

Write-Host "Starting API on http://127.0.0.1:8000 ..."
Start-Process -WindowStyle Minimized python -ArgumentList @(
    "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"
) -WorkingDirectory $Root

$nodePath = "C:\Program Files\nodejs"
if (Test-Path $nodePath) {
    $env:Path = "$nodePath;" + $env:Path
}

Write-Host "Starting frontend on http://127.0.0.1:5173 ..."
Start-Process -WindowStyle Minimized powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root\frontend'; npm run dev -- --host 127.0.0.1"
)

Start-Sleep -Seconds 3
Write-Host ""
Write-Host "Open: http://127.0.0.1:5173  (UI)"
Write-Host "API:  http://127.0.0.1:8000/health"
Write-Host "Stop: close the minimized terminal windows or end python/node tasks."
