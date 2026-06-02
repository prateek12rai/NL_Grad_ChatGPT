"""

Phase 5.3 — RAG orchestrator: analyze → retrieve → prompt → Groq → citations.

"""



from __future__ import annotations



import re

import time

from dataclasses import dataclass, field



from pipeline.index.catalog import count_catalog_documents, get_manifest_document
from pipeline.index.retrieval import _chunk_document_id
from pipeline.index.chroma_store import ChromaStore
from pipeline.index.hybrid_retrieval import retrieve_for_rag

from shared.chunk_content import is_placeholder_context, is_ui_boilerplate, sanitize_display_context
from shared.document_titles import resolve_document_title
from shared.schemas import GroqChatMessage, SourceOrg, VerificationStatus
from shared.source_links import resolve_source_url



from api.groq import GroqChatClient, chat_with_fallback

from api.groq.client import GroqCompletionResult

from api.rag.constants import PINKY_PROMISE_MESSAGE

from api.rag.prompts import SYSTEM_PROMPT, build_context_block, build_user_prompt

from api.rag.corpus_suggestions import build_corpus_follow_ups
from api.rag.nature_live import count_nature_on_date
from api.rag.query_analysis import QueryAnalysis, QueryIntent, analyze_query
from api.rag.document_resolve import resolve_document_id_from_query
from api.rag.relevance_gate import (
    is_medical_research_query,
    llm_answer_is_out_of_corpus,
    retrieval_meets_threshold,
)
from api.rag.single_article import (
    build_clarification_answer,
    enforce_single_citation_answer,
    is_multi_article_intent,
    nature_chunk_ok,
    retrieval_is_ambiguous,
    select_single_article_chunks,
)
from api.rag.suggestions import (

    QuerySuggestion,

    build_verified_query_suggestions,

    format_suggestions_block,

)

from api.sessions.store import CitationEntry, session_store
from pipeline.index.manifest_search import retrieve_from_manifest





@dataclass

class RagQueryResult:

    session_id: str

    answer: str

    citations: list[CitationEntry]

    model_used: str

    refused: bool = False

    retrieval_ms: float = 0.0

    out_of_corpus: bool = False

    needs_clarification: bool = False

    suggested_queries: list[QuerySuggestion] = field(default_factory=list)

    retrieval_mode: str = "vector"

    query_intent: str | None = None

    groq_live: bool = True
    indexed_count: int | None = None
    live_source_count: int | None = None
    coverage_note: str | None = None


def _citation_entries(chunks) -> list[CitationEntry]:
    """Session citations always start unverified — user must verify in HITL UI."""
    entries: list[CitationEntry] = []
    for i, c in enumerate(chunks, start=1):
        source_url = resolve_source_url(str(getattr(c, "source_url", "") or ""))
        title = resolve_document_title(
            str(c.document_title),
            source_url,
            str(getattr(c, "exact_context", "") or ""),
        )
        pub = getattr(c, "publication_year", "") or getattr(c, "publication_date", "")
        entries.append(
            CitationEntry(
                index=i,
                chunk_id=c.chunk_id,
                document_title=title,
                verification_status=VerificationStatus.UNVERIFIED,
                source_url=source_url,
                publication_date=str(pub) if pub else "",
            )
        )
    return entries


def _nature_only_chunks(chunks: list) -> list:
    return [c for c in chunks if nature_chunk_ok(c)]


def _citations_for_answer(
    citations: list[CitationEntry],
    cited: set[int],
    *,
    single_article: bool = True,
) -> list[CitationEntry]:
    """Only sources referenced in the answer; default cap of one citation."""
    if not citations:
        return []
    if cited:
        out = [c for c in citations if c.index in cited]
    else:
        out = list(citations[:1])
    if single_article:
        return out[:1]
    return out





def _parse_cited_indices(answer: str) -> set[int]:

    return {int(n) for n in re.findall(r"\[(\d+)\]", answer)}





def _document_key(chunk) -> str:

    if "::" in chunk.chunk_id:

        return chunk.chunk_id.split("::")[0]

    return chunk.document_title





def _dedupe_chunks_one_per_document(chunks: list, *, max_items: int = 6) -> list:

    seen: set[str] = set()

    out: list = []

    for chunk in chunks:

        key = _document_key(chunk)

        if key in seen:

            continue

        seen.add(key)

        out.append(chunk)

        if len(out) >= max_items:

            break

    return out





