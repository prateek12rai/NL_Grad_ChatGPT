"""Phase 5 fixtures — indexed Chroma + mock Groq."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize
from pipeline.index import ChromaStore
from shared.schemas import ChunkRecord, SourceOrg, VerificationStatus


@pytest.fixture
def phase5_indexed_chroma(tmp_chroma_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EMBED_MOCK", "true")
    monkeypatch.setenv("GROQ_MOCK", "true")
    from shared.config import settings

    settings.embed_mock = True
    settings.groq_mock = True

    chunk = ChunkRecord(
        chunk_id="sha256:phase5rag::p0001::c0001",
        document_id="sha256:phase5rag",
        source_org=SourceOrg.NATURE,
        source_url="https://www.nature.com/articles/s41598-026-00001-0",
        document_title="TB operational guidance in Nature medical research",
        publication_year=2026,
        page_number=24,
        chunk_index=1,
        exact_context=(
            "For multi-drug resistant strains, administer Bedaquiline under "
            "strictly monitored DOTS context."
        ),
        token_count=20,
        char_count=80,
        verification_status=VerificationStatus.UNVERIFIED,
        content_hash="p5hash1",
        created_at="2026-06-01T12:00:00Z",
    )
    client = BgeEmbeddingClient(api_token="", mock=True)
    vec = l2_normalize(client.embed_passages([chunk.exact_context])[0])
    store = ChromaStore(path=tmp_chroma_path)
    store.upsert_chunk(chunk, vec)

    from api.sessions.store import session_store

    session_store.clear()
    return {"store": store, "chunk": chunk}


@pytest.fixture(autouse=True)
def reset_sessions():
    from api.sessions.store import session_store

    session_store.clear()
    yield
    session_store.clear()
