"""Phase 5 — RAG API, refusal, export gate, CORS (architecture §11.3–11.4)."""

import time

import pytest
from fastapi.testclient import TestClient

from api.main import app
from pipeline.index import ChromaStore


@pytest.fixture
def client():
    return TestClient(app)


def test_post_query_returns_answer_and_citations(client, phase5_indexed_chroma):
    response = client.post(
        "/api/v1/query",
        json={"query": "Bedaquiline resistant tuberculosis DOTS"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["answer"]
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["chunk_id"] == phase5_indexed_chroma["chunk"].chunk_id
    assert body["citations"][0]["verification_status"] == "unverified"


def test_query_citations_unverified_even_if_chroma_verified(
    client, phase5_indexed_chroma
):
    from shared.schemas import VerificationStatus

    store = phase5_indexed_chroma["store"]
    chunk_id = phase5_indexed_chroma["chunk"].chunk_id
    meta = store.get_chunk_metadata(chunk_id)
    updated = dict(meta)
    updated["verification_status"] = VerificationStatus.VERIFIED.value
    store.collection.update(ids=[chunk_id], metadatas=[updated])

    body = client.post(
        "/api/v1/query",
        json={"query": "Bedaquiline resistant tuberculosis DOTS"},
    ).json()
    assert body["citations"][0]["verification_status"] == "unverified"


def test_refusal_when_chroma_empty(client, tmp_chroma_path, monkeypatch):
    monkeypatch.setenv("GROQ_MOCK", "true")
    from shared.config import settings

    settings.groq_mock = True
    response = client.post(
        "/api/v1/query",
        json={"query": "Obscure drug ZZZ-999 not in corpus"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["out_of_corpus"] is True
    assert len(body["citations"]) == 0
    assert "Pinky promise" in body["answer"]
    assert "Invalid" in body["answer"]


def test_out_of_corpus_returns_suggestions_when_verified_exists(
    client, phase5_indexed_chroma, monkeypatch
):
    from shared.config import settings
    from shared.schemas import VerificationStatus

    store = phase5_indexed_chroma["store"]
    chunk_id = phase5_indexed_chroma["chunk"].chunk_id
    meta = store.get_chunk_metadata(chunk_id)
    updated = dict(meta)
    updated["verification_status"] = VerificationStatus.VERIFIED.value
    store.collection.update(ids=[chunk_id], metadatas=[updated])

    monkeypatch.setattr(
        "api.rag.orchestrator.retrieve_for_rag",
        lambda *args, **kwargs: ([], "vector"),
    )
    response = client.post(
        "/api/v1/query",
        json={"query": "completely unrelated quantum physics topic xyz"},
    )
    body = response.json()
    assert body["out_of_corpus"] is True
    # Out-of-corpus suggestions are always fresh AND verifiable (each maps to a real
    # indexed Nature article via a non-empty document_id, so it can be opened + verified).
    assert len(body["suggested_queries"]) >= 1
    assert body["suggested_queries"][0]["query"]
    assert body["suggested_queries"][0]["document_id"]


def test_export_gate_isolated_per_session(client, phase5_indexed_chroma):
    q1 = client.post("/api/v1/query", json={"query": "Bedaquiline DOTS"})
    q2 = client.post("/api/v1/query", json={"query": "Bedaquiline DOTS"})
    s1, s2 = q1.json()["session_id"], q2.json()["session_id"]
    assert s1 != s2
    chunk_id = q1.json()["citations"][0]["chunk_id"]

    client.patch(
        f"/api/v1/sessions/{s1}/verify/{chunk_id}",
        json={"verified": True},
    )
    assert client.get(f"/api/v1/sessions/{s1}/export-gate").json()["allowed"] is True
    assert client.get(f"/api/v1/sessions/{s2}/export-gate").json()["allowed"] is False


def test_export_gate_blocks_until_verified(client, phase5_indexed_chroma):
    q = client.post("/api/v1/query", json={"query": "Bedaquiline DOTS"})
    session_id = q.json()["session_id"]
    chunk_id = q.json()["citations"][0]["chunk_id"]

    gate_before = client.get(f"/api/v1/sessions/{session_id}/export-gate")
    assert gate_before.status_code == 200
    assert gate_before.json()["allowed"] is False

    verify = client.patch(
        f"/api/v1/sessions/{session_id}/verify/{chunk_id}",
        json={"verified": True},
    )
    assert verify.status_code == 200

    gate_after = client.get(f"/api/v1/sessions/{session_id}/export-gate")
    assert gate_after.json()["allowed"] is True


def test_get_chunk_by_id(client, phase5_indexed_chroma):
    chunk_id = phase5_indexed_chroma["chunk"].chunk_id
    response = client.get(f"/api/v1/chunks/{chunk_id}")
    assert response.status_code == 200
    body = response.json()
    assert "Bedaquiline" in body["exact_context"]


def test_retrieval_under_500ms(phase5_indexed_chroma):
    from api.rag import run_rag_query

    result = run_rag_query(
        "Bedaquiline",
        chroma_store=phase5_indexed_chroma["store"],
    )
    assert result.retrieval_ms < 500


def test_starter_prompts_endpoint(client):
    res = client.get("/api/v1/starter-prompts")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 3
    assert body[-1]["kind"] == "off_topic"


def test_cors_allows_localhost_origin(client):
    response = client.options(
        "/api/v1/query",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in {
        k.lower() for k in response.headers.keys()
    }