def _filter_quality_chunks(chunks: list) -> list:

    return [
        c
        for c in chunks
        if not is_placeholder_context(c.exact_context)
        and not is_ui_boilerplate(c.exact_context)
        and len(sanitize_display_context(c.exact_context)) >= 80
    ]





def _fresh_corpus_suggestions(store: ChromaStore, *, limit: int = 3) -> list[QuerySuggestion]:
    """Verifiable Nature suggestions that rotate on every call (fresh per pop-up)."""
    suggestions = build_corpus_follow_ups(limit=limit, rotation_seed=str(time.time_ns()))
    if not suggestions:
        suggestions = build_verified_query_suggestions(store, limit=limit)
    return suggestions


def _out_of_corpus_response(store: ChromaStore) -> tuple[str, list[QuerySuggestion]]:

    suggestions = _fresh_corpus_suggestions(store, limit=3)

    answer = PINKY_PROMISE_MESSAGE + format_suggestions_block(suggestions)

    return answer, suggestions





def _exclude_doc_ids_from_chunks(chunks: list) -> set[str]:
    return {_chunk_document_id(c.chunk_id) for c in chunks}


_LIST_TOPIC_STOP = {
    "any",
    "article",
    "articles",
    "about",
    "date",
    "from",
    "form",
    "more",
    "nature",
    "paper",
    "papers",
    "published",
    "report",
    "reports",
    "research",
    "show",
    "tell",
}


def _topic_terms_for_list_query(query: str, analysis: QueryAnalysis) -> set[str]:
    """Non-date/topic terms for filtering date-list manifest results."""
    text = re.sub(r"\d{4}-\d{2}-\d{2}", " ", query.lower())
    terms = set(re.findall(r"[a-z][a-z0-9]{3,}", text))
    terms = {t for t in terms if t not in _LIST_TOPIC_STOP}
    if analysis.source_org:
        terms.discard(analysis.source_org.value.lower())
    return terms


def _filter_chunks_by_topic(chunks: list, query: str, analysis: QueryAnalysis) -> list:
    terms = _topic_terms_for_list_query(query, analysis)
    if not terms:
        return chunks
    filtered = []
    for chunk in chunks:
        haystack = f"{getattr(chunk, 'document_title', '')} {getattr(chunk, 'exact_context', '')}".lower()
        if any(term in haystack for term in terms):
            filtered.append(chunk)
    return filtered


def _is_clarification_retry(prior_session_id: str | None) -> bool:
    if not prior_session_id:
        return False
    session = session_store.get(prior_session_id)
    return session is not None and session.awaiting_clarification


def _build_out_of_corpus_result(
    store: ChromaStore,
    *,
    retrieval_ms: float,
    mode: str,
    analysis: QueryAnalysis,
) -> RagQueryResult:
    answer, suggestions = _out_of_corpus_response(store)
    session = session_store.create([])
    return RagQueryResult(
        session_id=session.session_id,
        answer=answer,
        citations=[],
        model_used="none",
        refused=True,
        retrieval_ms=retrieval_ms,
        out_of_corpus=True,
        suggested_queries=suggestions,
        retrieval_mode=mode,
        query_intent=analysis.intent.value,
        groq_live=False,
    )


def _build_date_not_found_result(
    store: ChromaStore,
    *,
    target_date,
    retrieval_ms: float,
    mode: str,
    analysis: QueryAnalysis,
) -> RagQueryResult:
    """Date has no indexed articles → apologize and surface the top 3 newest articles."""
    suggestions = build_corpus_follow_ups(limit=3, newest_first=True)
    if not suggestions:
        suggestions = _fresh_corpus_suggestions(store, limit=3)
    message = (
        f"Sorry, we don't have any articles for {target_date.isoformat()} in our database. "
        f"Try referring to our top 3 articles instead:"
    )
    answer = message + format_suggestions_block(suggestions)
    session = session_store.create([])
    return RagQueryResult(
        session_id=session.session_id,
        answer=answer,
        citations=[],
        model_used="none",
        refused=True,
        retrieval_ms=retrieval_ms,
        out_of_corpus=True,
        suggested_queries=suggestions,
        retrieval_mode=mode,
        query_intent=analysis.intent.value,
        groq_live=False,
    )


