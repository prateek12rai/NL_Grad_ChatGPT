"""Phase 3.4 — overlap integrity (architecture §10.3, gate 3.6.2)."""

from pathlib import Path

from pipeline.chunking.models import TextUnit
from pipeline.chunking.tokenization import units_to_chunk_drafts
from pipeline.chunking.tokenization.overlap import overlap_tail_text


def test_overlap_tail_non_empty():
    text = "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu."
    tail = overlap_tail_text(text, overlap_tokens=10)
    assert tail
    assert len(tail) <= len(text)


def test_contraindication_phrase_in_consecutive_chunks():
    fixture = (
        Path(__file__).resolve().parents[1] / "fixtures" / "phase3" / "contraindication_overlap.txt"
    )
    base = fixture.read_text(encoding="utf-8")
    # Long enough to produce multiple chunks after 512 cap
    long_text = (base + " ") * 25
    unit = TextUnit(
        page_number=1,
        section_title="CONTRAINDICATIONS",
        text=long_text,
        token_count=0,
        sentence_count=0,
    )
    drafts = units_to_chunk_drafts([unit])
    assert len(drafts) >= 2

    phrase = "Bedaquiline"
    hits = [d for d in drafts if phrase in d.exact_context]
    assert len(hits) >= 2, "Phrase must appear in at least two overlapping chunks"

    # Overlap: tail of chunk N should appear at start of chunk N+1
    for i in range(len(drafts) - 1):
        tail = overlap_tail_text(drafts[i].exact_context, overlap_tokens=80)
        if tail:
            assert drafts[i + 1].exact_context.startswith(tail[: min(40, len(tail))]) or tail[:20] in drafts[
                i + 1
            ].exact_context
