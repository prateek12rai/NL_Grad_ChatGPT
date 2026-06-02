"""Base adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from scraper.models import ScrapedItem


class BaseAdapter(ABC):
    source_name: str

    @abstractmethod
    def fetch_listing_html(self, client) -> str:
        """Return HTML for the listing page (live or fixture)."""

    @abstractmethod
    def parse_listing(self, html: str) -> list[ScrapedItem]:
        """Parse listing HTML into discovered items (newest-first preferred)."""

    def discover(self, client=None) -> list[ScrapedItem]:
        html = self.fetch_listing_html(client)
        items = self.parse_listing(html)
        return sorted(items, key=lambda i: i.publication_date, reverse=True)
