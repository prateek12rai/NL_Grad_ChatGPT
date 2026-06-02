"""
Phase 3.4 preview — chunk drafts with 512 cap + 80 overlap.

Usage:
  set PYTHONPATH=src
  python scripts/chunk_preview.py
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
from pipeline.chunking.tokenization import pages_to_chunk_drafts


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview Phase 3.4 chunk drafts")
    parser.add_argument("--manifest", default="data/manifest.json")
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()

    data = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    for doc in data.get("documents", [])[: args.limit]:
        local = ROOT / doc["local_path"]
        print(f"\n=== {doc['document_title']} ===")
        try:
            pages = extract_document(local, doc.get("content_type", "pdf")).pages
            drafts = pages_to_chunk_drafts(pages)
        except ExtractionError as exc:
            print(f"  SKIP: {exc}")
            continue
        print(f"  Chunks: {len(drafts)}")
        for i, d in enumerate(drafts[:5], start=1):
            title = d.section_title or "(no title)"
            preview = d.exact_context[:90].replace("\n", " ")
            print(f"  [{i}] p{d.page_number} | {title} | {d.token_count} tok | {preview}...")
        if drafts:
            over_max = [d for d in drafts if d.token_count > 512]
            print(f"  Over 512 tokens: {len(over_max)} (should be 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
