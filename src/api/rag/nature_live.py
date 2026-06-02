"""Optional live Nature listing count (may exceed local ingest)."""

from __future__ import annotations

import logging
from datetime import date

logger = logging.getLogger(__name__)


def count_nature_on_date(target_date: date) -> int | None:
    """
    Count Nature research articles on the listing whose publication date matches.

    Returns None if the live request fails (offline / blocked).
    """
    try:
        import httpx
        from scraper.adapters.nature import NatureAdapter

        adapter = NatureAdapter(max_articles=50)
        with httpx.Client(timeout=4.0, follow_redirects=True) as client:
            html = adapter.fetch_listing_html(client)
        items = adapter.parse_listing(html)
        iso = target_date.isoformat()
        return sum(1 for item in items if str(item.publication_date)[:10] == iso)
    except Exception as exc:
        logger.info("nature_live_count skipped: %s", exc)
        return None
