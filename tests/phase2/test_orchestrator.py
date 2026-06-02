"""Phase 2 integration — orchestrator, manifest, ingest log, PII."""

import json
from datetime import datetime, timezone

from scraper.manifest import ManifestFile, ManifestStore, make_document_id, reindex_manifest
from scraper.orchestrator import build_fixture_orchestrator
from scraper.pruner import prune_manifest
from shared.schemas import DocumentRecord, SourceOrg


def test_orchestrator_ingests_from_fixtures(phase2_html, phase2_data_dir):
    orch = build_fixture_orchestrator(phase2_html["nature"], phase2_data_dir)
    orch.repo_root = phase2_data_dir.parent
    result = orch.run(max_per_source=5)

    assert result.ingested >= 2
    manifest = orch.manifest_store.load()
    assert len(manifest.documents) >= 2
    orgs = {d.source_org for d in manifest.documents}
    assert orgs == {SourceOrg.NATURE}

    log_text = orch.logger.path.read_text(encoding="utf-8")
    assert "date_range" in log_text
    assert "last_30_days" in log_text


def test_pii_rejection_blocks_ingest(phase2_html, phase2_data_dir):
    bad_nature = phase2_html["nature"].replace(
        "BNT162b2 LP.8.1 early vaccine effectiveness",
        "Patient Aadhaar 1234 5678 9012 record",
    )
    orch = build_fixture_orchestrator(bad_nature, phase2_data_dir)
    orch.repo_root = phase2_data_dir.parent
    result = orch.run(max_per_source=5)
    assert result.skipped_pii >= 1
    log_lines = orch.logger.path.read_text(encoding="utf-8").strip().split("\n")
    events = [json.loads(line)["event"] for line in log_lines if line]
    assert "pii_rejected" in events


def test_cap_enforcement_prunes_to_1000(phase2_data_dir):
    store = ManifestStore(phase2_data_dir / "manifest.json")
    manifest = ManifestFile()
    repo = phase2_data_dir.parent
    corpus = phase2_data_dir / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)

    for i in range(1001):
        doc_id = make_document_id(f"https://www.nature.com/articles/s41467-026-{i:05d}", f"Doc {i}")
        fpath = corpus / "nature" / f"{doc_id.replace(':', '_')}.html"
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_bytes(b"<html>mock</html>")
        day = 1000 - i
        manifest.documents.append(
            DocumentRecord(
                document_id=doc_id,
                source_org=SourceOrg.NATURE,
                source_url=f"https://www.nature.com/articles/s41467-026-{i:05d}",
                document_title=f"Doc {i}",
                publication_date=f"2020-01-{day % 28 + 1:02d}",
                ingested_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                local_path=f"data/corpus/nature/{doc_id.replace(':', '_')}.html",
                chronological_rank=0,
            )
        )

    manifest = reindex_manifest(manifest)
    assert len(manifest.documents) == 1001

    manifest, pruned = prune_manifest(
        manifest,
        max_documents=1000,
        corpus_root=corpus,
        repo_root=repo,
    )
    assert len(manifest.documents) == 1000
    assert len(pruned) == 1
