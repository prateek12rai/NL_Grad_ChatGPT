"""
Phase 3.1 preview — extract text from manifest documents (first N).

Usage:
  set PYTHONPATH=src
  python scripts/extract_preview.py
  python scripts/extract_preview.py --document-id sha256:4942ed487933e004
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview Phase 3.1 extraction")
    parser.add_argument("--manifest", default="data/manifest.json")
    parser.add_argument("--document-id", default=None)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return 1

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    docs = data.get("documents", data) if isinstance(data, dict) else data
    if args.document_id:
        docs = [d for d in docs if d["document_id"] == args.document_id]

    for doc in docs[: args.limit]:
        local = ROOT / doc["local_path"]
        ctype = doc.get("content_type", "pdf")
        print(f"\n=== {doc['document_title']} ({doc['document_id']}) ===")
        print(f"Path: {local}  type: {ctype}")
        try:
            result = extract_document(local, ctype)
        except ExtractionError as exc:
            print(f"  ERROR: {exc}")
            continue
        for page in result.pages:
            preview = page.text[:200].replace("\n", " ")
            print(f"  Page {page.page_number}: {preview}...")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
