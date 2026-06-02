"""Optional live Groq — ONE API call only (budget)."""

import os

import pytest

from api.groq import GroqChatClient
from shared.schemas import GroqChatMessage

pytestmark = pytest.mark.live


def test_live_groq_single_chat_call(live_api_call):
    """Single Groq completion validates API key (gate 5.7.1 live)."""
    from shared.config import settings

    key = (os.environ.get("GROQ_API_KEY") or settings.groq_api_key or "").strip()
    if not key:
        pytest.skip("GROQ_API_KEY not set")

    client = GroqChatClient(api_key=key, mock=False)
    result = client.chat(
        [
            GroqChatMessage(role="system", content="Reply with one word: OK"),
            GroqChatMessage(role="user", content="Say OK only."),
        ],
        model=settings.groq_model_fallback,
        max_tokens=16,
    )
    assert result.content
    assert len(result.content.strip()) > 0
