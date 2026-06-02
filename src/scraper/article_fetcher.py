"""Fetch full article HTML for Nature (and similar publishers)."""

from __future__ import annotations

import html as html_module
import re

from bs4 import BeautifulSoup


def extract_nature_article_html(page_html: str, *, title: str, source_url: str) -> bytes:
    """Pull main article body from a Nature article page."""
    soup = BeautifulSoup(page_html, "lxml")
    body = (
        soup.select_one("div.c-article-body")
        or soup.select_one("article[data-test='article-body']")
        or soup.select_one("main article")
        or soup.select_one("main")
    )
    if body:
        inner = str(body)
    else:
        inner = f"<p>{html_module.escape(soup.get_text(' ', strip=True)[:12000])}</p>"

    safe_title = html_module.escape(title)
    doc = (
        f'<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<title>{safe_title}</title>"
        f'<link rel="canonical" href="{html_module.escape(source_url)}"/>'
        f"</head><body><article data-source=\"nature-live\">{inner}</article></body></html>"
    )
    return doc.encode("utf-8")


def is_nature_article_url(url: str) -> bool:
    return bool(re.search(r"nature\.com/articles/s\d+", url, re.I))
