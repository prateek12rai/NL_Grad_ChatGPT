"""Nature medical-research search — single canonical listing URL (last 30 days)."""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from shared.config import settings
from shared.schemas import SourceOrg
from scraper.adapters.base import BaseAdapter
from scraper.models import ScrapedItem

logger = logging.getLogger(__name__)

# Portfolio reference URL (only Nature ingest source)
NATURE_SEARCH_URL = (
    "https://www.nature.com/search?"
    "article_type=research&subject=medical-research&date_range=last_30_days&order=relevance"
)

_ARTICLE_PATH = re.compile(r"^/articles/s\d+-\d+-\d+-\d+$", re.I)


def assert_nature_url_compliant(url: str = NATURE_SEARCH_URL) -> None:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if params.get("date_range", [""])[0] != "last_30_days":
        raise ValueError(
            f"Nature URL must use date_range=last_30_days (portfolio search only): {url}"
        )
    if params.get("subject", [""])[0] != "medical-research":
        raise ValueError(f"Nature URL must include subject=medical-research: {url}")
    if params.get("article_type", [""])[0] != "research":
        raise ValueError(f"Nature URL must include article_type=research: {url}")


def _resolve_search_url(url: str | None) -> str:
    if url:
        assert_nature_url_compliant(url)
        return url
    from_env = getattr(settings, "nature_search_url", "") or ""
    if from_env.strip():
        assert_nature_url_compliant(from_env.strip())
        return from_env.strip()
    return NATURE_SEARCH_URL


class NatureAdapter(BaseAdapter):
    source_name = "Nature"

    def __init__(
        self,
        search_url: str | None = None,
        fixture_html: str | None = None,
        max_articles: int | None = None,
        max_pages: int | None = None,
    ) -> None:
        self.search_url = _resolve_search_url(search_url)
        self.fixture_html = fixture_html
        self.max_articles = (
            max_articles
            if max_articles is not None
            else settings.scraper_nature_max_articles
        )
        self.max_pages = max_pages if max_pages is not None else settings.scraper_nature_max_pages

    def _page_url(self, page: int) -> str:
        parsed = urlparse(self.search_url)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        if page > 1:
            params["page"] = str(page)
        elif "page" in params:
            del params["page"]
        query = urlencode(params)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", query, ""))

    def fetch_listing_html(self, client, *, page: int = 1) -> str:
        if self.fixture_html is not None:
            return self.fixture_html
        if client is None:
            raise RuntimeError("httpx client required for live Nature fetch")
        url = self._page_url(page)
        response = client.get(url)
        response.raise_for_status()
        return response.text

    def parse_listing(self, html: str) -> list[ScrapedItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ScrapedItem] = []
        base = "https://www.nature.com"

        for anchor in soup.select('a[href*="/articles/"]'):
            href = (anchor.get("href") or "").strip().split("?")[0]
            path = urlparse(urljoin(base, href)).path
            if not _ARTICLE_PATH.match(path):
                continue
            url = urljoin(base, path)
            title = anchor.get_text(strip=True) or "Nature Research Article"
            if len(title) < 8:
                continue
            parent = anchor.find_parent("article")
            time_el = parent.select_one("time[datetime]") if parent else None
            if time_el and time_el.get("datetime"):
                pub_date = time_el["datetime"][:10]
            else:
                pub_date = "2026-06-01"
            items.append(
                ScrapedItem(
                    source_org=SourceOrg.NATURE,
                    source_url=url,
                    document_title=title[:280],
                    publication_date=pub_date,
                    content_type="html",
                )
            )

        return _dedupe_by_url(items)

    def discover(self, client=None) -> list[ScrapedItem]:
        if self.fixture_html is not None:
            html = self.fixture_html
            items = self.parse_listing(html)
            return sorted(items, key=lambda i: i.publication_date, reverse=True)[
                : self.max_articles
            ]

        if client is None:
            raise RuntimeError("httpx client required for live Nature discover")

        all_items: list[ScrapedItem] = []
        seen_urls: set[str] = set()
        delay = settings.scraper_request_delay_seconds

        for page in range(1, self.max_pages + 1):
            html = self.fetch_listing_html(client, page=page)
            batch = self.parse_listing(html)
            new_items = [i for i in batch if i.source_url not in seen_urls]
            for item in new_items:
                seen_urls.add(item.source_url)
                all_items.append(item)

            logger.info(
                "nature_discover page=%s batch=%s new=%s total=%s",
                page,
                len(batch),
                len(new_items),
                len(all_items),
            )

            if not new_items:
                break
            if self.max_articles and len(all_items) >= self.max_articles:
                break
            if page < self.max_pages and delay > 0:
                time.sleep(delay)

        ordered = sorted(all_items, key=lambda i: i.publication_date, reverse=True)
        if self.max_articles:
            return ordered[: self.max_articles]
        return ordered


def _dedupe_by_url(items: list[ScrapedItem]) -> list[ScrapedItem]:
    seen: set[str] = set()
    out: list[ScrapedItem] = []
    for item in items:
        if item.source_url in seen:
            continue
        seen.add(item.source_url)
        out.append(item)
    return out
