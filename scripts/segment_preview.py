"""
Phase 3.3 preview — extract → sections → structural text units.

Usage:
  set PYTHONPATH=src
  python scripts/segment_preview.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline.chunking.exceptions import ExtractionError
from pipeline.chunking.extractors import extract_document
from pipeline.chunking.segmentation import pages_to_units


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview Phase 3.3 structural units")
    parser.add_argument("--manifest", default="data/manifest.json")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    data = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    for doc in data.get("documents", [])[: args.limit]:
        local = ROOT / doc["local_path"]
        print(f"\n=== {doc['document_title']} ===")
        try:
            pages = extract_document(local, doc.get("content_type", "pdf")).pages
            units = pages_to_units(pages)
        except ExtractionError as exc:
            print(f"  SKIP: {exc}")
            continue
        print(f"  Pages: {len(pages)}  Units: {len(units)}")
        for i, unit in enumerate(units[:6], start=1):
            title = unit.section_title or "(no section title)"
            preview = unit.text[:100].replace("\n", " ")
            print(f"  [{i}] p{unit.page_number} | {title} | {unit.token_count} tok | {preview}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
