"""
Phase 7 — GitHub Actions scheduler validations (docs/architecture.md §13).

These tests are intentionally **offline + quota-safe**:
- Nature listing is read from an HTML fixture.
- Downloads are mocked into local corpus.
- Embeddings are mocked (no Hugging Face calls).
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.index import ChromaStore
from pipeline.index.chroma_upsert import main as chroma_upsert_main
from pipeline.chunking.run import main as chunking_main
from scraper.orchestrator import build_fixture_orchestrator
from shared.config import settings


def test_phase7_fixture_ingest_chunk_index_upsert(tmp_path: Path, monkeypatch):
    # Arrange: isolated repo-like workspace
    repo_root = tmp_path / "repo"
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True)

    # Ensure phase pipeline writes artifacts inside this tmp repo, not the real workspace.
    settings.corpus_path = str(data_dir / "corpus")
    settings.chunk_output_dir = str(data_dir / "chunks")
    settings.chunk_index_path = str(data_dir / "chunks" / "index.json")

    fixtures = Path(__file__).resolve().parents[1] / "fixtures" / "phase2"
    nature_html = (fixtures / "nature_listing.html").read_text(encoding="utf-8")

    # Keep everything inside tmp workspace
    chroma_dir = repo_root / "chroma_db"
    chroma_dir.mkdir(parents=True)
    monkeypatch.setenv("CHROMA_PATH", str(chroma_dir))
    monkeypatch.setenv("EMBED_MOCK", "true")
    settings.chroma_path = str(chroma_dir)
    settings.embed_mock = True

    # Phase 7.2: ingest (fixture) → manifest + ingest_log
    orch = build_fixture_orchestrator(
        nature_html=nature_html,
        data_dir=data_dir,
        mock_downloads=True,
    )
    result = orch.run(sources=["nature"], max_per_source=3, max_total=3)
    assert result.ingested > 0

    # Ensure fixture corpus HTML is sufficiently "prose-like" to survive UI-noise
    # filters during chunking.
    corpus_dir = data_dir / "corpus" / "nature"
    assert corpus_dir.is_dir()
    for html_path in corpus_dir.glob("*.html"):
        html_path.write_text(
            "<html><head><title>Fixture Nature Article</title></head><body>"
            "<article>"
            "<h1>Fixture medical research</h1>"
            "<p>This fixture is a synthetic Nature-style article body used for offline Phase 7 tests.</p>"
            "<p>It discusses medical research topics such as cancer immunotherapy, trial design, and biomarkers.</p>"
            "<p>The goal is to ensure the chunking pipeline emits at least one ChunkRecord with exact_context.</p>"
            "<p>Methods: randomized cohorts, observational follow-up, and statistical controls.</p>"
            "<p>Results: a clinically meaningful signal was observed in the intervention group.</p>"
            "</article>"
            "</body></html>",
            encoding="utf-8",
        )

    manifest_path = data_dir / "manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest.get("documents", [])) <= settings.max_documents

    log_path = data_dir / "ingest_log.jsonl"
    assert log_path.is_file()
    # Prove Nature listing URL policy is enforced in logs (parse JSONL; don't depend
    # on serialization whitespace).
    events = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    nature_discover = [
        e for e in events if e.get("event") == "discover_start" and e.get("source") == "Nature"
    ]
    assert nature_discover, "Expected a Nature discover_start log event"
    assert any("last_30_days" in str(e) for e in nature_discover)

    # Phase 7.2: chunk → chunk index
    code = chunking_main(
        [
            "--manifest",
            str(manifest_path),
            "--repo-root",
            str(repo_root),
            "--force",
        ]
    )
    assert code == 0

    chunk_index = repo_root / "data" / "chunks" / "index.json"
    assert chunk_index.is_file()

    # Phase 7.2: upsert → chroma count smoke
    settings.chunk_index_path = str(chunk_index)
    code2 = chroma_upsert_main(["--repo-root", str(repo_root)])
    assert code2 == 0

    store = ChromaStore(path=chroma_dir)
    assert store.count() > 0

