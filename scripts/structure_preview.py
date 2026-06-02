"""
Phase 3.2 preview — extract + detect sections from manifest documents.

Usage:
  set PYTHONPATH=src
  python scripts/structure_preview.py
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
from pipeline.chunking.structure import detect_sections


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview Phase 3.2 structure detection")
    parser.add_argument("--manifest", default="data/manifest.json")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    docs = data.get("documents", [])

    for doc in docs[: args.limit]:
        local = ROOT / doc["local_path"]
        print(f"\n=== {doc['document_title']} ===")
        try:
            extracted = extract_document(local, doc.get("content_type", "pdf"))
            spans = detect_sections(extracted.pages)
        except ExtractionError as exc:
            print(f"  SKIP: {exc}")
            continue
        print(f"  Pages: {len(extracted.pages)}  Sections: {len(spans)}")
        for i, span in enumerate(spans[:8], start=1):
            title = span.title or "(no title)"
            preview = span.text[:120].replace("\n", " ")
            print(f"  [{i}] p{span.page_number} | {title} | {preview}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
