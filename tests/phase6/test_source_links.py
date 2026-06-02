"""Source URL resolution for legacy Nature fixtures."""

from shared.source_links import (
    FIXTURE_URL_REPLACEMENTS,
    is_legacy_fixture_nature_url,
    resolve_source_url,
)


def test_legacy_fixture_detected():
    assert is_legacy_fixture_nature_url(
        "https://www.nature.com/articles/d41586-026-00001-0"
    )


def test_resolve_to_real_nature_article():
    old = "https://www.nature.com/articles/d41586-026-00002-8"
    resolved = resolve_source_url(old)
    assert resolved == FIXTURE_URL_REPLACEMENTS[old]
    assert "s41467-026-70664-0" in resolved
