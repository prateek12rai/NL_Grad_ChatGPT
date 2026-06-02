"""Pydantic contracts used across all phases (architecture §7.2, §16)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


class SourceOrg(str, Enum):
    DHR = "DHR"
    ICMR = "ICMR"
    NATURE = "Nature"


class DocumentRecord(BaseModel):
    """Registry entry in data/manifest.json (Phase 2)."""

    document_id: str
    source_org: SourceOrg
    source_url: HttpUrl | str
    document_title: str
    publication_date: str
    ingested_at: str
    content_type: str = "pdf"
    local_path: str
    chronological_rank: int = 0


class ChunkRecord(BaseModel):
    """Disk JSONL model for Phase 3.5 / architecture §11.2."""

    chunk_id: str
    document_id: str
    source_org: SourceOrg
    source_url: str
    document_title: str
    publication_year: int
    page_number: int
    chunk_index: int
    exact_context: str
    token_count: int
    char_count: int
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    content_hash: str
    created_at: str

    def to_jsonl_dict(self) -> dict[str, Any]:
        """Serialize for ``data/chunks/*.jsonl`` (enum values as strings)."""
        data = self.model_dump()
        data["source_org"] = self.source_org.value
        data["verification_status"] = self.verification_status.value
        return data

    def to_chunk_metadata(self) -> ChunkMetadata:
        """Map to Phase 4 Chroma metadata contract."""
        return ChunkMetadata(
            chunk_id=self.chunk_id,
            source_org=self.source_org,
            source_url=self.source_url,
            document_title=self.document_title,
            publication_year=self.publication_year,
            page_number=self.page_number,
            exact_context=self.exact_context,
            verification_status=self.verification_status,
        )


class ChunkMetadata(BaseModel):
    """Chroma metadata payload per PRD / architecture §16.1."""

    source_url: str
    document_title: str
    publication_year: int
    page_number: int
    exact_context: str
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    source_org: SourceOrg
    chunk_id: str

    def to_chroma_metadata(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "document_title": self.document_title,
            "publication_year": self.publication_year,
            "page_number": self.page_number,
            "exact_context": self.exact_context,
            "verification_status": self.verification_status.value,
            "source_org": self.source_org.value,
            "chunk_id": self.chunk_id,
        }

    @classmethod
    def chroma_template_example(cls) -> ChunkMetadata:
        """PRD example metadata block."""
        return cls(
            source_url="https://www.icmr.gov.in/pdf/guidelines/tb_protocol_2026.pdf",
            document_title="National Operational Guidelines for Pulmonary Tuberculosis - Update",
            publication_year=2026,
            page_number=24,
            exact_context=(
                "For multi-drug resistant strains, administer Bedaquiline under "
                "strictly monitored DOTS context..."
            ),
            verification_status=VerificationStatus.UNVERIFIED,
            source_org=SourceOrg.ICMR,
            chunk_id="sha256:abc::p24::c3",
        )


class GroqChatMessage(BaseModel):
    role: str
    content: str


class GroqChatRequest(BaseModel):
    """Request shape for Groq chat completions (Phase 5)."""

    messages: list[GroqChatMessage]
    model: str | None = None
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class HealthResponse(BaseModel):
    status: str = "ok"
    chroma: str = "reachable"
    rag_retrieval: str | None = None
    groq_live: bool | None = None
    embed_mock: bool | None = None


class ExportGateResponse(BaseModel):
    allowed: bool
    total: int = 0
    verified: int = 0
    pending_indices: list[int] = Field(default_factory=list)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    # When set, retrieval and answers are limited to this manifest document_id.
    document_id: str | None = Field(default=None, max_length=128)
    # Session id from a prior "clarification needed" response — enables one retry pass.
    prior_session_id: str | None = Field(default=None, max_length=64)


class CitationResponse(BaseModel):
    index: int
    chunk_id: str
    document_title: str
    verification_status: VerificationStatus
    source_url: str | None = None
    publication_date: str | None = None


class QuerySuggestionResponse(BaseModel):
    """Clickable suggestion — POST ``query`` to /api/v1/query with ``document_id``."""

    label: str
    query: str
    chunk_id: str
    source_org: str
    document_id: str | None = None


class StarterPromptResponse(BaseModel):
    """Landing-page demo prompt (corpus showcase or off-topic pinky demo)."""

    id: str
    label: str
    query: str
    kind: str  # corpus | off_topic
    chunk_id: str = ""
    source_org: str = "Nature"
    document_id: str | None = None


class QueryResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[CitationResponse]
    model_used: str
    refused: bool = False
    retrieval_ms: float | None = None
    out_of_corpus: bool = False
    needs_clarification: bool = False
    suggested_queries: list[QuerySuggestionResponse] = Field(default_factory=list)
    retrieval_mode: str | None = None
    groq_live: bool | None = None
    indexed_count: int | None = None
    live_source_count: int | None = None
    coverage_note: str | None = None


class ChunkDetailResponse(BaseModel):
    chunk_id: str
    source_url: str
    document_title: str
    publication_year: int
    page_number: int
    exact_context: str
    verification_status: VerificationStatus
    source_org: SourceOrg
    content_hash: str | None = None


class VerifyChunkRequest(BaseModel):
    verified: bool = True
