"""Internal scraper types (Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass

from shared.schemas import SourceOrg


@dataclass(frozen=True)
class ScrapedItem:
    """Discovered document before download and manifest registration."""

    source_org: SourceOrg
    source_url: str
    document_title: str
    publication_date: str  # ISO date YYYY-MM-DD
    content_type: str = "pdf"  # pdf | html
