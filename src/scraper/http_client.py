"""Shared HTTP client for live scraping (browser-like headers)."""

from __future__ import annotations

import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def make_http_client() -> httpx.Client:
    return httpx.Client(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=httpx.Timeout(60.0, connect=30.0),
    )
