"""Phase 6 — HITL frontend structure (architecture §12)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"


def test_phase6_components_and_api_client():
    assert (SRC / "api" / "client.ts").is_file()
    assert (SRC / "components" / "SourcePreviewPanel.tsx").is_file()
    assert (SRC / "components" / "ExportToolbar.tsx").is_file()
    app = (SRC / "App.tsx").read_text(encoding="utf-8")
    assert "data-testid=\"hitl-app\"" in app
    assert "ExportToolbar" in app
    assert "SourcePreviewPanel" in app


def test_playwright_e2e_spec_exists():
    assert (FRONTEND / "e2e" / "hitl.spec.ts").is_file()
    pkg = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    assert "test:e2e" in pkg["scripts"]
    assert "@playwright/test" in pkg.get("devDependencies", {})
