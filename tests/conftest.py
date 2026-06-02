"""Shared pytest fixtures and live API budget enforcement."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from live_api_budget import (
    MAX_LIVE_API_CALLS,
    consume_live_api_call,
    reset_live_api_budget,
    total_consumed,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live: real Groq/Hugging Face API (strict 3-5 call budget; opt-in only)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip live tests unless explicitly requested with ``-m live``."""
    markexpr = config.getoption("-m", default="")
    if "live" in markexpr and "not live" not in markexpr.replace(" ", ""):
        return
    # Default run: skip live-marked tests
    skip_live = pytest.mark.skip(
        reason="Live API tests skipped (use: pytest -m live). Default saves API quota."
    )
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session", autouse=True)
def _live_api_budget_session() -> None:
    reset_live_api_budget()
    yield
    if total_consumed() > 0:
        print(
            f"\n[live_api_budget] consumed {total_consumed()}/{MAX_LIVE_API_CALLS} "
            "real API call(s) this session"
        )


@pytest.fixture
def live_api_call(request: pytest.FixtureRequest) -> None:
    """
    Call once per live test — hard stop after MAX_LIVE_API_CALLS (default 5).

    Raises pytest.skip if budget exhausted (safer than silent pass).
    """
    from live_api_budget import remaining_calls

    if remaining_calls() <= 0:
        pytest.skip(
            f"Live API budget exhausted ({MAX_LIVE_API_CALLS} calls max per test run)"
        )
    consume_live_api_call(request.node.nodeid)
    yield


@pytest.fixture
def tmp_chroma_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated Chroma directory per test."""
    chroma_dir = tmp_path / "chroma_test"
    path_str = str(chroma_dir)
    monkeypatch.setenv("CHROMA_PATH", path_str)
    from shared.config import settings

    settings.chroma_path = path_str
    return chroma_dir


@pytest.fixture(autouse=True)
def _force_mock_apis_by_default(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    """
    Unless ``-m live``, force mock modes so unit tests never hit real APIs.
    """
    if "live" in request.node.keywords:
        return
    monkeypatch.setenv("GROQ_MOCK", "true")
    monkeypatch.setenv("EMBED_MOCK", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-key-for-unit-tests")
    from shared.config import settings

    settings.groq_mock = True
    settings.embed_mock = True
    settings.groq_api_key = "test-key-for-unit-tests"


@pytest.fixture(autouse=True)
def _restore_settings_after_test():
    """Prevent settings mutations from leaking between tests."""
    from shared.config import settings

    snapshot = {
        "chroma_path": settings.chroma_path,
        "chunk_index_path": settings.chunk_index_path,
        "corpus_path": settings.corpus_path,
        "groq_mock": settings.groq_mock,
        "embed_mock": settings.embed_mock,
        "groq_api_key": settings.groq_api_key,
    }
    yield
    for key, value in snapshot.items():
        setattr(settings, key, value)
