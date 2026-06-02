"""Relevance gate — out-of-corpus pinky promise triggers."""

from __future__ import annotations

from pipeline.index.retrieval import ScoredChunk
from shared.config import settings
from shared.schemas import ChunkMetadata, SourceOrg, VerificationStatus

from api.rag.query_analysis import analyze_query
from api.rag.relevance_gate import (
    is_corpus_enumeration_query,
    is_medical_research_query,
    llm_answer_is_out_of_corpus,
    query_chunk_overlap,
    retrieval_meets_threshold,
)


def _chunk(text: str) -> ChunkMetadata:
    return ChunkMetadata(
        chunk_id="doc::p0001::c0001",
        source_org=SourceOrg.NATURE,
        source_url="https://example.com",
        document_title="Test article",
        publication_year=2026,
        page_number=1,
        exact_context=text,
        verification_status=VerificationStatus.UNVERIFIED,
    )


def test_query_chunk_overlap_requires_shared_terms():
    q = "bedaquiline resistant tuberculosis treatment"
    body = "Bedaquiline-resistant tuberculosis requires new DOTS protocols."
    assert query_chunk_overlap(q, body) >= 0.25
    assert query_chunk_overlap(q, "quantum entanglement in photonics") == 0.0


def test_retrieval_meets_threshold_skipped_in_embed_mock(monkeypatch):
    monkeypatch.setattr(settings, "embed_mock", True)
    hits = [ScoredChunk(chunk=_chunk("x"), distance=0.99)]
    assert retrieval_meets_threshold(hits, "unrelated", mode="vector") is True


def test_retrieval_fails_on_low_similarity(monkeypatch):
    monkeypatch.setattr(settings, "embed_mock", False)
    monkeypatch.setattr(settings, "rag_ooc_min_similarity", 0.22)
    hits = [ScoredChunk(chunk=_chunk("some text about medicine"), distance=0.95)]
    assert retrieval_meets_threshold(hits, "quantum physics lasers", mode="vector") is False


def test_retrieval_fails_on_no_term_overlap(monkeypatch):
    monkeypatch.setattr(settings, "embed_mock", False)
    monkeypatch.setattr(settings, "rag_ooc_min_similarity", 0.01)
    monkeypatch.setattr(settings, "rag_ooc_min_term_overlap", 0.08)
    hits = [ScoredChunk(chunk=_chunk("cardiology stent outcomes"), distance=0.2)]
    assert retrieval_meets_threshold(hits, "quantum physics lasers", mode="vector") is False


def test_llm_refusal_triggers_pinky():
    assert llm_answer_is_out_of_corpus(
        "I do not have sufficient information in the provided context.",
        set(),
    )


def test_llm_empty_citation_triggers_pinky():
    assert llm_answer_is_out_of_corpus("Here is a summary without citation.", set())


def test_llm_refusal_with_citations_triggers_pinky():
    answer = (
        "The provided context does not contain information about pizza; "
        "indexed count: 20. **Top articles:** item [1] item [2]"
    )
    assert llm_answer_is_out_of_corpus(answer, {1, 2, 3})


def test_non_medical_query_rejected():
    assert is_medical_research_query("quantum computing qubits and entanglement") is False
    assert is_medical_research_query("who won the football match yesterday") is False


def test_pizza_query_is_not_medical_or_corpus_count():
    q = "How much pizza can a 2 year old kid eat in 3 days without getting sick?"
    analysis = analyze_query(q)
    assert analysis.enumeration is False
    assert is_medical_research_query(q, analysis) is False
    assert is_corpus_enumeration_query(q, analysis) is False


def test_medical_and_corpus_queries_accepted():
    assert is_medical_research_query("bedaquiline resistant tuberculosis treatment") is True
    analysis = analyze_query("how many Nature articles were published on 2026-06-01")
    assert is_medical_research_query("how many Nature articles were published on 2026-06-01", analysis) is True
