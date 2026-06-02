"""Download discovered items to data/corpus/{org}/ — real bytes from publisher sites."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import httpx

from shared.config import settings
from scraper.article_fetcher import extract_nature_article_html, is_nature_article_url
from scraper.models import ScrapedItem

# Only used when --fixture (unit tests / offline CI)
_MOCK_PDF = b"%PDF-1.4\n% fixture corpus for tests\n"


class DocumentDownloader:
    def __init__(
        self,
        corpus_root: Path | None = None,
        client: httpx.Client | None = None,
        mock_downloads: bool = False,
    ) -> None:
        self.corpus_root = corpus_root or Path(settings.corpus_path)
        self.client = client
        self.mock_downloads = mock_downloads

    def local_path_for(self, item: ScrapedItem, document_id: str) -> Path:
        org = item.source_org.value.lower()
        ext = ".pdf" if item.content_type == "pdf" else ".html"
        safe_name = document_id.replace(":", "_")
        dest_dir = self.corpus_root / org
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir / f"{safe_name}{ext}"

    def download(self, item: ScrapedItem, document_id: str) -> Path:
        dest = self.local_path_for(item, document_id)
        if dest.exists() and dest.stat().st_size > 64:
            return dest

        if self.mock_downloads:
            content = _MOCK_PDF if item.content_type == "pdf" else self._mock_html(item)
            dest.write_bytes(content)
            return dest

        if self.client is None:
            raise RuntimeError("httpx client required for live downloads")

        if item.content_type == "pdf":
            content = self._download_pdf(item.source_url)
        elif is_nature_article_url(item.source_url):
            content = self._download_nature_article(item)
        else:
            response = self.client.get(item.source_url)
            response.raise_for_status()
            content = response.content

        dest.write_bytes(content)
        return dest

    def _download_pdf(self, url: str) -> bytes:
        response = self.client.get(url)  # type: ignore[union-attr]
        response.raise_for_status()
        data = response.content
        if not data.startswith(b"%PDF"):
            raise ValueError(f"URL did not return a valid PDF: {url}")
        return data

    def _download_nature_article(self, item: ScrapedItem) -> bytes:
        response = self.client.get(item.source_url)  # type: ignore[union-attr]
        response.raise_for_status()
        return extract_nature_article_html(
            response.text,
            title=item.document_title,
            source_url=item.source_url,
        )

    @staticmethod
    def _mock_html(item: ScrapedItem) -> bytes:
        body = (
            f"<html><head><title>{item.document_title}</title></head>"
            f"<body><p>Fixture content for {item.source_org.value} (not for production).</p></body></html>"
        )
        return body.encode("utf-8")

    @staticmethod
    def infer_content_type(url: str) -> str:
        path = urlparse(url).path.lower()
        if path.endswith(".pdf"):
            return "pdf"
        return "html"
