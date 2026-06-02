"""
Structural segmentation (production default) — architecture §9.

Groups sentences within each SectionSpan up to SOFT_MAX tokens.
No embedding model; section boundaries from Phase 3.2 are never crossed.
"""

from __future__ import annotations

from pipeline.chunking.models import PageText, SectionSpan, TextUnit
from pipeline.chunking.segmentation.sentence_splitter import split_sentences
from pipeline.chunking.structure.detector import detect_sections
from pipeline.chunking.tokenization.tokenizer import count_tokens

DEFAULT_SOFT_MAX_TOKENS = 400


class StructuralSegmenter:
    """Portfolio v1: structure + sentence packing (no sentence embeddings)."""

    def __init__(self, soft_max_tokens: int = DEFAULT_SOFT_MAX_TOKENS) -> None:
        self.soft_max_tokens = soft_max_tokens

    def segment_pages(self, pages: list[PageText]) -> list[TextUnit]:
        sections = detect_sections(pages)
        return self.segment_sections(sections)

    def segment_sections(self, sections: list[SectionSpan]) -> list[TextUnit]:
        units: list[TextUnit] = []
        for section in sections:
            units.extend(self._segment_one_section(section))
        return units

    def _segment_one_section(self, section: SectionSpan) -> list[TextUnit]:
        """Pack sentences within a single section; never cross section boundary."""
        sentences = split_sentences(section.text)
        if not sentences:
            body = section.text.strip()
            if not body:
                return []
            tc = count_tokens(body)
            return [
                TextUnit(
                    page_number=section.page_number,
                    section_title=section.title,
                    text=body,
                    token_count=tc,
                    sentence_count=1,
                )
            ]

        section_units: list[TextUnit] = []
        buffer: list[str] = []

        def flush_buffer() -> None:
            if not buffer:
                return
            text = " ".join(buffer)
            section_units.append(
                TextUnit(
                    page_number=section.page_number,
                    section_title=section.title,
                    text=text,
                    token_count=count_tokens(text),
                    sentence_count=len(buffer),
                )
            )

        for sentence in sentences:
            candidate = " ".join(buffer + [sentence])
            if buffer and count_tokens(candidate) > self.soft_max_tokens:
                flush_buffer()
                buffer = [sentence]
            else:
                buffer.append(sentence)

        flush_buffer()
        return section_units


def segment_structurally(
    sections: list[SectionSpan],
    soft_max_tokens: int = DEFAULT_SOFT_MAX_TOKENS,
) -> list[TextUnit]:
    """Segment sections into TextUnits (production default)."""
    return StructuralSegmenter(soft_max_tokens=soft_max_tokens).segment_sections(
        sections
    )


def pages_to_units(
    pages: list[PageText],
    soft_max_tokens: int = DEFAULT_SOFT_MAX_TOKENS,
) -> list[TextUnit]:
    """Extract pipeline helper: pages → sections → units."""
    return StructuralSegmenter(soft_max_tokens=soft_max_tokens).segment_pages(pages)
