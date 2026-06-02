"""Retrieval confidence gate — trigger pinky promise when query is out of corpus."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pipeline.index.retrieval import ScoredChunk
from shared.config import settings

if TYPE_CHECKING:
    from api.rag.query_analysis import QueryAnalysis

_TOKEN_RE = re.compile(r"[a-z0-9]{4,}", re.I)
_STOP = frozenset(
    {
        "what",
        "when",
        "where",
        "which",
        "about",
        "does",
        "have",
        "been",
        "were",
        "with",
        "from",
        "that",
        "this",
        "your",
        "their",
        "would",
        "could",
        "should",
        "article",
        "nature",
        "study",
        "research",
    }
)

_MEDICAL_TERMS = frozenset(
    {
        "clinical",
        "patient",
        "patients",
        "disease",
        "cancer",
        "diabetes",
        "therapy",
        "therapeutic",
        "treatment",
        "treatments",
        "drug",
        "drugs",
        "vaccine",
        "vaccines",
        "trial",
        "trials",
        "cohort",
        "hospital",
        "medical",
        "medicine",
        "health",
        "symptom",
        "symptoms",
        "diagnosis",
        "prognosis",
        "surgery",
        "screening",
        "tuberculosis",
        "asthma",
        "stroke",
        "cardiac",
        "oncology",
        "pathology",
        "biomarker",
        "antibiotic",
        "resistance",
        "mortality",
        "morbidity",
        "epidemiology",
        "pharmaceutical",
        "placebo",
        "randomized",
        "genome",
        "protein",
        "infection",
        "viral",
        "bacterial",
        "chronic",
        "acute",
        "pediatric",
        "pregnancy",
        "hypertension",
        "obesity",
        "insulin",
        "immunotherapy",
        "chemotherapy",
        "transplant",
        "tumor",
        "tumour",
        "syndrome",
        "disorder",
        "illness",
        "bedaquiline",
        "biomedical",
        "pharma",
        "dosing",
        "efficacy",
        "safety",
        "adverse",
        "endpoint",
        "endpoints",
    }
)

_NON_MEDICAL_DOMAINS = re.compile(
    r"\b(?:quantum|qubit|football|basketball|soccer|cricket|recipe|cooking|"
    r"bitcoin|cryptocurrency|stock\s+market|weather|capital\s+of|"
    r"javascript|python\s+programming|movie|netflix|celebrity|"
    r"election|president|parliament|pizza|burger|pasta|taco|"
    r"ice\s*cream|chocolate|candy|cookie|cupcake|donut|"
    r"aliens?|diet\s*coke|intelligence|loose\s+weight|chilling|"
    r"tea|pre\s*workout)\b",
    re.I,
)

_FOOD_OR_TRIVIA = re.compile(
    r"\b(?:pizza|burger|eat|eating|snack|meal|breakfast|lunch|dinner)\b",
    re.I,
)

_CORPUS_META = re.compile(
    r"\b(?:nature|articles?|papers?|published|corpus|indexed)\b",
    re.I,
)

_REFUSAL_MARKERS = (
    "insufficient information",
    "do not have sufficient",
    "does not contain",
    "do not contain",
    "not contain information",
    "cannot answer",
    "can't answer",
    "not in the provided",
    "no relevant",
    "outside the provided",
    "not covered in the provided",
)


def is_corpus_enumeration_query(query: str, analysis: "QueryAnalysis | None") -> bool:
    """True only for article count/list requests — not 'how much pizza'."""
    if analysis is None or not analysis.enumeration:
        return False
    lower = (query or "").lower()
    if _FOOD_OR_TRIVIA.search(lower) and not _CORPUS_META.search(lower):
        return False
    return bool(
        _CORPUS_META.search(lower)
        or re.search(
            r"\b(?:how many|list|count|articles?|papers?|reports?|published)\b",
            lower,
        )
    )


def is_medical_research_query(query: str, analysis: "QueryAnalysis | None" = None) -> bool:
    """
    True when the question is in scope for Nature medical-research RAG.
    Corpus count/list queries and explicit biomedical terms qualify; general trivia does not.
    """
    text = (query or "").strip()
    if not text:
        return False
    lower = text.lower()

    if _NON_MEDICAL_DOMAINS.search(lower):
        return False

    if _FOOD_OR_TRIVIA.search(lower) and not _CORPUS_META.search(lower):
        return False

    if is_corpus_enumeration_query(query, analysis):
        return True

    if _CORPUS_META.search(lower) and re.search(
        r"\b(?:how many|list|count|articles?|papers?)\b",
        lower,
    ):
        return True

    if re.search(
        r"\b(?:medical|clinical|biomedical|life\s+sciences?|health\s+research)\b",
        lower,
    ):
        return True

    tokens = _query_terms(query)
    if tokens & _MEDICAL_TERMS:
        return True

    return False


def _query_terms(query: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(query) if t.lower() not in _STOP}


def query_chunk_overlap(query: str, chunk_text: str) -> float:
    """Fraction of query terms found in chunk text (0–1)."""
    q = _query_terms(query)
    if not q:
        return 0.0
    body = (chunk_text or "").lower()
    hits = sum(1 for t in q if t in body)
    return hits / len(q)


def retrieval_meets_threshold(
    hits: list[ScoredChunk],
    query: str,
    *,
    mode: str,
) -> bool:
    """
    True when top retrieval hit is strong enough to answer in-corpus.
    Skips strict checks in embed_mock (unit tests).
    """
    if not hits:
        return False
    if settings.embed_mock:
        return True

    best = hits[0]
    min_sim = settings.rag_ooc_min_similarity
    if best.similarity < min_sim:
        return False

    overlap = query_chunk_overlap(query, best.chunk.exact_context)
    min_overlap = settings.rag_ooc_min_term_overlap
    if overlap < min_overlap:
        return False

    # Lexical mode: require a non-trivial BM25 match (distance derived from score)
    if mode == "lexical" and best.distance > 0.92:
        return False

    return True


def llm_answer_is_out_of_corpus(answer: str, cited: set[int]) -> bool:
    """Detect model refusals, empty citations, or cited answers that admit no evidence."""
    text = (answer or "").strip()
    if not text:
        return True
    lower = text.lower()
    if any(marker in lower for marker in _REFUSAL_MARKERS):
        return True
    if cited and (
        "does not contain" in lower
        or "do not contain" in lower
        or "not contain information" in lower
    ):
        return True
    if not cited and "pinky promise" not in lower:
        return True
    return False
