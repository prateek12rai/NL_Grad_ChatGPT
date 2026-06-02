"""
Nature-only corpus build (single listing URL, last 30 days).

  set PYTHONPATH=src
  python scripts/build_real_prototype.py --fresh
  python scripts/build_real_prototype.py --max-total 20

Steps: paginated Nature scrape → chunk → Chroma upsert
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shared.config import settings  # noqa: E402

NATURE_LISTING_URL = settings.nature_search_url


def _run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def _fresh_data() -> None:
    for rel in (
        "data/manifest.json",
        "data/ingest_log.jsonl",
        "data/chunks",
        "data/chroma_stats.json",
        "data/embed_log.jsonl",
    ):
        path = ROOT / rel
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    corpus = ROOT / settings.corpus_path
    if corpus.is_dir():
        shutil.rmtree(corpus)
    chroma = ROOT / settings.chroma_path
    if chroma.is_dir():
        try:
            shutil.rmtree(chroma)
        except OSError as exc:
            print(f"Warning: could not remove {chroma} ({exc}). Stop uvicorn and retry --fresh.")
    (ROOT / "data" / "chunks").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "corpus" / "nature").mkdir(parents=True, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Nature-only corpus from portfolio search URL (last 30 days)"
    )
    parser.add_argument("--fresh", action="store_true", help="Delete old manifest, corpus, chunks, chroma")
    parser.add_argument(
        "--max-articles",
        type=int,
        default=settings.scraper_nature_max_articles,
        help="Max articles to discover from Nature search",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=settings.scraper_nature_max_pages,
        help="Max search pages to crawl",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=None,
        help="Cap documents downloaded this run (e.g. 1180)",
    )
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument("--skip-chunk", action="store_true")
    parser.add_argument("--skip-embed", action="store_true")
    args = parser.parse_args(argv)

    print(f"Nature listing (only source): {NATURE_LISTING_URL}\n")

    if args.fresh:
        print("Clearing previous corpus artifacts…")
        _fresh_data()

    py = sys.executable

    if not args.skip_ingest:
        cmd = [
            py,
            "-m",
            "scraper.scheduler",
            "--max-articles",
            str(args.max_articles),
            "--max-pages",
            str(args.max_pages),
        ]
        if args.max_total is not None:
            cmd.extend(["--max-total", str(args.max_total)])
        _run(cmd)

    if not args.skip_chunk:
        _run([py, "-m", "pipeline.chunking.run", "--manifest", "data/manifest.json", "--force"])

    if not args.skip_embed:
        _run([py, "-m", "pipeline.index.chroma_upsert"])

    print("\nDone. Start API + UI:")
    print("  python -m uvicorn api.main:app --reload --port 8000")
    print("  cd frontend && npm run dev")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
