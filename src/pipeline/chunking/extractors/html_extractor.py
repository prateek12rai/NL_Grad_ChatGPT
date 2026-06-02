"""HTML text extraction — BeautifulSoup (§7.6)."""

from __future__ import annotations

import logging
from pathlib import Path

from bs4 import BeautifulSoup

from pipeline.chunking.exceptions import EmptyDocumentError, FileNotFoundExtractionError
from pipeline.chunking.extractors.base import BaseExtractor
from pipeline.chunking.extractors.normalize import normalize_page_text
from pipeline.chunking.models import ExtractionResult, PageText

logger = logging.getLogger(__name__)

_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "iframe", "aside", "form"}
# Nature.com sidebar, metrics, share widgets — not article body
_STRIP_SELECTORS = (
    "[data-test='sidebar']",
    ".c-article-sidebar",
    ".c-article-metrics",
    ".c-article-info-details",
    ".c-article-identifiers",
    ".c-article-references",
    ".c-article-section__figure",
    ".c-bibliographic-information",
    ".c-share-box",
    ".c-article-share-box",
    ".c-article-actions",
    ".c-article-subject-collection",
    ".u-hide-print",
    "[data-track-action='share']",
    "[aria-label*='Share']",
    "[class*='cookie']",
    "[class*='newsletter']",
    "[class*='subscribe']",
)
_BLOCK_TAGS = {
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "div",
    "section",
    "article",
    "blockquote",
    "pre",
    "table",
    "tr",
}
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class HtmlExtractor(BaseExtractor):
    name = "html"

    def extract(self, path: Path) -> ExtractionResult:
        if not path.is_file():
            raise FileNotFoundExtractionError(f"HTML not found: {path}")

        raw_html = path.read_text(encoding="utf-8", errors="replace")
        source_path = path.as_posix()
        soup = BeautifulSoup(raw_html, "lxml")

        for tag in soup.find_all(_STRIP_TAGS):
            tag.decompose()

        for selector in _STRIP_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

        pages = self._extract_by_sections(soup, source_path)
        if not pages:
            pages = self._extract_single_body(soup, source_path)

        if not pages:
            raise EmptyDocumentError(f"No text extracted from HTML: {path}")

        return ExtractionResult(pages=pages, extractor_name=self.name)

    def _extract_by_sections(self, soup: BeautifulSoup, source_path: str) -> list[PageText]:
        """One PageText per heading-led section; page_number = section index."""
        headings = soup.find_all(_HEADING_TAGS)
        if not headings:
            return []

        pages: list[PageText] = []
        section_index = 0

        for heading in headings:
            section_index += 1
            parts = [heading.get_text(separator=" ", strip=True)]
            for sibling in heading.find_next_siblings():
                if sibling.name in _HEADING_TAGS:
                    break
                if sibling.name:
                    parts.append(sibling.get_text(separator=" ", strip=True))
            text = normalize_page_text("\n\n".join(p for p in parts if p))
            if text:
                pages.append(
                    PageText(
                        page_number=section_index,
                        text=text,
                        source_path=source_path,
                    )
                )
        return pages

    def _extract_single_body(self, soup: BeautifulSoup, source_path: str) -> list[PageText]:
        """Fallback: flatten block elements into one virtual page."""
        body = soup.find("body") or soup
        blocks: list[str] = []
        for el in body.find_all(_BLOCK_TAGS):
            line = el.get_text(separator=" ", strip=True)
            if line:
                blocks.append(line)
        if not blocks:
            line = body.get_text(separator="\n", strip=True)
            if line:
                blocks.append(line)
        text = normalize_page_text("\n\n".join(blocks))
        if not text:
            return []
        return [PageText(page_number=1, text=text, source_path=source_path)]
