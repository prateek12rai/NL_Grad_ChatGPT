"""Phase 1.2 — shared contract tests."""

from shared.schemas import (
    ChunkMetadata,
    DocumentRecord,
    GroqChatMessage,
    GroqChatRequest,
    SourceOrg,
    VerificationStatus,
)


def test_chunk_metadata_to_chroma():
    chunk = ChunkMetadata.chroma_template_example()
    meta = chunk.to_chroma_metadata()
    assert meta["verification_status"] == "unverified"
    assert meta["source_org"] == "ICMR"
    assert meta["chunk_id"] == "sha256:abc::p24::c3"


def test_document_record_model():
    doc = DocumentRecord(
        document_id="sha256:test",
        source_org=SourceOrg.DHR,
        source_url="https://www.dhr.gov.in/example",
        document_title="Test Publication",
        publication_date="2026-01-01",
        ingested_at="2026-06-01T00:00:00Z",
        local_path="data/corpus/dhr/test.pdf",
    )
    assert doc.source_org == SourceOrg.DHR


def test_groq_chat_request_defaults():
    req = GroqChatRequest(
        messages=[GroqChatMessage(role="user", content="hi")]
    )
    assert req.max_tokens == 2048
    assert req.temperature == 0.1


def test_verification_status_enum():
    assert VerificationStatus.VERIFIED.value == "verified"
