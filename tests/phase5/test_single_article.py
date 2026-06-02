"""Single-article policy and clarification edge cases."""

from api.rag.single_article import (
    build_clarification_answer,
    enforce_single_citation_answer,
    retrieval_is_ambiguous,
)
from api.rag.query_analysis import QueryAnalysis, QueryIntent
from pipeline.index.retrieval import ScoredChunk
from shared.schemas import ChunkMetadata, SourceOrg, VerificationStatus


def _hit(doc_suffix: str, distance: float) -> ScoredChunk:
    chunk = ChunkMetadata(
        chunk_id=f"sha256:doc{doc_suffix}::p1::c1",
        source_org=SourceOrg.NATURE,
        source_url=f"https://www.nature.com/articles/s41598-026-{doc_suffix}",
        document_title=f"Study {doc_suffix}",
        publication_year=2026,
        page_number=1,
        exact_context="Clinical findings were significant.",
        verification_status=VerificationStatus.UNVERIFIED,
    )
    return ScoredChunk(chunk=chunk, distance=distance)


def test_enforce_single_citation_strips_extra_markers():
    text = "**Summary:** A [1] and B [2].\n**Key points:**\n- x [1]\n- y [2]"
    out = enforce_single_citation_answer(text)
    assert "[2]" not in out
    assert "[1]" in out


def _analysis() -> QueryAnalysis:
    return QueryAnalysis(
        raw_query="test",
        intent=QueryIntent.GENERAL,
        source_org=SourceOrg.NATURE,
        target_date=None,
        enumeration=False,
    )


def test_ambiguous_when_two_docs_score_similarly():
    hits = [_hit("aaa", 0.2), _hit("bbb", 0.22)]
    assert retrieval_is_ambiguous(hits, _analysis(), document_id=None) is True


def test_not_ambiguous_when_document_id_set():
    hits = [_hit("aaa", 0.2), _hit("bbb", 0.22)]
    assert retrieval_is_ambiguous(hits, _analysis(), document_id="sha256:docaaa") is False


def test_not_ambiguous_when_second_doc_scores_much_worse():
    hits = [_hit("aaa", 0.2), _hit("bbb", 0.65)]
    assert retrieval_is_ambiguous(hits, _analysis(), document_id=None) is False


def test_clarification_message_asks_for_date_and_focus():
    msg = build_clarification_answer()
    assert "Publication date" in msg
    assert "Exact focus" in msg
