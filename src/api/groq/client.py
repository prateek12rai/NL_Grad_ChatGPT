"""
Phase 5.1 — Groq chat client (OpenAI-compatible API).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from shared.config import settings
from shared.schemas import GroqChatMessage

from api.groq.exceptions import GroqAuthError, GroqError, GroqRateLimitError


@dataclass(frozen=True)
class GroqCompletionResult:
    content: str
    model: str
    rate_limit_remaining_tokens: str | None = None


def _messages_to_dicts(messages: list[GroqChatMessage]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


def _mock_completion(messages: list[GroqChatMessage], model: str) -> GroqCompletionResult:
    """Deterministic offline completion for tests and dev without API key."""
    user_text = " ".join(m.content for m in messages if m.role == "user")
    if "CONTEXT:" not in user_text and "context blocks" not in user_text.lower():
        return GroqCompletionResult(
            content=(
                "I do not have sufficient information in the provided sources to answer "
                "that question safely. Please consult official ICMR/DHR guidelines or a "
                "qualified clinician.\n\n"
                "_Disclaimer: This tool supports research review only; it does not provide "
                "individual diagnoses or prescriptions._"
            ),
            model="mock-refusal",
        )

    disclaimer = (
        "_Disclaimer: This tool supports research review only; it does not provide "
        "individual diagnoses or prescriptions._"
    )
    blocks = re.findall(
        r"\[(\d+)\]\s*\([^)]+\)\s*URL:\s*\S+\s*(.+?)(?=\n\[\d+\]|\n\nQUESTION:|\Z)",
        user_text,
        re.DOTALL,
    )
    if not blocks:
        blocks = re.findall(
            r"\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\n\nQUESTION:|\Z)",
            user_text,
            re.DOTALL,
        )
    if "INDEX SUMMARY" in user_text and "COUNT" in user_text.upper():
        count = len(blocks) or len(re.findall(r"^\[(\d+)\]", user_text, re.MULTILINE))
        lines = [
            f"**Direct answer:** {count} indexed document(s) match your filters [1]"
            + (f"–[{count}]" if count > 1 else "")
            + ".",
            "**Indexed articles:**",
        ]
        for num, body in blocks[:6]:
            title_m = re.search(r"—\s*([^,]+),", user_text)
            title = title_m.group(1).strip() if title_m else f"Source {num}"
            lines.append(f"{num}. {title} [{num}]")
        answer = "\n".join(lines) + f"\n\n{disclaimer}"
        return GroqCompletionResult(content=answer, model=model or "mock-groq")

    if blocks:
        lines = ["**Summary:** Based on the indexed sources:"]
        for num, body in blocks[:5]:
            snippet = re.sub(r"\s+", " ", body.strip())[:160]
            lines.append(f"- {snippet} [{num}]")
        answer = "\n".join(lines) + f"\n\n{disclaimer}"
        return GroqCompletionResult(content=answer, model=model or "mock-groq")

    return GroqCompletionResult(
        content=(
            "**Summary:** The indexed sources do not contain enough detail to answer "
            "confidently; try a more specific question or verify sources in the sandbox.\n\n"
            + disclaimer
        ),
        model=model or "mock-groq",
    )


class GroqChatClient:
    """Thin wrapper around Groq chat completions."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        mock: bool | None = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.groq_api_key).strip()
        use_mock = settings.groq_mock if mock is None else mock
        self.mock = use_mock or not self.api_key

    def chat(
        self,
        messages: list[GroqChatMessage],
        *,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> GroqCompletionResult:
        if self.mock:
            return _mock_completion(messages, model)

        try:
            from groq import Groq
        except ImportError as exc:
            raise GroqError("Install the groq package: pip install groq") from exc

        client = Groq(api_key=self.api_key)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=_messages_to_dicts(messages),
                max_tokens=max_tokens or settings.groq_max_tokens,
                temperature=temperature if temperature is not None else settings.groq_temperature,
            )
        except Exception as exc:
            message = str(exc).lower()
            if "401" in message or "unauthorized" in message:
                raise GroqAuthError(str(exc)) from exc
            if "429" in message or "rate limit" in message:
                raise GroqRateLimitError(str(exc)) from exc
            raise GroqError(str(exc)) from exc

        choice = response.choices[0].message.content or ""
        headers = getattr(response, "headers", None) or {}
        remaining = None
        if isinstance(headers, dict):
            remaining = headers.get("x-ratelimit-remaining-tokens")
        return GroqCompletionResult(
            content=choice,
            model=response.model or model,
            rate_limit_remaining_tokens=remaining,
        )
