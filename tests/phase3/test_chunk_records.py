"""Phase 3.5 — ChunkRecord metadata completeness (gate 3.6.3)."""

from pathlib import Path

import pytest

from pipeline.chunking.metadata import (
    content_hash,
    drafts_to_chunk_records,
    format_chunk_id,
    publication_year_from_date,
)
from pipeline.chunking.models import ChunkDraft
from shared.schemas import ChunkRecord, DocumentRecord, SourceOrg, VerificationStatus

REQUIRED_FIELDS = {
    "chunk_id",
    "document_id",
    "source_org",
    "source_url",
    "document_title",
    "publication_year",
    "page_number",
    "chunk_index",
    "exact_context",
    "token_count",
    "char_count",
    "verification_status",
    "content_hash",
    "created_at",
}


@pytest.fixture
def sample_document() -> DocumentRecord:
    return DocumentRecord(
        document_id="sha256:4942ed487933e004",
        source_org=SourceOrg.DHR,
        source_url="https://www.dhr.gov.in/documents/publications/tb-policy-2026.pdf",
        document_title="National TB Policy Framework 2026",
        publication_date="2026-05-20",
        ingested_at="2026-06-01T00:00:00Z",
        content_type="pdf",
        local_path="data/corpus/dhr/sha256_4942ed487933e004.pdf",
    )


def test_format_chunk_id_zero_padded():
    cid = format_chunk_id("sha256:4942ed487933e004", page_number=24, chunk_index=3)
    assert cid == "sha256:4942ed487933e004::p0024::c0003"


def test_publication_year_from_date():
    assert publication_year_from_date("2026-05-20") == 2026
    assert publication_year_from_date("2025-11-01") == 2025


def test_content_hash_stable():
    text = "For multi-drug resistant strains, administer Bedaquiline."
    assert content_hash(text) == content_hash(text)
    assert len(content_hash(text)) == 64


def test_chunk_record_all_fields_present(sample_document: DocumentRecord):
    drafts = [
        ChunkDraft(page_number=1, section_title="Intro", exact_context="First chunk text.", token_count=4),
        ChunkDraft(page_number=1, section_title="Intro", exact_context="Second chunk text.", token_count=4),
        ChunkDraft(page_number=2, section_title="Methods", exact_context="Page two chunk.", token_count=4),
    ]
    records = drafts_to_chunk_records(
        sample_document, drafts, created_at="2026-06-01T12:00:01Z"
    )
    assert len(records) == 3
    for record in records:
        assert set(record.model_fields.keys()) == REQUIRED_FIELDS
        line = record.to_jsonl_dict()
        assert set(line.keys()) == REQUIRED_FIELDS
        assert line["verification_status"] == "unverified"
        assert line["source_org"] == "DHR"
        assert line["publication_year"] == 2026
        assert line["content_hash"] == content_hash(record.exact_context)
        assert line["char_count"] == len(record.exact_context)


def test_chunk_index_resets_per_page(sample_document: DocumentRecord):
    drafts = [
        ChunkDraft(page_number=1, section_title=None, exact_context="A", token_count=1),
        ChunkDraft(page_number=1, section_title=None, exact_context="B", token_count=1),
        ChunkDraft(page_number=2, section_title=None, exact_context="C", token_count=1),
    ]
    records = drafts_to_chunk_records(sample_document, drafts, created_at="2026-06-01T12:00:01Z")
    assert [r.chunk_index for r in records] == [1, 2, 1]
    assert records[0].chunk_id.endswith("::c0001")
    assert records[1].chunk_id.endswith("::c0002")
    assert records[2].chunk_id.endswith("::c0001")


def test_to_chunk_metadata_bridge(sample_document: DocumentRecord):
    draft = ChunkDraft(page_number=24, section_title=None, exact_context="Clinical text.", token_count=3)
    record = drafts_to_chunk_records(sample_document, [draft], created_at="2026-06-01T12:00:01Z")[0]
    meta = record.to_chunk_metadata()
    chroma = meta.to_chroma_metadata()
    assert chroma["chunk_id"] == record.chunk_id
    assert chroma["exact_context"] == "Clinical text."
    assert chroma["verification_status"] == "unverified"


def test_html_fixture_pipeline_metadata(sample_html_path: Path, sample_document: DocumentRecord):
    from pipeline.chunking.extractors import extract_document
    from pipeline.chunking.tokenization import pages_to_chunk_drafts

    pages = extract_document(sample_html_path, "html").pages
    drafts = pages_to_chunk_drafts(pages)
    doc = sample_document.model_copy(
        update={
            "document_id": "sha256:testhtml",
            "content_type": "html",
            "source_org": SourceOrg.NATURE,
        }
    )
    records = drafts_to_chunk_records(doc, drafts, created_at="2026-06-01T12:00:01Z")
    assert records
    for record in records:
        assert isinstance(record, ChunkRecord)
        assert record.verification_status == VerificationStatus.UNVERIFIED
        assert record.token_count <= 512
