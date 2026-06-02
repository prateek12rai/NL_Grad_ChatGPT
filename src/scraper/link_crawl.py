"""Collect PDF/HTML links from a site by crawling listing pages."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def collect_pdf_links(
    client,
    start_urls: list[str],
    *,
    same_host: str,
    max_pdfs: int = 50,
    max_pages: int = 8,
) -> list[tuple[str, str]]:
    """
    Return ``(absolute_pdf_url, link_title)`` from *start_urls* and one hop of internal links.
    """
    host = urlparse(same_host).netloc
    seen_pages: set[str] = set()
    seen_pdfs: set[str] = set()
    queue = list(start_urls)
    results: list[tuple[str, str]] = []

    while queue and len(seen_pages) < max_pages and len(results) < max_pdfs:
        page_url = queue.pop(0)
        if page_url in seen_pages:
            continue
        seen_pages.add(page_url)
        try:
            response = client.get(page_url)
            response.raise_for_status()
        except Exception:
            continue
        soup = BeautifulSoup(response.text, "lxml")
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href or href.startswith("#"):
                continue
            absolute = urljoin(page_url, href)
            parsed = urlparse(absolute)
            if parsed.netloc != host:
                continue
            lower = absolute.lower()
            if lower.endswith(".pdf"):
                if absolute not in seen_pdfs:
                    seen_pdfs.add(absolute)
                    title = anchor.get_text(" ", strip=True) or parsed.path.split("/")[-1]
                    results.append((absolute, title))
                continue
            if (
                len(seen_pages) + len(queue) < max_pages
                and absolute not in seen_pages
                and parsed.scheme in ("http", "https")
                and not lower.endswith((".jpg", ".png", ".css", ".js"))
            ):
                queue.append(absolute)

    return results
