"""Phase 2.7.1 — Adapter unit tests with mocked HTML."""

from scraper.adapters.dhr import DHRAdapter
from scraper.adapters.icmr import ICMRAdapter
from scraper.adapters.nature import NatureAdapter
from shared.schemas import SourceOrg


def test_dhr_adapter_parses_fixture(phase2_html):
    adapter = DHRAdapter(fixture_html=phase2_html["dhr"])
    items = adapter.discover()
    assert len(items) >= 2
    assert all(i.source_org == SourceOrg.DHR for i in items)
    assert items[0].publication_date >= items[1].publication_date


def test_icmr_adapter_parses_fixture(phase2_html):
    adapter = ICMRAdapter(fixture_html=phase2_html["icmr"])
    items = adapter.discover()
    assert len(items) >= 2
    assert all(i.source_org == SourceOrg.ICMR for i in items)
    assert any(".pdf" in i.source_url for i in items)


def test_nature_adapter_parses_fixture(phase2_html):
    adapter = NatureAdapter(fixture_html=phase2_html["nature"])
    items = adapter.discover()
    assert len(items) >= 2
    assert all(i.source_org == SourceOrg.NATURE for i in items)
    assert all("/articles/" in i.source_url for i in items)
