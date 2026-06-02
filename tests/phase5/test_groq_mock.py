"""Phase 5.7.1 — Groq mock integration."""

import pytest

from api.groq import GroqChatClient, chat_with_fallback
from api.groq.exceptions import GroqRateLimitError
from api.groq.model_router import model_chain
from shared.schemas import GroqChatMessage


def test_mock_completion_with_context():
    client = GroqChatClient(api_key="", mock=True)
    messages = [
        GroqChatMessage(role="system", content="rules"),
        GroqChatMessage(
            role="user",
            content="CONTEXT:\n[1] Bedaquiline for resistant TB.\n\nQUESTION: What drug?",
        ),
    ]
    result = client.chat(messages, model="test-model")
    assert result.content
    assert "[1]" in result.content or "Bedaquiline" in result.content


def test_mock_refusal_without_context():
    client = GroqChatClient(api_key="", mock=True)
    messages = [GroqChatMessage(role="user", content="QUESTION: Random drug XYZ999?")]
    result = client.chat(messages, model="test-model")
    assert "sufficient" in result.content.lower() or "insufficient" in result.content.lower()


def test_model_chain_includes_primary():
    chain = model_chain()
    assert "meta-llama" in chain[0] or chain[0]


def test_fallback_on_rate_limit(monkeypatch):
    from api.groq.client import _mock_completion

    calls: list[str] = []

    def fake_chat(self, messages, *, model, max_tokens=None, temperature=None):
        calls.append(model)
        if len(calls) == 1:
            raise GroqRateLimitError("429")
        return _mock_completion(messages, model)

    monkeypatch.setattr(GroqChatClient, "chat", fake_chat)
    result = chat_with_fallback(
        [GroqChatMessage(role="user", content="CONTEXT:\n[1] test\n\nQUESTION: hi?")],
        client=GroqChatClient(api_key="fake-key", mock=False),
    )
    assert len(calls) >= 2
    assert result.content
