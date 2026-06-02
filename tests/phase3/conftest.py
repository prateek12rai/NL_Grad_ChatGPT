"""Phase 3 test fixtures."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "phase3"


@pytest.fixture
def sample_html_path() -> Path:
    return FIXTURES / "sample_page.html"


@pytest.fixture
def sample_pdf_path() -> Path:
    path = FIXTURES / "sample_guideline.pdf"
    if not path.exists():
        pytest.skip(
            "sample_guideline.pdf missing — run: pip install fpdf2 && "
            "python scripts/generate_phase3_pdf_fixture.py"
        )
    return path


@pytest.fixture
def corpus_nature_html() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    nature_dir = root / "data" / "corpus" / "nature"
    if not nature_dir.is_dir():
        return None
    files = list(nature_dir.glob("*.html"))
    return files[0] if files else None
