"""Phase 3.1 — document text extractors."""

from __future__ import annotations

from pathlib import Path

from pipeline.chunking.exceptions import ExtractionError
from pipeline.chunking.extractors.html_extractor import HtmlExtractor
from pipeline.chunking.extractors.pdf_extractor import PdfExtractor
from pipeline.chunking.models import ExtractionResult

_EXTRACTORS = {
    "pdf": PdfExtractor(),
    "html": HtmlExtractor(),
}


def get_extractor(content_type: str) -> PdfExtractor | HtmlExtractor:
    key = content_type.lower().strip()
    if key not in _EXTRACTORS:
        raise ValueError(f"Unsupported content_type: {content_type}")
    return _EXTRACTORS[key]


def extract_document(path: Path, content_type: str) -> ExtractionResult:
    """
    Extract normalized pages from a corpus file.

    Raises FileNotFoundExtractionError, EmptyDocumentError, EncryptedPdfError.
    """
    extractor = get_extractor(content_type)
    return extractor.extract(path.resolve())


__all__ = [
    "PdfExtractor",
    "HtmlExtractor",
    "extract_document",
    "get_extractor",
    "ExtractionError",
]
