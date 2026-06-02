"""Phase 3.4 — 512 token ceiling tests (architecture §10, gate 3.6.1)."""

from pathlib import Path

from pipeline.chunking.models import TextUnit
from pipeline.chunking.tokenization import (
    count_tokens,
    split_text_to_chunks,
    units_to_chunk_drafts,
)
from pipeline.chunking.tokenization.chunk_enforcer import DEFAULT_MAX_TOKENS

MAX = DEFAULT_MAX_TOKENS


def test_split_short_text_single_chunk():
    text = "Short clinical guidance for DOTS programs."
    chunks = split_text_to_chunks(text, max_tokens=MAX)
    assert len(chunks) == 1
    assert count_tokens(chunks[0]) <= MAX


def test_split_long_text_multiple_chunks():
    sentence = "For multi-drug resistant strains, administer Bedaquiline under monitored DOTS context. "
    text = sentence * 80
    chunks = split_text_to_chunks(text, max_tokens=MAX)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert count_tokens(chunk) <= MAX, count_tokens(chunk)


def test_units_to_chunk_drafts_respects_ceiling():
    sentence = "Clinical management requires careful monitoring. "
    body = sentence
    while count_tokens(body) <= 512:
        body += sentence
    unit = TextUnit(
        page_number=1,
        section_title="Guidelines",
        text=body,
        token_count=0,
        sentence_count=0,
    )
    drafts = units_to_chunk_drafts([unit])
    assert len(drafts) >= 2
    for draft in drafts:
        assert draft.token_count <= MAX
        assert draft.exact_context
        assert draft.page_number == 1


def test_sample_pdf_pipeline_chunk_limits(sample_pdf_path: Path):
    from pipeline.chunking.extractors import extract_document
    from pipeline.chunking.tokenization import pages_to_chunk_drafts

    pages = extract_document(sample_pdf_path, "pdf").pages
    drafts = pages_to_chunk_drafts(pages)
    assert len(drafts) >= 1
    for draft in drafts:
        assert draft.token_count <= MAX
