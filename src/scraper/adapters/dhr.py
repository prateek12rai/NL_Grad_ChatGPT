"""
DHR adapter — Department of Health Research publications.

The main dhr.gov.in publications UI is a client-rendered SPA with no PDF links in HTML.
Live ingest crawls the official HTAIn portal (htain.dhr.gov.in) for real PDFs.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from shared.schemas import SourceOrg
from scraper.adapters.base import BaseAdapter
from scraper.downloader import DocumentDownloader
from scraper.link_crawl import collect_pdf_links
from scraper.models import ScrapedItem

# Legacy listing (SPA — kept for reference / future Playwright)
DHR_PUBLICATIONS_URL = "https://www.dhr.gov.in/documents/publications?page=1"
# Live PDF source on official DHR subdomain
HTAIN_BASE_URL = "https://htain.dhr.gov.in"
DHR_BASE_URL = HTAIN_BASE_URL  # live PDF portal (main site is SPA)


class DHRAdapter(BaseAdapter):
    source_name = "DHR"

    def __init__(
        self,
        base_url: str = HTAIN_BASE_URL,
        fixture_html: str | None = None,
        max_pdfs: int = 15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.fixture_html = fixture_html
        self.max_pdfs = max_pdfs

    def fetch_listing_html(self, client) -> str:
        if self.fixture_html is not None:
            return self.fixture_html
        if client is None:
            raise RuntimeError("httpx client required for live DHR fetch")
        response = client.get(self.base_url + "/")
        response.raise_for_status()
        return response.text

    def discover(self, client=None) -> list[ScrapedItem]:
        if self.fixture_html is not None:
            return super().discover(client)

        if client is None:
            raise RuntimeError("httpx client required for live DHR discover")
        pairs = collect_pdf_links(
            client,
            [self.base_url + "/", self.base_url + "/index.php"],
            same_host=self.base_url,
            max_pdfs=self.max_pdfs,
            max_pages=10,
        )
        items = [
            ScrapedItem(
                source_org=SourceOrg.DHR,
                source_url=url,
                document_title=title or Path(url).stem.replace("_", " "),
                publication_date=_year_from_url(url),
                content_type="pdf",
            )
            for url, title in pairs
        ]
        return sorted(items, key=lambda i: i.publication_date, reverse=True)

    def parse_listing(self, html: str) -> list[ScrapedItem]:
        """Parse fixture HTML or HTAIn homepage fallback."""
        soup = BeautifulSoup(html, "lxml")
        items: list[ScrapedItem] = []
        base = self.base_url

        for link in soup.select('a[href$=".pdf"], a[href*=".pdf"]'):
            href = link.get("href", "").strip()
            if not href:
                continue
            url = urljoin(base, href)
            title = link.get_text(strip=True) or Path(url).stem
            items.append(
                ScrapedItem(
                    source_org=SourceOrg.DHR,
                    source_url=url,
                    document_title=title,
                    publication_date=_year_from_url(url),
                    content_type="pdf",
                )
            )

        # Fixture structure (tests)
        for row in soup.select(".publication-item, article.publication, tr.publication-row"):
            link = row.select_one("a[href]")
            if not link:
                continue
            href = link.get("href", "").strip()
            url = urljoin("https://www.dhr.gov.in", href)
            title = link.get_text(strip=True) or "DHR Publication"
            items.append(
                ScrapedItem(
                    source_org=SourceOrg.DHR,
                    source_url=url,
                    document_title=title,
                    publication_date="2026-01-01",
                    content_type=DocumentDownloader.infer_content_type(url),
                )
            )

        return _dedupe_by_url(items)


def _year_from_url(url: str) -> str:
    m = re.search(r"(20\d{2})", url)
    return f"{m.group(1)}-06-01" if m else "2026-01-01"


def _dedupe_by_url(items: list[ScrapedItem]) -> list[ScrapedItem]:
    seen: set[str] = set()
    out: list[ScrapedItem] = []
    for item in items:
        if item.source_url in seen:
            continue
        seen.add(item.source_url)
        out.append(item)
    return out
