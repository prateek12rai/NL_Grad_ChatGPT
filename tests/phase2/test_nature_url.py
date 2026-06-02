"""Phase 2.7.4 — Nature URL must use portfolio last_30_days search."""

from urllib.parse import parse_qs, urlparse

from scraper.adapters.nature import (
    NATURE_SEARCH_URL,
    NatureAdapter,
    assert_nature_url_compliant,
)


def test_nature_search_url_contains_last_30_days():
    parsed = urlparse(NATURE_SEARCH_URL)
    params = parse_qs(parsed.query)
    assert params.get("date_range") == ["last_30_days"]
    assert params.get("subject") == ["medical-research"]


def test_assert_nature_url_compliant_passes():
    assert_nature_url_compliant(NATURE_SEARCH_URL)


def test_assert_nature_url_compliant_rejects_last_7_days():
    bad = NATURE_SEARCH_URL.replace("last_30_days", "last_7_days")
    try:
        assert_nature_url_compliant(bad)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_nature_adapter_rejects_invalid_url_at_init():
    bad = "https://www.nature.com/search?subject=medical-research"
    try:
        NatureAdapter(search_url=bad)
        created = True
    except ValueError:
        created = False
    assert not created
