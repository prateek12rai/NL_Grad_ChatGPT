"""Phase 2 fixtures."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "phase2"


@pytest.fixture
def phase2_html() -> dict[str, str]:
    return {
        "dhr": (FIXTURES / "dhr_listing.html").read_text(encoding="utf-8"),
        "icmr": (FIXTURES / "icmr_listing.html").read_text(encoding="utf-8"),
        "nature": (FIXTURES / "nature_listing.html").read_text(encoding="utf-8"),
    }


@pytest.fixture
def phase2_data_dir(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    (data / "corpus").mkdir()
    return data
