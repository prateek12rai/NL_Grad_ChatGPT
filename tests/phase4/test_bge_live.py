"""Optional live Hugging Face embed — ONE API call only (budget)."""

import os

import pytest

from pipeline.embeddings import BgeEmbeddingClient

pytestmark = pytest.mark.live


@pytest.fixture
def live_client() -> BgeEmbeddingClient:
    token = os.environ.get("HUGGINGFACE_API_TOKEN", "").strip()
    if not token:
        from shared.config import settings

        token = (settings.huggingface_api_token or "").strip()
    if not token:
        pytest.skip("HUGGINGFACE_API_TOKEN not set")
    return BgeEmbeddingClient(api_token=token, mock=False)


def test_live_hf_single_embed_call(live_api_call, live_client: BgeEmbeddingClient):
    """Single HF Inference call validates token + dimension (gate 4.6.1 live)."""
    vectors = live_client.embed_passages(["Bedaquiline TB validation probe."])
    assert len(vectors) == 1
    assert len(vectors[0]) >= 768
