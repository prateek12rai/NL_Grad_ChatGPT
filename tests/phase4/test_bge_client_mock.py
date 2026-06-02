"""Phase 4.1 — BGE client mock mode (gate 4.6.1 partial, no HF network)."""

import pytest

from pipeline.embeddings import (
    BgeEmbeddingClient,
    mock_embedding_vector,
    plan_batches,
)
from pipeline.embeddings.bge_client import PASSAGE_PREFIX, QUERY_PREFIX
from pipeline.embeddings.exceptions import EmbeddingAuthError


@pytest.fixture
def mock_client() -> BgeEmbeddingClient:
    return BgeEmbeddingClient(api_token="", mock=True)


def test_mock_vector_dimension():
    vec = mock_embedding_vector("clinical guidance text")
    assert len(vec) == 1024


def test_mock_vector_deterministic():
    text = "For multi-drug resistant strains, administer Bedaquiline."
    assert mock_embedding_vector(text) == mock_embedding_vector(text)
    assert mock_embedding_vector(text) != mock_embedding_vector(text + " ")


def test_embed_passages_mock(mock_client: BgeEmbeddingClient):
    texts = ["First passage.", "Second passage."]
    vectors = mock_client.embed_passages(texts)
    assert len(vectors) == 2
    assert all(len(v) == 1024 for v in vectors)
    # Prefix applied — same raw text ≠ same vector as unprefixed mock
    assert vectors[0] == mock_client.embed_passages([texts[0]])[0]


def test_embed_query_prefix(mock_client: BgeEmbeddingClient):
    query_vec = mock_client.embed_query("TB treatment protocol")
    passage_vec = mock_client.embed_passages(["TB treatment protocol"])[0]
    assert len(query_vec) == 1024
    assert query_vec != passage_vec
    assert query_vec == mock_client.embed_query("TB treatment protocol")


def test_embed_passages_empty(mock_client: BgeEmbeddingClient):
    assert mock_client.embed_passages([]) == []


def test_live_client_requires_token(monkeypatch):
    monkeypatch.delenv("EMBED_MOCK", raising=False)
    from shared.config import settings

    monkeypatch.setattr(settings, "embed_mock", False)
    monkeypatch.setattr(settings, "huggingface_api_token", "")
    with pytest.raises(EmbeddingAuthError):
        BgeEmbeddingClient(api_token="", mock=False)


def test_plan_batches_respects_size_and_chars():
    texts = ["a" * 1000 for _ in range(20)]
    batches = plan_batches(texts, batch_size=8, max_chars=5000)
    assert sum(len(b) for b in batches) == 20
    for batch in batches:
        assert len(batch) <= 8
        assert sum(len(t) for t in batch) <= 5000 or len(batch) == 1


def test_passage_prefix_constant():
    assert PASSAGE_PREFIX == "passage: "
    assert QUERY_PREFIX == "query: "
