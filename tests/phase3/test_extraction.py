"""Phase 3.1 — text extraction tests (architecture §7)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.chunking.exceptions import (
    EmptyDocumentError,
    FileNotFoundExtractionError,
)
from pipeline.chunking.extractors import extract_document
from pipeline.chunking.extractors.html_extractor import HtmlExtractor
from pipeline.chunking.extractors.normalize import normalize_page_text
from pipeline.chunking.extractors.pdf_extractor import PdfExtractor
from pipeline.chunking.models import PageText


def test_normalize_page_text_rules():
    raw = "Line one\r\nLine two  with   spaces\x00hidden"
    out = normalize_page_text(raw)
    assert "\r" not in out
    assert "  " not in out
    assert "\x00" not in out
    assert "Line one" in out
    assert "Line two with spaceshidden" in out.replace("  ", " ")


def test_normalize_empty_returns_empty():
    assert normalize_page_text("") == ""
    assert normalize_page_text("   \n  ") == ""


def test_html_extractor_sections(sample_html_path: Path):
    result = HtmlExtractor().extract(sample_html_path)
    assert not result.is_empty
    assert len(result.pages) >= 2
    assert result.pages[0].page_number == 1
    texts = " ".join(p.text for p in result.pages)
    assert "Contraindications" in texts
    assert "Bedaquiline" in texts
    assert "Navigation should be removed" not in texts
    assert result.pages[0].source_path.endswith("sample_page.html")


def test_html_extractor_single_page_body(tmp_path: Path):
    html = tmp_path / "simple.html"
    html.write_text(
        "<html><body><p>Clinical guidance for DOTS.</p></body></html>",
        encoding="utf-8",
    )
    result = HtmlExtractor().extract(html)
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "DOTS" in result.pages[0].text


def test_html_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundExtractionError):
        HtmlExtractor().extract(tmp_path / "missing.html")


def test_pdf_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundExtractionError):
        PdfExtractor().extract(tmp_path / "missing.pdf")


def test_pdf_extractor_pdfplumber_primary(tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page one TB guidelines."

    mock_pdf = MagicMock()
    mock_pdf.is_encrypted = False
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdfplumber.open", return_value=mock_pdf):
        result = PdfExtractor().extract(pdf_path)

    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "TB guidelines" in result.pages[0].text


def test_pdf_empty_raises_empty_document(tmp_path: Path):
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    mock_pdf = MagicMock()
    mock_pdf.is_encrypted = False
    mock_pdf.pages = []
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    mock_reader = MagicMock()
    mock_reader.is_encrypted = False
    mock_reader.pages = []

    with patch("pdfplumber.open", return_value=mock_pdf):
        with patch("pypdf.PdfReader", return_value=mock_reader):
            with pytest.raises(EmptyDocumentError):
                PdfExtractor().extract(pdf_path)


def test_extract_document_factory_html(sample_html_path: Path):
    result = extract_document(sample_html_path, "html")
    assert result.extractor_name == "html"
    assert len(result.pages) >= 1


def test_extract_document_unsupported_type(sample_html_path: Path):
    with pytest.raises(ValueError, match="Unsupported"):
        extract_document(sample_html_path, "docx")


def test_corpus_nature_html_if_present(corpus_nature_html: Path | None):
    if corpus_nature_html is None:
        pytest.skip("No Nature HTML in data/corpus")
    result = extract_document(corpus_nature_html, "html")
    assert len(result.pages) >= 1
    text = result.pages[0].text
    assert len(text.strip()) > 100
    assert any(
        token in text.lower()
        for token in ("abstract", "background", "methods", "results", "nature", "mock")
    )


def test_sample_pdf_if_present(sample_pdf_path: Path):
    result = extract_document(sample_pdf_path, "pdf")
    assert len(result.pages) >= 1
    assert any("TB" in p.text or "Contraindications" in p.text for p in result.pages)
