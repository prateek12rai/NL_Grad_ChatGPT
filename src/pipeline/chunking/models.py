"""Phase 3 data models — extraction through chunking."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageText:
    """One page (PDF) or section (HTML) of normalized plain text."""

    page_number: int  # 1-based
    text: str
    source_path: str


@dataclass
class ExtractionResult:
    """Output of Phase 3.1 extractors."""

    pages: list[PageText] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    extractor_name: str = ""

    @property
    def is_empty(self) -> bool:
        return len(self.pages) == 0


@dataclass(frozen=True)
class TextUnit:
    """Coherent text unit after structural segmentation (Phase 3.3)."""

    page_number: int
    section_title: str | None
    text: str
    token_count: int = 0
    sentence_count: int = 0


@dataclass(frozen=True)
class ChunkDraft:
    """Bounded chunk after Phase 3.4 (exact_context ready for Phase 3.5 metadata)."""

    page_number: int
    section_title: str | None
    exact_context: str
    token_count: int = 0


@dataclass(frozen=True)
class SectionSpan:
    """Logical section within a page (architecture §8.3)."""

    page_number: int
    start_char: int
    end_char: int
    title: str | None
    text: str

    @property
    def char_length(self) -> int:
        return max(0, self.end_char - self.start_char)
