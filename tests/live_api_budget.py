"""
Hard cap on real API calls during pytest live runs (max 5 per session).

Usage: every @pytest.mark.live test must request the ``live_api_call`` fixture.
"""

from __future__ import annotations

import os

# Strict ceiling — do not raise without team approval (architecture / free-tier safety)
MAX_LIVE_API_CALLS = int(os.environ.get("MAX_LIVE_API_CALLS", "5"))

_call_count = 0


def remaining_calls() -> int:
    return max(0, MAX_LIVE_API_CALLS - _call_count)


def consume_live_api_call(test_name: str) -> None:
    """Record one live API call or raise if budget exhausted."""
    global _call_count
    if _call_count >= MAX_LIVE_API_CALLS:
        raise RuntimeError(
            f"Live API budget exhausted ({MAX_LIVE_API_CALLS} calls). "
            f"Skipped further calls; last attempted: {test_name}"
        )
    _call_count += 1


def reset_live_api_budget() -> None:
    global _call_count
    _call_count = 0


def total_consumed() -> int:
    return _call_count
