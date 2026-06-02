"""Pre-retrieval: infer intent, source, and date filters from the user question."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum

from shared.schemas import SourceOrg

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


class QueryIntent(str, Enum):
    COUNT = "count"
    LIST = "list"
    EXPLAIN = "explain"
    GENERAL = "general"


@dataclass(frozen=True)
class QueryAnalysis:
    raw_query: str
    intent: QueryIntent
    source_org: SourceOrg | None
    target_date: date | None
    enumeration: bool  # user wants a tally or itemized list


def _parse_date(text: str) -> date | None:
    lower = text.lower()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", lower)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(
        r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|"
        r"september|october|november|december)\s+(\d{4})",
        lower,
    )
    if m:
        return date(int(m.group(3)), _MONTHS[m.group(2)], int(m.group(1)))
    m = re.search(
        r"(january|february|march|april|may|june|july|august|"
        r"september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})",
        lower,
    )
    if m:
        return date(int(m.group(3)), _MONTHS[m.group(1)], int(m.group(2)))
    return None


def _parse_source_org(text: str) -> SourceOrg | None:
    lower = text.lower()
    if re.search(r"\bnature\b", lower):
        return SourceOrg.NATURE
    if re.search(r"\bicmr\b", lower):
        return SourceOrg.ICMR
    if re.search(r"\bdhr\b|\bhtain\b", lower):
        return SourceOrg.DHR
    return None


def analyze_query(query: str) -> QueryAnalysis:
    lower = query.lower()
    target_date = _parse_date(query)
    source_org = _parse_source_org(query)

    # "How much pizza…" is not a corpus count — only article tallies use COUNT intent
    count_like = bool(
        re.search(
            r"\b(how many|number of|count of|total)\b",
            lower,
        )
    ) or bool(
        re.search(r"\bhow much\b", lower)
        and re.search(r"\b(?:articles?|papers?|reports?|indexed|corpus|nature)\b", lower)
    )
    list_like = bool(
        re.search(
            r"\b(list|which|what are|name all|enumerate|published on)\b",
            lower,
        )
    )
    report_like = bool(re.search(r"\breports?\b|\barticles?\b|\bpapers?\b", lower))

    if count_like:
        intent = QueryIntent.COUNT
    elif list_like or (report_like and target_date):
        intent = QueryIntent.LIST
    elif re.search(r"\b(what|why|how|explain|summarize|describe)\b", lower):
        intent = QueryIntent.EXPLAIN
    else:
        intent = QueryIntent.GENERAL

    enumeration = intent in (QueryIntent.COUNT, QueryIntent.LIST) or (
        report_like and (source_org is not None or target_date is not None)
    )

    return QueryAnalysis(
        raw_query=query,
        intent=intent,
        source_org=source_org,
        target_date=target_date,
        enumeration=enumeration,
    )
