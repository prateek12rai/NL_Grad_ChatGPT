"""Phase 2.7.6 — Regression: Phase 1 tests remain green."""

import os
import subprocess
import sys
from pathlib import Path


def test_phase1_regression_suite():
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/phase1/", "-q"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
