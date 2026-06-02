"""Pre-retrieval query understanding and manifest search."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from api.rag.query_analysis import QueryIntent, analyze_query
from pipeline.index.manifest_search import retrieve_from_manifest
from shared.schemas import SourceOrg


def test_analyze_nature_count_query():
    a = analyze_query("how many reports have been published on nature on 1 june 2026")
    assert a.intent == QueryIntent.COUNT
    assert a.source_org == SourceOrg.NATURE
    assert a.target_date == date(2026, 6, 1)
    assert a.enumeration is True


@pytest.mark.skipif(
    not Path("data/manifest.json").is_file(),
    reason="requires manifest",
)
def test_manifest_nature_june_2026_returns_indexed_documents():
    hits = retrieve_from_manifest(
        source_org=SourceOrg.NATURE,
        target_date=date(2026, 6, 1),
        max_documents=6,
    )
    assert len(hits) >= 1
    titles = {h.chunk.document_title for h in hits}
    assert len(titles) == len(hits)
