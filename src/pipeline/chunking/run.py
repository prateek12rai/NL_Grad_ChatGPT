"""
Phase 3.6 CLI — chunk all manifest documents.

Usage (from repo root):
  set PYTHONPATH=src
  python -m pipeline.chunking.run --manifest data/manifest.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.chunking.orchestrator import ChunkingOrchestrator
from scraper.manifest import ManifestStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Chunk corpus documents into data/chunks/*.jsonl"
    )
    parser.add_argument(
        "--manifest",
        default="data/manifest.json",
        help="Path to manifest.json (default: data/manifest.json)",
    )
    parser.add_argument(
        "--document-id",
        default=None,
        help="Process only this document_id",
    )
    parser.add_argument(
        "--incremental",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip documents already chunked at same ingested_at (default: on)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild chunk files even if up to date",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for resolving local_path entries",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path

    orchestrator = ChunkingOrchestrator(
        repo_root=repo_root,
        manifest_store=ManifestStore(manifest_path),
    )
    result = orchestrator.run(
        document_id=args.document_id,
        incremental=args.incremental,
        force=args.force,
    )

    print(
        f"Chunking complete: processed={result.processed}, "
        f"chunks_written={result.chunks_written}, "
        f"skipped_incremental={result.skipped_incremental}, "
        f"skipped_extract={result.skipped_extract}, "
        f"skipped_missing={result.skipped_missing}, "
        f"pii_dropped={result.chunks_dropped_pii}"
    )
    index_path = orchestrator.index_path
    if index_path.exists():
        print(f"Index: {index_path} ({index_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
