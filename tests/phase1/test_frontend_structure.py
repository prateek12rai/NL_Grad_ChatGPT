"""Phase 1.5.4 — Frontend scaffold (Vercel/Vite) structure validation."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_frontend_package_and_vercel_config():
    pkg = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    assert "build" in pkg["scripts"]
    assert "react" in pkg["dependencies"]
    vercel = json.loads((FRONTEND / "vercel.json").read_text(encoding="utf-8"))
    assert vercel.get("outputDirectory") == "dist"


def test_frontend_entry_files_exist():
    assert (FRONTEND / "index.html").is_file()
    assert (FRONTEND / "src" / "App.tsx").is_file()
    assert (FRONTEND / "vite.config.ts").is_file()
