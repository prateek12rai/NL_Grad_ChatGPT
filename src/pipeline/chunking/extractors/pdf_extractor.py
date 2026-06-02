"""PDF text extraction — pdfplumber primary, pypdf fallback (§7.5)."""

from __future__ import annotations

import logging
from pathlib import Path

from pipeline.chunking.exceptions import (
    EmptyDocumentError,
    EncryptedPdfError,
    FileNotFoundExtractionError,
)
from pipeline.chunking.extractors.base import BaseExtractor
from pipeline.chunking.extractors.normalize import normalize_page_text
from pipeline.chunking.models import ExtractionResult, PageText

logger = logging.getLogger(__name__)


class PdfExtractor(BaseExtractor):
    name = "pdf"

    def extract(self, path: Path) -> ExtractionResult:
        if not path.is_file():
            raise FileNotFoundExtractionError(f"PDF not found: {path}")

        source_path = path.as_posix()
        warnings: list[str] = []
        pages: list[PageText] = []

        try:
            pages = self._extract_pdfplumber(path, source_path)
        except EncryptedPdfError:
            raise
        except Exception as exc:
            warnings.append(f"pdfplumber failed: {exc}")
            logger.warning("pdfplumber failed for %s: %s", path, exc)

        if not pages:
            try:
                pages = self._extract_pypdf(path, source_path)
            except EncryptedPdfError:
                raise
            except Exception as exc:
                warnings.append(f"pypdf failed: {exc}")
                logger.warning("pypdf failed for %s: %s", path, exc)

        if not pages:
            raise EmptyDocumentError(f"No text extracted from PDF: {path}")

        return ExtractionResult(
            pages=pages,
            warnings=warnings,
            extractor_name=self.name,
        )

    def _extract_pdfplumber(self, path: Path, source_path: str) -> list[PageText]:
        import pdfplumber

        pages: list[PageText] = []
        with pdfplumber.open(path) as pdf:
            if getattr(pdf, "is_encrypted", False):
                raise EncryptedPdfError(str(path))
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    raw = page.extract_text() or ""
                except Exception as exc:
                    logger.warning("pdfplumber page %s failed: %s", i, exc)
                    continue
                text = normalize_page_text(raw)
                if text:
                    pages.append(
                        PageText(page_number=i, text=text, source_path=source_path)
                    )
        return pages

    def _extract_pypdf(self, path: Path, source_path: str) -> list[PageText]:
        from pypdf import PdfReader
        from pypdf.errors import FileNotDecryptedError

        pages: list[PageText] = []
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                if reader.decrypt("") == 0:
                    raise EncryptedPdfError(str(path))
            except FileNotDecryptedError as exc:
                raise EncryptedPdfError(str(path)) from exc

        for i, page in enumerate(reader.pages, start=1):
            try:
                raw = page.extract_text() or ""
            except Exception as exc:
                logger.warning("pypdf page %s failed: %s", i, exc)
                continue
            text = normalize_page_text(raw)
            if text:
                pages.append(
                    PageText(page_number=i, text=text, source_path=source_path)
                )
        return pages
