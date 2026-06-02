"""ICMR reports adapter — live PDF discovery from icmr.gov.in."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from shared.schemas import SourceOrg
from scraper.adapters.base import BaseAdapter
from scraper.models import ScrapedItem

ICMR_REPORTS_URL = "https://www.icmr.gov.in/reports"
ICMR_HOME_URL = "https://www.icmr.gov.in/"

# Prefer clinical/guideline PDFs over short calls/EOIs when trimming
_ICMR_PRIORITY = ("guideline", "report", "document", "publication", "manual", "policy")


class ICMRAdapter(BaseAdapter):
    source_name = "ICMR"

    def __init__(
        self,
        base_url: str = ICMR_REPORTS_URL,
        fixture_html: str | None = None,
        max_pdfs: int = 20,
    ) -> None:
        self.base_url = base_url
        self.fixture_html = fixture_html
        self.max_pdfs = max_pdfs

    def fetch_listing_html(self, client) -> str:
        if self.fixture_html is not None:
            return self.fixture_html
        if client is None:
            raise RuntimeError("httpx client required for live ICMR fetch")
        parts: list[str] = []
        for url in (self.base_url, ICMR_HOME_URL):
            response = client.get(url)
            response.raise_for_status()
            parts.append(response.text)
        return "\n".join(parts)

    def parse_listing(self, html: str) -> list[ScrapedItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ScrapedItem] = []
        base = "https://www.icmr.gov.in"

        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href.lower().endswith(".pdf"):
                continue
            url = urljoin(base, href)
            if urlparse(url).netloc != "www.icmr.gov.in":
                continue
            title = anchor.get_text(" ", strip=True) or Path(url).stem.replace("_", " ")
            if len(title) < 4:
                title = Path(url).stem.replace("_", " ")
            items.append(
                ScrapedItem(
                    source_org=SourceOrg.ICMR,
                    source_url=url,
                    document_title=title[:240],
                    publication_date=_parse_date(title) or _year_from_url(url),
                    content_type="pdf",
                )
            )

        # Fixture rows
        for row in soup.select(".report-item, article.report, .views-row"):
            link = row.select_one('a[href$=".pdf"], a[href*="/reports/"], a.report-link')
            if not link:
                continue
            href = link.get("href", "").strip()
            url = urljoin(base, href)
            title_el = row.select_one("h2, h3, .title") or link
            title = title_el.get_text(strip=True) or "ICMR Report"
            date_el = row.select_one(".date, time, span.date")
            pub_date = _parse_date(date_el.get_text(strip=True) if date_el else "") or "2026-01-01"
            items.append(
                ScrapedItem(
                    source_org=SourceOrg.ICMR,
                    source_url=url,
                    document_title=title,
                    publication_date=pub_date,
                    content_type="pdf",
                )
            )

        items = _dedupe_by_url(items)
        return _prioritize_icmr(items)[: self.max_pdfs]


def _prioritize_icmr(items: list[ScrapedItem]) -> list[ScrapedItem]:
    def score(item: ScrapedItem) -> tuple[int, str]:
        blob = f"{item.document_title} {item.source_url}".lower()
        pri = 0
        for i, token in enumerate(_ICMR_PRIORITY):
            if token in blob:
                pri = max(pri, len(_ICMR_PRIORITY) - i)
        if "/call/" in blob or "eoi" in blob:
            pri -= 2
        return (pri, item.publication_date)

    return sorted(items, key=score, reverse=True)


def _parse_date(text: str) -> str | None:
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text or "")
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(20\d{2})", text or "")
    if m:
        return f"{m.group(1)}-06-01"
    return None


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
