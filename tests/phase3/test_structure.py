"""Phase 3.2 — structure detection tests (architecture §8)."""

from pathlib import Path

import pytest

from pipeline.chunking.extractors import extract_document
from pipeline.chunking.models import PageText
from pipeline.chunking.structure.detector import StructureDetector, is_heading
from pipeline.chunking.structure import detect_sections


@pytest.mark.parametrize(
    "line,expected",
    [
        ("# Introduction", True),
        ("## Methods", True),
        ("1. Background", True),
        ("2.3 Treatment Protocol", True),
        ("Contraindications", True),
        ("CONTRAINDICATIONS", True),
        ("RECOMMENDATIONS", True),
        ("For multi-drug resistant strains, administer Bedaquiline.", False),
        ("short", False),
        ("", False),
    ],
)
def test_is_heading(line: str, expected: bool):
    assert is_heading(line) is expected


def test_detect_page_numbered_and_medical_headers():
    text = Path(__file__).resolve().parents[1] / "fixtures" / "phase3" / "sample_guideline_structure.txt"
    page = PageText(page_number=1, text=text.read_text(encoding="utf-8"), source_path="fixture.txt")
    spans = StructureDetector().detect_page(page)

    titles = [s.title for s in spans if s.title]
    assert "Introduction" in titles
    assert any("CONTRAINDICATIONS" in (t or "").upper() for t in titles)
    assert any("Recommendations" in (t or "") for t in titles)

    contra = next(s for s in spans if s.title and "CONTRAINDICATION" in s.title.upper())
    assert "Bedaquiline" in contra.text
    assert "DOTS" in contra.text


def test_short_section_merged_into_previous():
    page = PageText(
        page_number=1,
        text="Introduction\n\nShort.\n\nCONTRAINDICATIONS\n\nLong text about Bedaquiline and DOTS monitoring.",
        source_path="t.txt",
    )
    spans = StructureDetector(min_section_chars=20).detect_page(page)
    assert len(spans) <= 3
    merged_text = " ".join(s.text for s in spans)
    assert "Bedaquiline" in merged_text


def test_no_headings_single_span():
    page = PageText(
        page_number=1,
        text="Single paragraph clinical guidance without headings.",
        source_path="t.txt",
    )
    spans = StructureDetector().detect_page(page)
    assert len(spans) == 1
    assert spans[0].title is None
    assert spans[0].start_char == 0
    assert spans[0].end_char == len(page.text)


def test_section_offsets_within_page():
    page = PageText(
        page_number=2,
        text="Introduction\n\nBody paragraph one.\n\nContraindications\n\nBody paragraph two.",
        source_path="t.txt",
    )
    spans = StructureDetector().detect_page(page)
    for span in spans:
        assert 0 <= span.start_char <= span.end_char <= len(page.text)
        assert span.text in page.text or page.text[span.start_char : span.end_char].strip() in span.text


def test_detect_sections_multi_page():
    pages = [
        PageText(page_number=1, text="Introduction\n\nPage one body.", source_path="a"),
        PageText(page_number=2, text="Recommendations\n\nPage two body.", source_path="a"),
    ]
    spans = detect_sections(pages)
    assert len(spans) >= 2
    assert {s.page_number for s in spans} == {1, 2}


def test_html_extract_then_detect_sections(sample_html_path: Path):
    extracted = extract_document(sample_html_path, "html")
    spans = detect_sections(extracted.pages)
    assert len(spans) >= 2
    assert any(s.title and "Contraindications" in s.title for s in spans)


def test_pdf_extract_then_detect_sections(sample_pdf_path: Path):
    extracted = extract_document(sample_pdf_path, "pdf")
    spans = detect_sections(extracted.pages)
    assert len(spans) >= 1
    all_text = " ".join(s.text for s in spans)
    assert "TB" in all_text or "Contraindications" in all_text
