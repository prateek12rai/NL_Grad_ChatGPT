"""LIST-by-date queries should return deterministic multi-article sources."""

from datetime import date
from unittest.mock import MagicMock, patch

from api.rag.orchestrator import run_rag_query
from api.rag.query_analysis import QueryIntent
from pipeline.index.retrieval import ScoredChunk
from shared.schemas import ChunkMetadata, SourceOrg, VerificationStatus


def _hit(doc_id: str, title: str, exact_context: str = "Abstract: Example abstract text.") -> ScoredChunk:
    chunk = ChunkMetadata(
        chunk_id=f"{doc_id}::p0001::c0001",
        source_org=SourceOrg.NATURE,
        source_url=f"https://www.nature.com/articles/{doc_id}",
        document_title=title,
        publication_year=2026,
        page_number=1,
        exact_context=exact_context,
        verification_status=VerificationStatus.UNVERIFIED,
    )
    return ScoredChunk(chunk=chunk, distance=0.01)


def test_list_date_returns_multiple_sources_and_citations():
    store = MagicMock()
    hits = [_hit("sha256:a", "A"), _hit("sha256:b", "B"), _hit("sha256:c", "C")]
    with patch("api.rag.orchestrator.analyze_query") as analyze:
        analyze.return_value = MagicMock(
            raw_query="tell me more about 2026-06-01 articles",
                intent=QueryIntent.LIST,
            target_date=date(2026, 6, 1),
            source_org=None,
            enumeration=True,
        )
        with patch("api.rag.orchestrator.retrieve_from_manifest", return_value=hits):
            res = run_rag_query("tell me more about 2026-06-01 articles", chroma_store=store)
    assert res.out_of_corpus is False
    assert res.citations and len(res.citations) >= 2
    assert "**Sources:**" in res.answer


def test_list_date_with_topic_filters_unrelated_articles():
    store = MagicMock()
    hits = [
        _hit("sha256:a", "Cancer immunotherapy trial", "Abstract: cancer outcomes."),
        _hit("sha256:b", "Kidney segmentation model", "Abstract: imaging segmentation."),
    ]
    with patch("api.rag.orchestrator.analyze_query") as analyze:
        analyze.return_value = MagicMock(
            raw_query="any report on cancer form 2026-06-01",
            intent=QueryIntent.LIST,
            target_date=date(2026, 6, 1),
            source_org=None,
            enumeration=True,
        )
        with patch("api.rag.orchestrator.retrieve_from_manifest", return_value=hits):
            res = run_rag_query("any report on cancer form 2026-06-01", chroma_store=store)
    assert res.out_of_corpus is False
    assert len(res.citations) == 1
    assert "Cancer immunotherapy trial" in res.answer
    assert "Kidney segmentation" not in res.answer


def test_list_date_with_missing_topic_returns_pinky():
    store = MagicMock()
    hits = [_hit("sha256:b", "Kidney segmentation model", "Abstract: imaging segmentation.")]
    with patch("api.rag.orchestrator.analyze_query") as analyze:
        analyze.return_value = MagicMock(
            raw_query="any report on cancer form 2026-06-01",
            intent=QueryIntent.LIST,
            target_date=date(2026, 6, 1),
            source_org=None,
            enumeration=True,
        )
        with patch("api.rag.orchestrator.retrieve_from_manifest", return_value=hits):
            res = run_rag_query("any report on cancer form 2026-06-01", chroma_store=store)
    assert res.out_of_corpus is True
    assert res.citations == []


def test_list_date_returns_up_to_three_articles():
    store = MagicMock()
    hits = [_hit(f"sha256:{c}", t) for c, t in zip("abcd", ["A", "B", "C", "D"])]
    with patch("api.rag.orchestrator.analyze_query") as analyze:
        analyze.return_value = MagicMock(
            raw_query="show me all research articles published on 2026-06-01",
            intent=QueryIntent.LIST,
            target_date=date(2026, 6, 1),
            source_org=None,
            enumeration=True,
        )
        with patch("api.rag.orchestrator.retrieve_from_manifest", return_value=hits[:3]) as rfm:
            res = run_rag_query(
                "show me all research articles published on 2026-06-01", chroma_store=store
            )
    # Asked manifest for up to the configured list cap (3).
    assert rfm.call_args.kwargs["max_documents"] == 3
    assert res.out_of_corpus is False
    assert len(res.citations) == 3
    assert all(c.source_url for c in res.citations)


def test_list_date_with_no_data_returns_top3_not_found():
    store = MagicMock()
    with patch("api.rag.orchestrator.analyze_query") as analyze:
        analyze.return_value = MagicMock(
            raw_query="show me all research articles published on 2026-05-28",
            intent=QueryIntent.LIST,
            target_date=date(2026, 5, 28),
            source_org=None,
            enumeration=True,
        )
        # No article exists for that date.
        with patch("api.rag.orchestrator.retrieve_from_manifest", return_value=[]):
            res = run_rag_query(
                "show me all research articles published on 2026-05-28", chroma_store=store
            )
    assert res.out_of_corpus is True
    assert res.citations == []
    assert "don't have any articles for 2026-05-28" in res.answer
    # Top 3 verifiable articles offered as a fallback.
    assert len(res.suggested_queries) >= 1

