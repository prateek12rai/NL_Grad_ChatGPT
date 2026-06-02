"""
CLI entry for ingest — Nature-only portfolio search (last 30 days).

Usage:
  python -m scraper.scheduler                    # LIVE Nature scrape (paginated)
  python -m scraper.scheduler --fixture          # offline HTML fixture only
  python -m scraper.scheduler --max-total 1180   # cap downloads this run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scraper.adapters.nature import NATURE_SEARCH_URL, NatureAdapter
from scraper.downloader import DocumentDownloader
from scraper.orchestrator import IngestOrchestrator
from shared.config import settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Nature medical-research ingest (single listing URL, last 30 days)"
    )
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Use bundled Nature HTML fixture (offline tests only)",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help=f"Max articles to discover/download (default: {settings.scraper_nature_max_articles})",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help=f"Max search result pages to crawl (default: {settings.scraper_nature_max_pages})",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=None,
        help="Cap new documents ingested this run (default: all discovered up to max-articles)",
    )
    args = parser.parse_args(argv)

    max_articles = args.max_articles if args.max_articles is not None else settings.scraper_nature_max_articles
    max_pages = args.max_pages if args.max_pages is not None else settings.scraper_nature_max_pages
    max_total = args.max_total if args.max_total is not None else settings.scraper_max_total

    adapters = _build_adapters(
        use_fixtures=args.fixture,
        max_articles=max_articles,
        max_pages=max_pages,
    )
    orchestrator = IngestOrchestrator(
        downloader=DocumentDownloader(mock_downloads=args.fixture),
        adapters=adapters,
        mock_downloads=args.fixture,
        repo_root=Path.cwd(),
    )

    try:
        result = orchestrator.run(
            sources=["nature"],
            max_per_source=max_articles,
            max_total=max_total,
        )
    finally:
        orchestrator.close()

    print(f"Listing URL: {NATURE_SEARCH_URL}")
    print(
        f"Ingest complete: ingested={result.ingested}, "
        f"skipped_existing={result.skipped_existing}, "
        f"skipped_pii={result.skipped_pii}, pruned={len(result.pruned_ids)}"
    )
    return 0


def _build_adapters(use_fixtures: bool, max_articles: int, max_pages: int):
    if use_fixtures:
        root = Path(__file__).resolve().parents[2]
        fixtures = root / "tests" / "fixtures" / "phase2"
        return [
            NatureAdapter(
                fixture_html=(fixtures / "nature_listing.html").read_text(encoding="utf-8"),
                max_articles=max_articles,
            ),
        ]
    return [
        NatureAdapter(
            search_url=settings.nature_search_url or NATURE_SEARCH_URL,
            max_articles=max_articles,
            max_pages=max_pages,
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(main())
