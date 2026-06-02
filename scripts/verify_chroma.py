"""
Phase 4.5 — verify local Chroma index health.

Usage:
  set PYTHONPATH=src
  set EMBED_MOCK=true
  python scripts/verify_chroma.py
  python scripts/verify_chroma.py --expected 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline.index.verify import verify_chroma_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Chroma index (Phase 4.5)")
    parser.add_argument(
        "--expected",
        type=int,
        default=None,
        help="Expected vector count (default: read chroma_stats.json)",
    )
    parser.add_argument(
        "--repo-root",
        default=str(ROOT),
        help="Repository root for stats/index paths",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Override sample query string",
    )
    args = parser.parse_args()

    report = verify_chroma_index(
        expected_count=args.expected,
        repo_root=Path(args.repo_root),
        sample_query=args.query or None,
    )

    print("Chroma verification report")
    print("-" * 40)
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        detail = f" — {check.detail}" if check.detail else ""
        print(f"  [{status}] {check.name}{detail}")

    print("-" * 40)
    if report.passed:
        print("Overall: PASS")
        return 0
    print("Overall: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
