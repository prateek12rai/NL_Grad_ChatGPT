"""
Validate API keys with minimal live calls.

Default (Groq-only setup): 1 Groq call if HF token missing or EMBED_MOCK=true.
Optional: up to 2 calls if HF token present and EMBED_MOCK=false.

Usage:
  set PYTHONPATH=src
  python scripts/validate_api_keys.py
  python scripts/validate_api_keys.py --groq-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)

from shared.config import Settings

settings = Settings()
from shared.schemas import GroqChatMessage


def _mask(secret: str) -> str:
    if not secret or len(secret) < 8:
        return "(missing)"
    return f"{secret[:4]}...{secret[-4:]}"


def validate_groq() -> tuple[bool, str]:
    key = (settings.groq_api_key or "").strip()
    if not key:
        return False, "GROQ_API_KEY is empty in .env"
    try:
        from api.groq import GroqChatClient

        client = GroqChatClient(api_key=key, mock=False)
        result = client.chat(
            [GroqChatMessage(role="user", content="Reply with exactly: OK")],
            model=settings.groq_model_fallback,
            max_tokens=8,
        )
        if not result.content.strip():
            return False, "Groq returned empty content"
        return True, f"OK (model={result.model}, key={_mask(key)})"
    except Exception as exc:
        return False, f"Groq failed: {exc}"


def validate_huggingface() -> tuple[bool, str]:
    token = (settings.huggingface_api_token or "").strip()
    if settings.embed_mock or not token:
        return True, "SKIPPED (EMBED_MOCK=true or no HF token — mock embeddings)"
    try:
        from pipeline.embeddings import BgeEmbeddingClient

        client = BgeEmbeddingClient(api_token=token, mock=False)
        vectors = client.embed_passages(["API key validation probe."])
        dim = len(vectors[0]) if vectors else 0
        if dim < 1:
            return False, "HF returned empty embedding"
        return True, f"OK (dim={dim}, token={_mask(token)})"
    except Exception as exc:
        return False, f"Hugging Face failed: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate API keys (minimal calls)")
    parser.add_argument(
        "--groq-only",
        action="store_true",
        help="Only validate Groq (1 API call)",
    )
    args = parser.parse_args()

    hf_will_call = (
        not args.groq_only
        and not settings.embed_mock
        and bool((settings.huggingface_api_token or "").strip())
    )
    max_calls = 1 if args.groq_only or not hf_will_call else 2
    print(f"API key validation (max {max_calls} live call(s))\n")
    print(f"  Mode: EMBED_MOCK={settings.embed_mock}, GROQ_MOCK={settings.groq_mock}\n")

    groq_ok, groq_msg = validate_groq()
    print(f"  Groq:          {'PASS' if groq_ok else 'FAIL'} — {groq_msg}")

    if args.groq_only:
        hf_msg = "SKIPPED (--groq-only)"
        hf_ok = True
        print(f"  Hugging Face:  SKIP — {hf_msg}")
    else:
        hf_ok, hf_msg = validate_huggingface()
        skipped = hf_msg.startswith("SKIPPED")
        label = "SKIP" if skipped else ("PASS" if hf_ok else "FAIL")
        print(f"  Hugging Face:  {label} — {hf_msg}")

    print()
    if groq_ok and (hf_ok or args.groq_only or settings.embed_mock):
        print("Overall: PASS — Groq ready; embeddings use mock (no HF token needed)")
        return 0
    if groq_ok:
        print("Overall: PARTIAL — Groq OK")
        return 0
    print("Overall: FAIL — fix GROQ_API_KEY in .env")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
