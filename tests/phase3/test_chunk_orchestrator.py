"""Phase 3.6 — orchestrator, index.json, incremental, PII (architecture §12–14)."""

import json
from pathlib import Path

import pytest

from pipeline.chunking.orchestrator import ChunkingOrchestrator
from pipeline.chunking.run import main
from pipeline.chunking.writer import chunk_jsonl_path, chunk_meta_path, read_chunk_jsonl
from scraper.manifest import ManifestFile, ManifestStore
from shared.schemas import DocumentRecord, SourceOrg


@pytest.fixture
def chunk_workspace(tmp_path: Path, sample_html_path: Path) -> dict:
    """Isolated data/ dir with one HTML manifest row."""
    data_dir = tmp_path / "data"
    chunks_dir = data_dir / "chunks"
    chunks_dir.mkdir(parents=True)
    corpus_dir = data_dir / "corpus" / "nature"
    corpus_dir.mkdir(parents=True)
    html_copy = corpus_dir / "sample.html"
    html_copy.write_text(sample_html_path.read_text(encoding="utf-8"), encoding="utf-8")

    doc = DocumentRecord(
        document_id="sha256:phase3testhtml01",
        source_org=SourceOrg.NATURE,
        source_url="https://www.nature.com/articles/phase3-test",
        document_title="Phase 3 HTML Test",
        publication_date="2026-05-28",
        ingested_at="2026-06-01T10:00:00Z",
        content_type="html",
        local_path="data/corpus/nature/sample.html",
    )
    manifest = ManifestFile(documents=[doc], pruned_document_ids=[])
    manifest_path = data_dir / "manifest.json"
    ManifestStore(manifest_path).save(manifest)

    return {
        "repo_root": tmp_path,
        "data_dir": data_dir,
        "chunks_dir": chunks_dir,
        "manifest_path": manifest_path,
        "document": doc,
    }


def test_orchestrator_writes_jsonl_and_index(chunk_workspace: dict):
    ws = chunk_workspace
    orch = ChunkingOrchestrator(
        repo_root=ws["repo_root"],
        manifest_store=ManifestStore(ws["manifest_path"]),
        output_dir=ws["chunks_dir"],
    )
    result = orch.run(incremental=False)

    assert result.processed == 1
    assert result.chunks_written >= 1

    jsonl_path = chunk_jsonl_path(ws["chunks_dir"], ws["document"].document_id)
    assert jsonl_path.exists()
    rows = read_chunk_jsonl(jsonl_path)
    assert rows[0]["chunk_id"].startswith(ws["document"].document_id)
    assert rows[0]["verification_status"] == "unverified"
    for row in rows:
        assert row["token_count"] <= 512

    index = json.loads((ws["chunks_dir"] / "index.json").read_text(encoding="utf-8"))
    assert index["schema_version"] == "1"
    assert index["total_chunks"] == len(rows)
    assert index["documents"][0]["chunk_count"] == len(rows)


def test_incremental_skips_unchanged(chunk_workspace: dict):
    ws = chunk_workspace
    orch = ChunkingOrchestrator(
        repo_root=ws["repo_root"],
        manifest_store=ManifestStore(ws["manifest_path"]),
        output_dir=ws["chunks_dir"],
    )
    orch.run(incremental=False)
    second = orch.run(incremental=True)
    assert second.skipped_incremental == 1
    assert second.processed == 0


def test_force_rebuilds(chunk_workspace: dict):
    ws = chunk_workspace
    orch = ChunkingOrchestrator(
        repo_root=ws["repo_root"],
        manifest_store=ManifestStore(ws["manifest_path"]),
        output_dir=ws["chunks_dir"],
    )
    orch.run(incremental=False)
    meta_path = chunk_meta_path(ws["chunks_dir"], ws["document"].document_id)
    meta_path.write_text(
        json.dumps(
            {
                "document_id": ws["document"].document_id,
                "source_ingested_at": "2020-01-01T00:00:00Z",
                "chunk_count": 1,
                "pipeline_version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    forced = orch.run(incremental=True, force=True)
    assert forced.processed == 1


def test_pii_chunk_dropped(tmp_path: Path, sample_html_path: Path):
    data_dir = tmp_path / "data"
    chunks_dir = data_dir / "chunks"
    chunks_dir.mkdir(parents=True)
    corpus_dir = data_dir / "corpus" / "icmr"
    corpus_dir.mkdir(parents=True)
    bad_html = sample_html_path.read_text(encoding="utf-8").replace(
        "Bedaquiline",
        "Patient Aadhaar 1234 5678 9012 on Bedaquiline",
    )
    (corpus_dir / "bad.html").write_text(bad_html, encoding="utf-8")

    doc = DocumentRecord(
        document_id="sha256:phase3piitest01",
        source_org=SourceOrg.ICMR,
        source_url="https://www.icmr.gov.in/bad.html",
        document_title="PII Test",
        publication_date="2026-01-01",
        ingested_at="2026-06-01T10:00:00Z",
        content_type="html",
        local_path="data/corpus/icmr/bad.html",
    )
    manifest_path = data_dir / "manifest.json"
    ManifestStore(manifest_path).save(ManifestFile(documents=[doc]))

    log_path = data_dir / "chunk_log.jsonl"
    orch = ChunkingOrchestrator(
        repo_root=tmp_path,
        manifest_store=ManifestStore(manifest_path),
        output_dir=chunks_dir,
        logger=__import__("pipeline.chunking.chunk_log", fromlist=["ChunkLogger"]).ChunkLogger(
            log_path
        ),
    )
    result = orch.run(incremental=False)
    assert result.chunks_dropped_pii >= 1
    events = [json.loads(line)["event"] for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert "pii_chunk_dropped" in events


def test_pruned_removes_chunk_files(chunk_workspace: dict):
    ws = chunk_workspace
    doc_id = "sha256:oldpruneddoc0001"
    jsonl_path = chunk_jsonl_path(ws["chunks_dir"], doc_id)
    meta_path = chunk_meta_path(ws["chunks_dir"], doc_id)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text('{"document_id":"x"}\n', encoding="utf-8")
    meta_path.write_text("{}", encoding="utf-8")

    manifest = ManifestStore(ws["manifest_path"]).load()
    manifest.pruned_document_ids = [doc_id]
    ManifestStore(ws["manifest_path"]).save(manifest)

    orch = ChunkingOrchestrator(
        repo_root=ws["repo_root"],
        manifest_store=ManifestStore(ws["manifest_path"]),
        output_dir=ws["chunks_dir"],
    )
    result = orch.run(incremental=False)
    assert result.pruned_files_removed >= 2
    assert not jsonl_path.exists()
    assert not meta_path.exists()


def test_cli_main(chunk_workspace: dict):
    ws = chunk_workspace
    code = main(
        [
            "--repo-root",
            str(ws["repo_root"]),
            "--manifest",
            str(ws["manifest_path"]),
            "--no-incremental",
        ]
    )
    assert code == 0
    assert (ws["chunks_dir"] / "index.json").exists()
