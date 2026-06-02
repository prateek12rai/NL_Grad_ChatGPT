"""Phase 4.5 — verify_chroma_index checks."""

import json
from pathlib import Path

import pytest

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize
from pipeline.index import ChromaStore
from pipeline.index.verify import REQUIRED_METADATA_KEYS, verify_chroma_index
from shared.schemas import ChunkRecord, SourceOrg, VerificationStatus


@pytest.fixture
def verified_index(tmp_chroma_path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    stats = {
        "schema_version": "1",
        "total_vectors": 1,
        "collection": "india_medical_local",
    }
    stats_path = data_dir / "chroma_stats.json"
    stats_path.write_text(json.dumps(stats), encoding="utf-8")
    monkeypatch.setattr("shared.config.settings.corpus_path", str(data_dir / "corpus"))

    chunk = ChunkRecord(
        chunk_id="sha256:verify01::p0001::c0001",
        document_id="sha256:verify01",
        source_org=SourceOrg.DHR,
        source_url="https://www.dhr.gov.in/doc.pdf",
        document_title="Verify Doc",
        publication_year=2026,
        page_number=1,
        chunk_index=1,
        exact_context="National health policy verification sample text.",
        token_count=8,
        char_count=45,
        verification_status=VerificationStatus.UNVERIFIED,
        content_hash="vh1",
        created_at="2026-06-01T12:00:00Z",
    )
    client = BgeEmbeddingClient(api_token="", mock=True)
    vec = l2_normalize(client.embed_passages([chunk.exact_context])[0])
    store = ChromaStore(path=tmp_chroma_path)
    store.upsert_chunk(chunk, vec)
    return tmp_chroma_path, client, tmp_path


def test_verify_all_checks_pass(verified_index):
    chroma_path, client, repo_root = verified_index
    report = verify_chroma_index(
        chroma_path=chroma_path,
        embed_client=client,
        repo_root=repo_root,
    )
    assert report.passed
    names = {c.name for c in report.checks}
    assert "collection_exists" in names
    assert "sample_query" in names
    assert "metadata_keys" in names


def test_verify_fails_on_count_mismatch(verified_index):
    chroma_path, client, repo_root = verified_index
    report = verify_chroma_index(
        chroma_path=chroma_path,
        expected_count=99,
        embed_client=client,
        repo_root=repo_root,
    )
    assert not report.passed
    count_check = next(c for c in report.checks if c.name == "vector_count")
    assert not count_check.passed


def test_required_metadata_keys_complete():
    assert "content_hash" in REQUIRED_METADATA_KEYS
    assert "chunk_id" in REQUIRED_METADATA_KEYS
