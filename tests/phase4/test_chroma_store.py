"""Phase 4.3 — Chroma PersistentClient, collection, mapper (architecture §9)."""

import json
from pathlib import Path

import pytest

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize
from pipeline.index import (
    COLLECTION_METADATA,
    ChromaStore,
    build_upsert_payload,
    chunk_to_chroma_metadata,
    get_medical_collection,
)
from pipeline.index.chroma_store import get_chroma_client
from shared.config import settings
from shared.schemas import ChunkRecord, SourceOrg, VerificationStatus


@pytest.fixture
def sample_chunk() -> ChunkRecord:
    return ChunkRecord(
        chunk_id="sha256:test::p0001::c0001",
        document_id="sha256:test",
        source_org=SourceOrg.ICMR,
        source_url="https://www.icmr.gov.in/example.pdf",
        document_title="TB Guidelines",
        publication_year=2026,
        page_number=24,
        chunk_index=1,
        exact_context="For multi-drug resistant strains, administer Bedaquiline under DOTS.",
        token_count=12,
        char_count=60,
        verification_status=VerificationStatus.UNVERIFIED,
        content_hash="abc123",
        created_at="2026-06-01T12:00:00Z",
    )


@pytest.fixture
def unit_embedding() -> list[float]:
    client = BgeEmbeddingClient(api_token="", mock=True)
    return l2_normalize(client.embed_passages(["test passage"])[0])


def test_collection_metadata_cosine(tmp_chroma_path):
    collection = get_medical_collection()
    assert collection.name == "india_medical_local"
    meta = collection.metadata or {}
    assert meta.get("hnsw:space") == "cosine"
    assert meta.get("schema_version") == "1"
    expected = f"mock:{settings.embed_model_id}" if settings.embed_mock else settings.embed_model_id
    assert meta.get("embedding_model") == expected


def test_mapper_prf_fields(sample_chunk: ChunkRecord):
    meta = chunk_to_chroma_metadata(sample_chunk)
    assert meta["source_org"] == "ICMR"
    assert meta["verification_status"] == "unverified"
    assert meta["publication_year"] == 2026
    assert meta["page_number"] == 24
    assert meta["chunk_id"] == sample_chunk.chunk_id
    assert meta["content_hash"] == sample_chunk.content_hash
    assert isinstance(meta["exact_context"], str)


def test_build_upsert_payload(sample_chunk: ChunkRecord, unit_embedding: list[float]):
    payload = build_upsert_payload([sample_chunk], [unit_embedding])
    assert payload["ids"] == [sample_chunk.chunk_id]
    assert payload["documents"] == [sample_chunk.exact_context]
    assert len(payload["embeddings"][0]) == len(unit_embedding)
    assert payload["metadatas"][0]["document_title"] == "TB Guidelines"


def test_upsert_and_retrieve_metadata(
    tmp_chroma_path, sample_chunk: ChunkRecord, unit_embedding: list[float]
):
    store = ChromaStore(path=tmp_chroma_path)
    store.upsert_chunk(sample_chunk, unit_embedding)
    assert store.count() == 1
    stored = store.get_chunk_metadata(sample_chunk.chunk_id)
    assert stored is not None
    assert stored["chunk_id"] == sample_chunk.chunk_id
    assert stored["source_url"] == sample_chunk.source_url


def test_rejects_non_unit_embedding(tmp_chroma_path, sample_chunk: ChunkRecord):
    store = ChromaStore(path=tmp_chroma_path)
    raw = [2.0, 0.0, 0.0] + [0.0] * 1021
    with pytest.raises(ValueError, match="L2-normalized"):
        store.upsert_chunk(sample_chunk, raw)


def test_persistence_after_reopen(
    tmp_chroma_path, sample_chunk: ChunkRecord, unit_embedding: list[float]
):
    store = ChromaStore(path=tmp_chroma_path)
    store.upsert_chunk(sample_chunk, unit_embedding)

    again = ChromaStore(path=tmp_chroma_path)
    assert again.count() == 1
    assert again.chunk_exists(sample_chunk.chunk_id)


def test_offline_query_top_k(
    tmp_chroma_path, sample_chunk: ChunkRecord, unit_embedding: list[float]
):
    store = ChromaStore(path=tmp_chroma_path)
    store.upsert_chunk(sample_chunk, unit_embedding)
    client = BgeEmbeddingClient(api_token="", mock=True)
    query_vec = l2_normalize(client.embed_query("Bedaquiline DOTS treatment"))
    results = store.query_by_embedding(query_vec, n_results=1)
    assert results["ids"][0][0] == sample_chunk.chunk_id


def test_upsert_from_disk_chunk_jsonl(tmp_chroma_path, unit_embedding: list[float]):
    """Load real chunk JSONL if present in workspace."""
    root = Path(__file__).resolve().parents[2]
    jsonl = root / "data" / "chunks" / "sha256_897f356f852ac50d.jsonl"
    if not jsonl.exists():
        pytest.skip("chunk jsonl not on disk")
    line = jsonl.read_text(encoding="utf-8").strip().split("\n")[0]
    chunk = ChunkRecord.model_validate(json.loads(line))
    vec = l2_normalize(BgeEmbeddingClient(api_token="", mock=True).embed_passages([chunk.exact_context])[0])
    store = ChromaStore(path=tmp_chroma_path)
    store.upsert_chunk(chunk, vec)
    assert store.chunk_exists(chunk.chunk_id)


def test_chroma_sqlite_created(tmp_chroma_path):
    get_chroma_client(tmp_chroma_path)
    assert (tmp_chroma_path / "chroma.sqlite3").exists()
