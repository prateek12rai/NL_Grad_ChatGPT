"""Clarification → retry → answer or pinky promise."""

from unittest.mock import MagicMock, patch

import pytest

from api.rag.orchestrator import run_rag_query
from api.sessions.store import session_store
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
        exact_context="Clinical findings were significant for the trial endpoints.",
        verification_status=VerificationStatus.UNVERIFIED,
    )
    return ScoredChunk(chunk=chunk, distance=distance)


@pytest.fixture(autouse=True)
def _clear_sessions():
    session_store.clear()
    yield
    session_store.clear()


def test_first_ambiguous_query_returns_clarification():
    hits = [_hit("aaa", 0.2), _hit("bbb", 0.22)]
    store = MagicMock()
    with patch("api.rag.orchestrator.retrieve_for_rag", return_value=(hits, "vector")):
        result = run_rag_query("vague screening question", chroma_store=store)
    assert result.needs_clarification is True
    assert "Clarification needed" in result.answer
    assert result.out_of_corpus is False
    prior = session_store.get(result.session_id)
    assert prior is not None
    assert prior.awaiting_clarification is True


def test_second_ambiguous_follow_up_returns_pinky_not_clarification_again():
    hits = [_hit("aaa", 0.2), _hit("bbb", 0.22)]
    store = MagicMock()
    with patch("api.rag.orchestrator.retrieve_for_rag", return_value=(hits, "vector")):
        first = run_rag_query("vague screening question", chroma_store=store)
    assert first.needs_clarification is True
    with patch("api.rag.orchestrator.retrieve_for_rag", return_value=(hits, "vector")):
        second = run_rag_query(
            "still vague screening question",
            prior_session_id=first.session_id,
            chroma_store=store,
        )
    assert second.out_of_corpus is True
    assert second.needs_clarification is False
    assert "Pinky promise" in second.answer


def test_pizza_starter_query_returns_pinky_no_citations():
    store = MagicMock()
    with patch("api.rag.orchestrator.retrieve_for_rag") as retrieve:
        result = run_rag_query(
            "How much pizza can a 2 year old kid eat in 3 days without getting sick?",
            chroma_store=store,
        )
    retrieve.assert_not_called()
    assert result.out_of_corpus is True
    assert len(result.citations) == 0
    assert "Pinky promise" in result.answer


def test_non_medical_query_skips_clarification_and_groq():
    hits = [_hit("aaa", 0.2), _hit("bbb", 0.22)]
    store = MagicMock()
    with patch("api.rag.orchestrator.retrieve_for_rag", return_value=(hits, "vector")) as retrieve:
        result = run_rag_query("quantum computing qubits", chroma_store=store)
    retrieve.assert_not_called()
    assert result.out_of_corpus is True
    assert result.needs_clarification is False
    assert len(result.citations) == 0
    assert "Pinky promise" in result.answer


def test_retry_unknown_article_returns_pinky_promise():
    hits = [_hit("aaa", 0.2), _hit("bbb", 0.22)]
    store = MagicMock()
    with patch("api.rag.orchestrator.retrieve_for_rag", return_value=(hits, "vector")):
        first = run_rag_query("vague screening question", chroma_store=store)
    unknown_query = (
        "Validating the ADFSCI hypotension symptom domain\n"
        "Published: 01 June 2026\nmain findings"
    )
    with patch("api.rag.orchestrator.retrieve_for_rag", return_value=(hits, "vector")):
        second = run_rag_query(
            unknown_query,
            prior_session_id=first.session_id,
            chroma_store=store,
        )
    assert second.out_of_corpus is True
    assert "Pinky promise" in second.answer