def run_rag_query(

    query: str,

    *,

    top_k: int | None = None,

    document_id: str | None = None,

    prior_session_id: str | None = None,

    chroma_store: ChromaStore | None = None,

    groq_client: GroqChatClient | None = None,

) -> RagQueryResult:

    from shared.config import settings



    store = chroma_store or ChromaStore()

    analysis: QueryAnalysis = analyze_query(query)

    if not is_medical_research_query(query, analysis):
        return _build_out_of_corpus_result(
            store,
            retrieval_ms=0.0,
            mode="none",
            analysis=analysis,
        )

    # Deterministic LIST-by-date: avoid LLM picking a single article.
    if analysis.intent == QueryIntent.LIST and analysis.target_date and not document_id:
        t0 = time.perf_counter()
        hits = retrieve_from_manifest(
            source_org=analysis.source_org,
            target_date=analysis.target_date,
            max_documents=max(1, settings.rag_list_max_documents),
        )
        retrieval_ms = (time.perf_counter() - t0) * 1000
        date_has_docs = len(hits) > 0
        chunks = _nature_only_chunks([h.chunk for h in hits])
        chunks = _filter_chunks_by_topic(chunks, query, analysis)
        if not chunks:
            # No article exists for this date at all → friendly not-found + top 3 articles.
            if not date_has_docs:
                return _build_date_not_found_result(
                    store,
                    target_date=analysis.target_date,
                    retrieval_ms=retrieval_ms,
                    mode="manifest",
                    analysis=analysis,
                )
            # Date exists but the requested topic isn't among that day's articles.
            return _build_out_of_corpus_result(
                store,
                retrieval_ms=retrieval_ms,
                mode="manifest",
                analysis=analysis,
            )
        citations = _citation_entries(chunks)
        lines = [
            f"**Direct answer:** Here are the indexed Nature article(s) for {analysis.target_date.isoformat()}.\n",
            "**Sources:**",
        ]
        for i, c in enumerate(citations, start=1):
            lines.append(f"- {c.document_title} [{i}]")
        lines.append(
            "\n_Disclaimer: This tool supports research review only; it does not provide "
            "individual diagnoses or prescriptions._"
        )
        answer = "\n".join(lines)
        session = session_store.create(citations, cited_indices=set(range(1, len(citations) + 1)))
        return RagQueryResult(
            session_id=session.session_id,
            answer=answer,
            citations=citations,
            model_used="manifest-list",
            refused=False,
            retrieval_ms=retrieval_ms,
            out_of_corpus=False,
            needs_clarification=False,
            suggested_queries=build_corpus_follow_ups(
                limit=3,
                exclude_document_ids=_exclude_doc_ids_from_chunks(chunks),
                rotation_seed=session.session_id,
            ),
            retrieval_mode="manifest",
            query_intent=analysis.intent.value,
            groq_live=False,
        )

    t0 = time.perf_counter()

    context_hits, mode = retrieve_for_rag(

        query,

        top_k=top_k,

        store=store,

        embed_client=None,

        analysis=analysis,

        document_id=document_id,

    )

    retrieval_ms = (time.perf_counter() - t0) * 1000

    multi_article = is_multi_article_intent(analysis, query)
    clarification_retry = _is_clarification_retry(prior_session_id)

    if clarification_retry:
        resolved_id = document_id or resolve_document_id_from_query(query)
        if not resolved_id:
            return _build_out_of_corpus_result(
                store,
                retrieval_ms=retrieval_ms,
                mode=mode,
                analysis=analysis,
            )
        if resolved_id != document_id:
            document_id = resolved_id
            context_hits, mode = retrieve_for_rag(
                query,
                top_k=top_k,
                store=store,
                embed_client=None,
                analysis=analysis,
                document_id=document_id,
            )
            retrieval_ms = (time.perf_counter() - t0) * 1000

    if (
        not clarification_retry
        and not multi_article
        and not document_id
        and not retrieval_meets_threshold(context_hits, query, mode=mode)
    ):
        return _build_out_of_corpus_result(
            store,
            retrieval_ms=retrieval_ms,
            mode=mode,
            analysis=analysis,
        )

    if retrieval_is_ambiguous(context_hits, analysis, document_id=document_id):
        if clarification_retry or not is_medical_research_query(query, analysis):
            return _build_out_of_corpus_result(
                store,
                retrieval_ms=retrieval_ms,
                mode=mode,
                analysis=analysis,
            )
        answer = build_clarification_answer()
        session = session_store.create(
            [],
            cited_indices=set(),
            awaiting_clarification=True,
        )
        return RagQueryResult(
            session_id=session.session_id,
            answer=answer,
            citations=[],
            model_used="clarification",
            refused=False,
            retrieval_ms=retrieval_ms,
            out_of_corpus=False,
            needs_clarification=True,
            suggested_queries=build_corpus_follow_ups(
                limit=3,
                rotation_seed=query,
            ),
            retrieval_mode=mode,
            query_intent=analysis.intent.value,
            groq_live=settings.groq_live,
        )

    chunks = _filter_quality_chunks([h.chunk for h in context_hits])
    chunks = _nature_only_chunks(chunks)

    if document_id:
        chunks = [c for c in chunks if _chunk_document_id(c.chunk_id) == document_id]
        chunks = chunks[: settings.rag_context_chunks]
    elif multi_article:
        chunks = _dedupe_chunks_one_per_document(
            chunks,
            max_items=min(5, settings.rag_max_citations + 4),
        )
    else:
        chunks = select_single_article_chunks(
            context_hits,
            max_chunks=settings.rag_context_chunks,
        )



    if not chunks:
        return _build_out_of_corpus_result(
            store,
            retrieval_ms=retrieval_ms,
            mode=mode,
            analysis=analysis,
        )



    citations = _citation_entries(chunks[:1] if not multi_article else chunks)

    indexed_count: int | None = None
    live_source_count: int | None = None
    coverage_note: str | None = None
    if analysis.enumeration:
        indexed_count = count_catalog_documents(
            source_org=analysis.source_org,
            target_date=analysis.target_date,
        )
        if (
            settings.rag_nature_live_count
            and analysis.source_org
            and analysis.source_org.value == "Nature"
            and analysis.target_date
        ):
            live_source_count = count_nature_on_date(analysis.target_date)
        if indexed_count is not None:
            if live_source_count is not None and live_source_count > indexed_count:
                coverage_note = (
                    f"Your local index holds {indexed_count} Nature article(s) for "
                    f"{analysis.target_date.isoformat()}; Nature's current listing shows "
                    f"about {live_source_count}. Run ingest to add missing articles."
                )
            else:
                coverage_note = (
                    f"Count is from your indexed corpus ({indexed_count} document(s) "
                    f"matching filters), sorted newest first."
                )

    article_scope_title: str | None = None
    if document_id:
        scoped = get_manifest_document(document_id)
        if scoped:
            article_scope_title = resolve_document_title(
                str(scoped.get("document_title", "")),
                str(scoped.get("source_url", "")),
                "",
            )

    context_block = build_context_block(chunks)

    messages = [
        GroqChatMessage(role="system", content=SYSTEM_PROMPT),
        GroqChatMessage(
            role="user",
            content=build_user_prompt(
                query,
                context_block,
                analysis,
                chunk_count=len(chunks),
                indexed_count=indexed_count,
                live_source_count=live_source_count,
                coverage_note=coverage_note,
                article_scope_title=article_scope_title,
                single_article=not multi_article,
            ),
        ),
    ]



    client = groq_client or GroqChatClient()

    groq_live = settings.groq_live and not client.mock

    completion: GroqCompletionResult = chat_with_fallback(

        messages,

        client=client,

        max_tokens=settings.groq_max_tokens,

        temperature=settings.rag_temperature,

    )



    answer_text = completion.content
    if not multi_article:
        answer_text = enforce_single_citation_answer(answer_text)

    cited = _parse_cited_indices(answer_text)
    if (
        not multi_article
        and llm_answer_is_out_of_corpus(answer_text, cited)
    ):
        return _build_out_of_corpus_result(
            store,
            retrieval_ms=retrieval_ms,
            mode=mode,
            analysis=analysis,
        )

    if not multi_article and citations:
        cited = {1}

    if not cited:
        refused = "insufficient" in answer_text.lower()
    else:
        refused = False

    ui_citations = _citations_for_answer(
        citations, cited, single_article=not multi_article
    )
    cited_scope = {c.index for c in ui_citations}

    session = session_store.create(ui_citations, cited_indices=cited_scope)

    return RagQueryResult(

        session_id=session.session_id,

        answer=answer_text,

        citations=ui_citations,

        model_used=completion.model,

        refused=refused,

        retrieval_ms=retrieval_ms,

        suggested_queries=build_corpus_follow_ups(
            limit=3,
            exclude_document_ids=_exclude_doc_ids_from_chunks(chunks)
            | ({document_id} if document_id else set()),
            rotation_seed=session.session_id,
        ),

        retrieval_mode=mode,

        query_intent=analysis.intent.value,

        groq_live=groq_live,

        indexed_count=indexed_count,

        live_source_count=live_source_count,

        coverage_note=coverage_note,

    )


