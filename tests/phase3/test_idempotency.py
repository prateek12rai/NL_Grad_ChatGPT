"""Phase 3.5 — stable chunk_id set across runs (gate 3.6.4)."""

from pathlib import Path

from pipeline.chunking.metadata import document_to_chunk_records, drafts_to_chunk_records
from pipeline.chunking.models import ChunkDraft
from shared.schemas import DocumentRecord, SourceOrg


def _chunk_id_set(records) -> set[str]:
    return {r.chunk_id for r in records}


def test_drafts_to_chunk_records_idempotent():
    doc = DocumentRecord(
        document_id="sha256:deadbeef00000001",
        source_org=SourceOrg.ICMR,
        source_url="https://www.icmr.gov.in/example.pdf",
        document_title="Test Guideline",
        publication_date="2026-01-15",
        ingested_at="2026-06-01T00:00:00Z",
        content_type="pdf",
        local_path="data/corpus/icmr/test.pdf",
    )
    drafts = [
        ChunkDraft(page_number=1, section_title="A", exact_context="Sentence one here.", token_count=4),
        ChunkDraft(page_number=1, section_title="A", exact_context="Sentence two here.", token_count=4),
        ChunkDraft(page_number=3, section_title="B", exact_context="Page three text.", token_count=4),
    ]
    stamp = "2026-06-01T12:00:00Z"
    run_a = drafts_to_chunk_records(doc, drafts, created_at=stamp)
    run_b = drafts_to_chunk_records(doc, drafts, created_at=stamp)
    assert _chunk_id_set(run_a) == _chunk_id_set(run_b)
    assert [r.chunk_id for r in run_a] == [r.chunk_id for r in run_b]


def test_document_pipeline_idempotent(sample_html_path: Path):
    doc = DocumentRecord(
        document_id="sha256:idempotenthtml01",
        source_org=SourceOrg.NATURE,
        source_url="https://www.nature.com/articles/test",
        document_title="Fixture Article",
        publication_date="2026-05-28",
        ingested_at="2026-06-01T00:00:00Z",
        content_type="html",
        local_path=str(sample_html_path),
    )
    stamp = "2026-06-01T12:00:00Z"
    run_a = document_to_chunk_records(doc, sample_html_path, created_at=stamp)
    run_b = document_to_chunk_records(doc, sample_html_path, created_at=stamp)
    assert _chunk_id_set(run_a) == _chunk_id_set(run_b)
    assert len(run_a) == len(run_b) >= 1


def test_sample_pdf_idempotent_if_present(sample_pdf_path: Path):
    doc = DocumentRecord(
        document_id="sha256:phase3pdffixture",
        source_org=SourceOrg.ICMR,
        source_url="https://www.icmr.gov.in/fixture.pdf",
        document_title="Phase 3 PDF Fixture",
        publication_date="2026-03-01",
        ingested_at="2026-06-01T00:00:00Z",
        content_type="pdf",
        local_path=str(sample_pdf_path),
    )
    stamp = "2026-06-01T12:00:00Z"
    ids_a = _chunk_id_set(document_to_chunk_records(doc, sample_pdf_path, created_at=stamp))
    ids_b = _chunk_id_set(document_to_chunk_records(doc, sample_pdf_path, created_at=stamp))
    assert ids_a == ids_b
