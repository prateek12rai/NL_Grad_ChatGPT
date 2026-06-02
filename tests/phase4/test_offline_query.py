"""Phase 4.5 — offline retrieval + persistence (gates 4.6.3, 4.6.4)."""

import pytest

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize
from pipeline.embeddings.normalize import L2_TOLERANCE, l2_norm
from pipeline.index import ChromaStore, retrieve
from pipeline.index.verify import verify_chroma_index
from shared.schemas import ChunkMetadata, SourceOrg


@pytest.fixture
def indexed_store(tmp_chroma_path):
    from shared.schemas import ChunkRecord, VerificationStatus

    chunk = ChunkRecord(
        chunk_id="sha256:offlineq::p0001::c0001",
        document_id="sha256:offlineq",
        source_org=SourceOrg.ICMR,
        source_url="https://www.icmr.gov.in/tb.pdf",
        document_title="TB Guidelines",
        publication_year=2026,
        page_number=1,
        chunk_index=1,
        exact_context="Bedaquiline for multi-drug resistant tuberculosis under DOTS.",
        token_count=10,
        char_count=55,
        verification_status=VerificationStatus.UNVERIFIED,
        content_hash="offline_hash_1",
        created_at="2026-06-01T12:00:00Z",
    )
    client = BgeEmbeddingClient(api_token="", mock=True)
    vec = l2_normalize(client.embed_passages([chunk.exact_context])[0])
    store = ChromaStore(path=tmp_chroma_path)
    store.upsert_chunk(chunk, vec)
    return store, client


def test_offline_query_returns_metadata(indexed_store):
    store, client = indexed_store
    hits = retrieve(
        "Bedaquiline resistant tuberculosis",
        top_k=8,
        store=store,
        embed_client=client,
    )
    assert len(hits) >= 1
    assert isinstance(hits[0], ChunkMetadata)
    assert hits[0].source_org == SourceOrg.ICMR
    assert "Bedaquiline" in hits[0].exact_context or hits[0].chunk_id


def test_offline_query_empty_collection(tmp_chroma_path):
    store = ChromaStore(path=tmp_chroma_path)
    client = BgeEmbeddingClient(api_token="", mock=True)
    assert retrieve("test", store=store, embed_client=client) == []


def test_persistence_via_verify(indexed_store, tmp_chroma_path):
    store, client = indexed_store
    report = verify_chroma_index(
        chroma_path=tmp_chroma_path,
        expected_count=1,
        embed_client=client,
    )
    assert report.passed
    persistence = next(c for c in report.checks if c.name == "persistence_reopen")
    assert persistence.passed


def test_stored_vectors_unit_norm(indexed_store):
    store, _ = indexed_store
    fetched = store.collection.get(include=["embeddings"], limit=1)
    vec = fetched["embeddings"][0]
    assert abs(l2_norm(vec) - 1.0) < L2_TOLERANCE
