"""Landing-page starter prompts — latest article + date-list demo + off-topic showcase."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from api.rag.corpus_suggestions import build_corpus_follow_ups
from api.rag.suggestions import QuerySuggestion, build_verified_query_suggestions
from pipeline.index.catalog import oldest_publication_date
from pipeline.index.chroma_store import ChromaStore

_MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _human_date(value: date) -> str:
    return f"{value.day} {_MONTH_NAMES[value.month - 1]} {value.year}"


class StarterPromptKind(str, Enum):
    CORPUS = "corpus"
    OFF_TOPIC = "off_topic"


@dataclass(frozen=True)
class StarterPrompt:
    id: str
    label: str
    query: str
    kind: StarterPromptKind
    chunk_id: str = ""
    source_org: str = "Nature"
    document_id: str = ""


_OFF_TOPIC_DEMOS: tuple[StarterPrompt, ...] = (
    StarterPrompt(
        id="demo-off-topic-aliens-cancer",
        label="👽 Do you think Aliens have cure for Cancer?",
        query="Do you think aliens have a cure for cancer? Explain briefly in a science-fiction way, but keep it general (no medical advice).",
        kind=StarterPromptKind.OFF_TOPIC,
    ),
    StarterPrompt(
        id="demo-off-topic-dietcoke-weight",
        label="🥤 If I drink Diet Coke can I really cut that weight?",
        query="If I drink Diet Coke can I really cut that weight? Keep it vague and general for a prototype demo.",
        kind=StarterPromptKind.OFF_TOPIC,
    ),
    StarterPrompt(
        id="demo-off-topic-intelligence",
        label="🧠 What is the research done on Increasing Intelligence?",
        query="What is the research done on increasing intelligence? Keep it general and not medical advice.",
        kind=StarterPromptKind.OFF_TOPIC,
    ),
    StarterPrompt(
        id="demo-off-topic-chilling-weight",
        label="😎 Any reports on How to Loose weight by just chilling?",
        query="Any reports on how to lose weight by just chilling? Keep it funny, vague, and prototype-only.",
        kind=StarterPromptKind.OFF_TOPIC,
    ),
    StarterPrompt(
        id="demo-off-topic-tea-preworkout",
        label="🍵 Do you think Tea can be used as Pre workout?",
        query="Do you think tea can be used as pre workout? Keep it vague, funny, and prototype-only.",
        kind=StarterPromptKind.OFF_TOPIC,
    ),
)


_FALLBACK_CORPUS: tuple[StarterPrompt, ...] = (
    StarterPrompt(
        id="fallback-tb-screening",
        label="Bedaquiline-resistant TB under revised DOTS",
        query="What does the indexed Nature research say about bedaquiline-resistant tuberculosis and DOTS treatment protocols?",
        kind=StarterPromptKind.CORPUS,
        source_org="Nature",
    ),
    StarterPrompt(
        id="fallback-asthma-copd",
        label="Asthma–COPD overlap screening accuracy",
        query="Summarize clinical screening accuracy and implications from the Nature article on asthma COPD overlap.",
        kind=StarterPromptKind.CORPUS,
        source_org="Nature",
    ),
)


def _from_query_suggestion(s: QuerySuggestion, *, suffix: str) -> StarterPrompt:
    return StarterPrompt(
        id=f"corpus-{suffix}",
        label=s.label[:96] if len(s.label) > 96 else s.label,
        query=s.query,
        kind=StarterPromptKind.CORPUS,
        chunk_id=s.chunk_id,
        source_org=s.source_org,
        document_id=s.document_id or "",
    )


def _latest_article_prompt(seed: str) -> StarterPrompt:
    """Prompt 1 — a fresh question about one of our latest indexed Nature articles."""
    picks = build_corpus_follow_ups(limit=1, rotation_seed=seed)
    if picks:
        return _from_query_suggestion(picks[0], suffix="latest")
    store = ChromaStore()
    verified = build_verified_query_suggestions(store, limit=1)
    if verified:
        return _from_query_suggestion(verified[0], suffix="verified")
    return _FALLBACK_CORPUS[0]


def _date_list_prompt() -> StarterPrompt:
    """
    Prompt 2 — "show me all research on <date>" for a random date in the 3 days
    *before* our oldest indexed article, so it demonstrates the graceful
    "we don't have that date → here are our top 3 articles" path.
    """
    oldest = oldest_publication_date()
    base = oldest if oldest is not None else date(2026, 6, 1)
    offset = secrets.randbelow(3) + 1  # 1..3 days before the oldest article
    target = base - timedelta(days=offset)
    return StarterPrompt(
        id=f"date-list-{target.isoformat()}",
        label=f"📅 Show me all research on {_human_date(target)}",
        query=f"Show me all research articles published on {target.isoformat()}",
        kind=StarterPromptKind.CORPUS,
        source_org="Nature",
    )


def build_starter_prompts() -> list[StarterPrompt]:
    """
    Three fresh landing prompts (refreshed per request for a live demo feel):

    1. A question about one of our latest Nature articles (verifiable).
    2. A "show me all research on <date>" query for a date just before our oldest
       article — demonstrates the friendly not-found → top 3 articles fallback.
    3. A light-hearted off-topic prompt (triggers the Pinky Promise).
    """
    seed = str(time.time_ns())
    off_topic = _OFF_TOPIC_DEMOS[secrets.randbelow(len(_OFF_TOPIC_DEMOS))]
    return [
        _latest_article_prompt(seed),
        _date_list_prompt(),
        off_topic,
    ]
