"""Helpers for citation source URLs (fixture vs live corpus)."""

from __future__ import annotations

import re

# Legacy Phase 2 fixture article IDs — not real Nature pages
_FIXTURE_NATURE_ARTICLE = re.compile(
    r"^https://www\.nature\.com/articles/d41586-026-0000[12]-[08]$"
)

NATURE_SEARCH_URL = (
    "https://www.nature.com/search?"
    "article_type=research&subject=medical-research&date_range=last_30_days&order=relevance"
)

# Canonical replacements for demo fixture documents (real Nature Communications articles)
FIXTURE_URL_REPLACEMENTS: dict[str, str] = {
    "https://www.nature.com/articles/d41586-026-00001-0": (
        "https://www.nature.com/articles/s41467-026-73798-3"
    ),
    "https://www.nature.com/articles/d41586-026-00002-8": (
        "https://www.nature.com/articles/s41467-026-70664-0"
    ),
}


def is_legacy_fixture_nature_url(url: str) -> bool:
    return bool(_FIXTURE_NATURE_ARTICLE.match(url.strip()))


def resolve_source_url(url: str) -> str:
    """Map old fixture URLs to live Nature article pages when known."""
    return FIXTURE_URL_REPLACEMENTS.get(url.strip(), url.strip())
