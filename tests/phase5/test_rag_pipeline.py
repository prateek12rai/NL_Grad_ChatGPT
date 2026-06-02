"""RAG pipeline: retrieval diversity, context selection, embedding compatibility."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.index.context_select import is_low_quality_chunk, select_context_chunks
from pipeline.index.hybrid_retrieval import retrieval_mode, retrieve_for_rag
from pipeline.index.index_profile import index_has_live_embeddings, query_embedding_compatible
from pipeline.index.lexical import _load_lexical_rows, retrieve_lexical
from pipeline.index.retrieval import ScoredChunk
from shared.schemas import ChunkMetadata, SourceOrg, VerificationStatus


@pytest.fixture
def clear_lexical_cache():
    _load_lexical_rows.cache_clear()
    yield
    _load_lexical_rows.cache_clear()


@pytest.mark.skipif(
    not Path("data/chunks/index.json").is_file(),
    reason="requires built corpus under data/chunks",
)
def test_lexical_gentrification_query_finds_nature_article(clear_lexical_cache):
    hits = retrieve_lexical(
        "gentrification infant mortality Michigan neighborhood",
        top_k=5,
    )
    assert len(hits) >= 1
    top_title = hits[0].chunk.document_title.lower()
    assert "gentrification" in top_title or "michigan" in top_title or "mortality" in top_title


@pytest.mark.skipif(
    not Path("data/chunks/index.json").is_file(),
    reason="requires built corpus under data/chunks",
)
def test_lexical_different_queries_differ(clear_lexical_cache):
    h1 = retrieve_lexical("gentrification infant mortality Michigan", top_k=3)
    h2 = retrieve_lexical("LILRB4 leukemia STAR T-cell therapy", top_k=3)
    assert h1 and h2
    ids1 = {h.chunk.chunk_id for h in h1}
    ids2 = {h.chunk.chunk_id for h in h2}
    assert ids1 != ids2


def test_select_context_dedupes_per_document():
    def _hit(doc: str, sim: float) -> ScoredChunk:
        chunk = ChunkMetadata(
            chunk_id=f"id-{doc}-{sim}",
            source_org=SourceOrg.ICMR,
            source_url="https://example.org",
            document_title=f"Quality document about {doc}",
            publication_year=2026,
            page_number=1,
            exact_context="x" * 80,
            verification_status=VerificationStatus.UNVERIFIED,
        )
        return ScoredChunk(chunk=chunk, distance=1.0 - sim)

    hits = [
        _hit("a", 0.9),
        _hit("a", 0.85),
        _hit("a", 0.8),
        _hit("b", 0.75),
        _hit("c", 0.7),
    ]
    selected = select_context_chunks(hits, max_chunks=5, max_per_document=2, min_similarity=0.0)
    titles = [h.chunk.document_title for h in selected]
    assert titles.count("Quality document about a") == 2
    assert len(selected) >= 3


def test_low_quality_title_filtered():
    from shared.document_titles import is_low_quality_title

    assert is_low_quality_title("(39.8 MB)")
    chunk = ChunkMetadata(
        chunk_id="x",
        source_org=SourceOrg.DHR,
        source_url="",
        document_title="(39.8 MB)",
        publication_year=2026,
        page_number=1,
        exact_context="x" * 20,
        verification_status=VerificationStatus.UNVERIFIED,
    )
    assert is_low_quality_chunk(chunk)


def test_phase5_fixture_uses_vector_mode(phase5_indexed_chroma):
    store = phase5_indexed_chroma["store"]
    assert query_embedding_compatible(store)
    assert retrieval_mode(store) == "vector"
    assert not index_has_live_embeddings(store)


def test_phase5_fixture_retrieval_returns_fixture_chunk(phase5_indexed_chroma):
    store = phase5_indexed_chroma["store"]
    hits, mode = retrieve_for_rag("Bedaquiline DOTS", store=store)
    assert mode == "vector"
    assert hits
    assert any("Bedaquiline" in h.chunk.exact_context for h in hits)
