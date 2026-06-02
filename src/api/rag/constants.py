"""User-facing RAG messages (product copy)."""

PINKY_PROMISE_MESSAGE = (
    "I made a Pinky promise that I will never ever give Invalid response"
)

CLARIFICATION_MESSAGE = """**Clarification needed**

Your question could apply to **more than one** indexed Nature medical-research article in our corpus. To give a single, accurate answer with **one citation**, please specify:

- **Publication date** (YYYY-MM-DD, as listed on Nature)
- **Time window** (e.g. last 7 days vs full 30-day index) if relevant
- **Exact focus** — what you want from the article (e.g. main findings, methods, limitations, screening accuracy, policy implications)

Example: *"Summarize the 2026-06-01 Nature paper on asthma COPD screening — methods and clinical implications only."*

_We answer one article per question unless you are asking for a count or list across the portfolio._"""
