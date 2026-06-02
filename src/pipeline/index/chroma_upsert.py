"""
Phase 4.4 CLI — index Phase 3 chunks into local Chroma.

Usage:
  set PYTHONPATH=src
  set EMBED_MOCK=true
  python -m pipeline.index.chroma_upsert
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.index.orchestrator import IndexOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Embed Phase 3 chunks and upsert into local Chroma"
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without writing to Chroma",
    )
    parser.add_argument(
        "--prune-only",
        action="store_true",
        help="Only run prune cascade from manifest pruned_document_ids",
    )
    parser.add_argument(
        "--no-clear-pruned",
        action="store_true",
        help="Do not clear pruned_document_ids from manifest after delete",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    orchestrator = IndexOrchestrator(repo_root=Path(args.repo_root).resolve())
    result = orchestrator.run(
        dry_run=args.dry_run,
        prune_only=args.prune_only,
        clear_pruned_manifest=not args.no_clear_pruned,
    )
    print(
        f"Index complete: embedded={result.chunks_embedded}, "
        f"skipped={result.chunks_skipped_unchanged}, "
        f"deleted={result.chunks_deleted}, "
        f"errors={result.chunks_errors}, "
        f"dry_run={result.dry_run}"
    )
    print(f"Chroma count: {orchestrator.store.count()}")
    print(f"Stats: {orchestrator.stats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
