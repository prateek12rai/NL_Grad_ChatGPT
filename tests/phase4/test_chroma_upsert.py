"""Phase 4.4 — indexer orchestrator and CLI (architecture §10)."""

import json
from pathlib import Path

import pytest

from pipeline.embeddings import BgeEmbeddingClient
from pipeline.index import ChromaStore, IndexOrchestrator
from pipeline.index.chroma_upsert import main as chroma_upsert_main
from pipeline.index.loader import load_chunks_from_index
from scraper.manifest import ManifestFile, ManifestStore
from shared.schemas import ChunkRecord, SourceOrg, VerificationStatus


@pytest.fixture
def index_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    data_dir = tmp_path / "data"
    chunks_dir = data_dir / "chunks"
    chunks_dir.mkdir(parents=True)
    chroma_dir = tmp_path / "chroma_test"
    chroma_dir.mkdir()

    chunk = ChunkRecord(
        chunk_id="sha256:idxws01::p0001::c0001",
        document_id="sha256:idxws01",
        source_org=SourceOrg.ICMR,
        source_url="https://www.icmr.gov.in/example.pdf",
        document_title="Indexer Test Doc",
        publication_year=2026,
        page_number=1,
        chunk_index=1,
        exact_context="Bedaquiline under monitored DOTS for resistant TB.",
        token_count=10,
        char_count=45,
        verification_status=VerificationStatus.UNVERIFIED,
        content_hash="hash_v1",
        created_at="2026-06-01T12:00:00Z",
    )
    jsonl_path = chunks_dir / "sha256_idxws01.jsonl"
    jsonl_path.write_text(
        json.dumps(chunk.to_jsonl_dict(), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    index = {
        "schema_version": "1",
        "generated_at": "2026-06-01T12:00:00Z",
        "total_chunks": 1,
        "documents": [
            {
                "document_id": "sha256:idxws01",
                "chunk_file": "data/chunks/sha256_idxws01.jsonl",
                "chunk_count": 1,
                "content_hash": "sha256:aggregate",
            }
        ],
    }
    index_path = chunks_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    manifest_path = data_dir / "manifest.json"
    ManifestStore(manifest_path).save(ManifestFile())

    monkeypatch.setenv("CHROMA_PATH", str(chroma_dir))
    monkeypatch.setenv("EMBED_MOCK", "true")
    from shared.config import settings

    settings.chroma_path = str(chroma_dir)
    settings.embed_mock = True
    settings.chunk_index_path = str(index_path)
    settings.corpus_path = str(data_dir / "corpus")

    return {
        "repo_root": tmp_path,
        "chroma_dir": chroma_dir,
        "index_path": index_path,
        "chunk": chunk,
    }


def test_load_chunks_from_index(index_workspace: dict):
    records = load_chunks_from_index(index_workspace["repo_root"])
    assert len(records) == 1
    assert records[0].chunk_id == index_workspace["chunk"].chunk_id


def test_indexer_embeds_into_chroma(index_workspace: dict):
    orch = IndexOrchestrator(
        repo_root=index_workspace["repo_root"],
        embed_client=BgeEmbeddingClient(api_token="", mock=True),
    )
    result = orch.run()
    assert result.chunks_embedded == 1
    assert orch.store.count() == 1
    assert orch.store.chunk_exists(index_workspace["chunk"].chunk_id)
    assert orch.stats_path.exists()


def test_indexer_skips_unchanged_hash(index_workspace: dict):
    orch = IndexOrchestrator(
        repo_root=index_workspace["repo_root"],
        embed_client=BgeEmbeddingClient(api_token="", mock=True),
    )
    orch.run()
    second = orch.run()
    assert second.chunks_skipped_unchanged == 1
    assert second.chunks_embedded == 0


def test_dry_run_no_write(index_workspace: dict):
    orch = IndexOrchestrator(
        repo_root=index_workspace["repo_root"],
        embed_client=BgeEmbeddingClient(api_token="", mock=True),
    )
    result = orch.run(dry_run=True)
    assert result.chunks_embedded == 1
    assert orch.store.count() == 0


def test_cli_main(index_workspace: dict):
    code = chroma_upsert_main(
        ["--repo-root", str(index_workspace["repo_root"])]
    )
    assert code == 0
    store = ChromaStore(path=index_workspace["chroma_dir"])
    assert store.count() == 1
