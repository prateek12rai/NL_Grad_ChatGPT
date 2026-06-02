"""Phase 4.4 — prune cascade delete (gate 4.6.5)."""

import json
from pathlib import Path

import pytest

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize
from pipeline.index import ChromaStore, IndexOrchestrator
from scraper.manifest import ManifestFile, ManifestStore
from shared.schemas import ChunkRecord, SourceOrg, VerificationStatus


def _make_chunk(doc_id: str, page: int, idx: int, text: str) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=f"{doc_id}::p{page:04d}::c{idx:04d}",
        document_id=doc_id,
        source_org=SourceOrg.DHR,
        source_url="https://www.dhr.gov.in/example.pdf",
        document_title="Prune Test",
        publication_year=2026,
        page_number=page,
        chunk_index=idx,
        exact_context=text,
        token_count=5,
        char_count=len(text),
        verification_status=VerificationStatus.UNVERIFIED,
        content_hash=f"hash_{doc_id}_{page}_{idx}",
        created_at="2026-06-01T12:00:00Z",
    )


@pytest.fixture
def prune_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    data_dir = tmp_path / "data"
    chroma_dir = tmp_path / "chroma_test"
    chroma_dir.mkdir()
    monkeypatch.setenv("CHROMA_PATH", str(chroma_dir))
    monkeypatch.setenv("EMBED_MOCK", "true")
    from shared.config import settings

    settings.chroma_path = str(chroma_dir)
    settings.embed_mock = True
    settings.corpus_path = str(data_dir / "corpus")

    store = ChromaStore(path=chroma_dir)
    client = BgeEmbeddingClient(api_token="", mock=True)

    keep_doc = "sha256:keepdoc000001"
    prune_doc = "sha256:prunedoc00001"
    chunks = [
        _make_chunk(keep_doc, 1, 1, "Keep this document chunk."),
        _make_chunk(prune_doc, 1, 1, "Delete this document chunk."),
        _make_chunk(prune_doc, 1, 2, "Delete second chunk."),
    ]
    vectors = [l2_normalize(v) for v in client.embed_passages([c.exact_context for c in chunks])]
    store.upsert_chunks(chunks, vectors)
    assert store.count() == 3

    manifest_path = data_dir / "manifest.json"
    ManifestStore(manifest_path).save(
        ManifestFile(pruned_document_ids=[prune_doc])
    )

    return {
        "repo_root": tmp_path,
        "chroma_dir": chroma_dir,
        "manifest_path": manifest_path,
        "keep_doc": keep_doc,
        "prune_doc": prune_doc,
    }


def test_prune_cascade_deletes_document_vectors(prune_workspace: dict):
    ws = prune_workspace
    orch = IndexOrchestrator(
        repo_root=ws["repo_root"],
        embed_client=BgeEmbeddingClient(api_token="", mock=True),
    )
    result = orch.run(prune_only=True)
    assert result.chunks_deleted == 2
    assert orch.store.count() == 1
    assert orch.store.chunk_exists(f"{ws['keep_doc']}::p0001::c0001")
    assert not orch.store.chunk_exists(f"{ws['prune_doc']}::p0001::c0001")

    manifest = ManifestStore(ws["manifest_path"]).load()
    assert manifest.pruned_document_ids == []
