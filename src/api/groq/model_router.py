"""
Phase 5.2 — Groq free-tier model fallback chain (architecture §11.2).
"""

from __future__ import annotations

import logging

from shared.config import settings
from shared.schemas import GroqChatMessage

from api.groq.client import GroqChatClient, GroqCompletionResult
from api.groq.exceptions import GroqAllModelsRateLimitedError, GroqRateLimitError

logger = logging.getLogger(__name__)

FALLBACK_MODEL_B = "llama-3.3-70b-versatile"


def model_chain() -> list[str]:
    chain = [
        settings.groq_model_primary,
        settings.groq_model_fallback,
        FALLBACK_MODEL_B,
    ]
    seen: set[str] = set()
    ordered: list[str] = []
    for model in chain:
        if model and model not in seen:
            ordered.append(model)
            seen.add(model)
    return ordered


def chat_with_fallback(
    messages: list[GroqChatMessage],
    *,
    client: GroqChatClient | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> GroqCompletionResult:
    groq = client or GroqChatClient()
    last_rate_limit: Exception | None = None

    for model in model_chain():
        try:
            result = groq.chat(
                messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if result.model != model:
                result = GroqCompletionResult(
                    content=result.content,
                    model=model,
                    rate_limit_remaining_tokens=result.rate_limit_remaining_tokens,
                )
            return result
        except GroqRateLimitError as exc:
            logger.warning("groq_rate_limit model=%s", model)
            last_rate_limit = exc
            continue

    raise GroqAllModelsRateLimitedError(
        str(last_rate_limit) if last_rate_limit else "All models rate-limited"
    )
