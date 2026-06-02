"""Phase 5.4 — REST routes for Vercel HITL console."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from pipeline.index.chroma_store import ChromaStore
from shared.schemas import (
    ChunkDetailResponse,
    CitationResponse,
    ExportGateResponse,
    QueryRequest,
    QueryResponse,
    QuerySuggestionResponse,
    StarterPromptResponse,
    SourceOrg,
    VerificationStatus,
    VerifyChunkRequest,
)

from api.rag import run_rag_query
from api.rag.starter_prompts import build_starter_prompts
from api.rag.suggestions import build_verified_query_suggestions
from api.sessions.store import session_store
from shared.chunk_content import (
    is_placeholder_context,
    load_chunk_text_from_store,
    sanitize_display_context,
)
from shared.config import settings
from shared.document_titles import resolve_document_title
from shared.source_links import resolve_source_url


def _suggestion_models(suggestions) -> list[QuerySuggestionResponse]:
    return [
        QuerySuggestionResponse(
            label=s.label,
            query=s.query,
            chunk_id=s.chunk_id,
            source_org=s.source_org,
            document_id=s.document_id or None,
        )
        for s in suggestions
    ]

router = APIRouter(prefix="/api/v1")


def _get_chunk_from_chroma(chunk_id: str) -> ChunkDetailResponse:
    store = ChromaStore()
    meta = store.get_chunk_metadata(chunk_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Chunk not found")
    source_url = resolve_source_url(str(meta["source_url"]))
    exact_context = str(meta["exact_context"])
    if is_placeholder_context(exact_context):
        canonical = load_chunk_text_from_store(chunk_id)
        if canonical:
            exact_context = canonical
    exact_context = sanitize_display_context(exact_context)
    if not exact_context.strip():
        raise HTTPException(status_code=404, detail="Chunk has no reviewable content")

    doc_title = resolve_document_title(
        str(meta["document_title"]),
        source_url,
        exact_context,
    )
    return ChunkDetailResponse(
        chunk_id=str(meta["chunk_id"]),
        source_url=source_url,
        document_title=doc_title,
        publication_year=int(meta["publication_year"]),
        page_number=int(meta["page_number"]),
        exact_context=exact_context,
        verification_status=VerificationStatus.UNVERIFIED,
        source_org=SourceOrg(str(meta["source_org"])),
        content_hash=str(meta.get("content_hash")) if meta.get("content_hash") else None,
    )


@router.post("/query", response_model=QueryResponse)
def post_query(body: QueryRequest) -> QueryResponse:
    if not settings.groq_api_key.strip() and not settings.groq_mock:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is required for live answers. Set it in .env and restart the API.",
        )
    result = run_rag_query(
        body.query,
        document_id=body.document_id,
        prior_session_id=body.prior_session_id,
    )
    return QueryResponse(
        session_id=result.session_id,
        answer=result.answer,
        citations=[
            CitationResponse(
                index=c.index,
                chunk_id=c.chunk_id,
                document_title=c.document_title,
                verification_status=c.verification_status,
                source_url=c.source_url or None,
                publication_date=c.publication_date or None,
            )
            for c in result.citations
        ],
        model_used=result.model_used,
        refused=result.refused,
        retrieval_ms=result.retrieval_ms,
        out_of_corpus=result.out_of_corpus,
        needs_clarification=result.needs_clarification,
        suggested_queries=_suggestion_models(result.suggested_queries),
        retrieval_mode=result.retrieval_mode,
        groq_live=result.groq_live,
        indexed_count=result.indexed_count,
        live_source_count=result.live_source_count,
        coverage_note=result.coverage_note,
    )


@router.get("/suggestions", response_model=list[QuerySuggestionResponse])
def get_verified_suggestions() -> list[QuerySuggestionResponse]:
    """Verified-topic suggestions for the HITL UI (same payload as out-of-corpus queries)."""
    return _suggestion_models(build_verified_query_suggestions(limit=3))


@router.get("/starter-prompts", response_model=list[StarterPromptResponse])
def get_starter_prompts() -> list[StarterPromptResponse]:
    """Landing-page demo: corpus questions + one off-topic prompt for pinky-promise UX."""
    return [
        StarterPromptResponse(
            id=p.id,
            label=p.label,
            query=p.query,
            kind=p.kind.value,
            chunk_id=p.chunk_id,
            source_org=p.source_org,
            document_id=p.document_id or None,
        )
        for p in build_starter_prompts()
    ]


@router.get("/chunks/{chunk_id}", response_model=ChunkDetailResponse)
def get_chunk(chunk_id: str) -> ChunkDetailResponse:
    return _get_chunk_from_chroma(chunk_id)


@router.patch("/sessions/{session_id}/verify/{chunk_id}")
def verify_chunk(
    session_id: str,
    chunk_id: str,
    body: VerifyChunkRequest,
) -> dict[str, str]:
    if not session_store.get(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    if body.verified:
        if not session_store.mark_verified(session_id, chunk_id):
            raise HTTPException(status_code=404, detail="Citation not in session")

        store = ChromaStore()
        meta = store.get_chunk_metadata(chunk_id)
        if meta:
            updated = dict(meta)
            updated["verification_status"] = VerificationStatus.VERIFIED.value
            store.collection.update(ids=[chunk_id], metadatas=[updated])

    return {"status": "ok", "chunk_id": chunk_id}


@router.get("/sessions/{session_id}/export-gate", response_model=ExportGateResponse)
def export_gate(session_id: str) -> ExportGateResponse:
    gate = session_store.export_gate(session_id)
    if gate is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return gate
