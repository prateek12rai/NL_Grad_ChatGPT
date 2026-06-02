"""Groq API errors (Phase 5.1)."""


class GroqError(Exception):
    """Base Groq client failure."""


class GroqRateLimitError(GroqError):
    """HTTP 429 — try next model in chain."""


class GroqAuthError(GroqError):
    """Invalid or missing API key."""


class GroqAllModelsRateLimitedError(GroqError):
    """Every model in the fallback chain returned 429."""
