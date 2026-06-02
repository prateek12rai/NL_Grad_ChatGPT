"""Structure detection — heading/section boundaries (architecture §8)."""

from __future__ import annotations

import re
from dataclasses import replace

from pipeline.chunking.models import PageText, SectionSpan

_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+\S")
# e.g. "1. Background", "2.3 Treatment Protocol"
_NUMBERED_SECTION = re.compile(r"^\d+(?:\.\d+)*\.?\s+[A-Za-z]")
_ALL_CAPS = re.compile(r"^[A-Z0-9][A-Z0-9\s\-–—,:]{3,79}$")

_MEDICAL_HEADERS = frozenset(
    {
        "introduction",
        "background",
        "methods",
        "methodology",
        "results",
        "discussion",
        "conclusion",
        "recommendations",
        "recommendation",
        "contraindications",
        "contraindication",
        "dosage",
        "dosing",
        "adverse effects",
        "warnings",
        "precautions",
        "indications",
        "summary",
        "executive summary",
        "guidelines",
        "treatment",
        "diagnosis",
        "management",
    }
)

_MIN_SECTION_CHARS = 20


class StructureDetector:
    """Detect section spans from extracted page text."""

    def __init__(self, min_section_chars: int = _MIN_SECTION_CHARS) -> None:
        self.min_section_chars = min_section_chars

    def detect_pages(self, pages: list[PageText]) -> list[SectionSpan]:
        spans: list[SectionSpan] = []
        for page in pages:
            spans.extend(self.detect_page(page))
        return self._merge_short_sections(spans)

    def detect_page(self, page: PageText) -> list[SectionSpan]:
        """
        §8.4: Walk lines; on heading flush prior section; merge shorts < 20 chars.
        """
        text = page.text
        if not text.strip():
            return []

        lines = text.splitlines()
        sections: list[SectionSpan] = []
        current_title: str | None = None
        current_lines: list[str] = []
        section_start_offset = 0
        pos = 0

        def line_end_offset(line_index: int) -> int:
            end = 0
            for j in range(line_index + 1):
                end += len(lines[j])
                if j < line_index:
                    end += 1
            return end

        def flush(up_to_line: int) -> None:
            nonlocal current_title, current_lines, section_start_offset
            body = "\n".join(ln for ln in current_lines if ln is not None).strip()
            if current_title is None and not body:
                return

            section_text = body if body else (current_title or "")
            if not section_text.strip():
                current_title = None
                current_lines = []
                return

            end_char = line_end_offset(up_to_line) if up_to_line >= 0 else len(text)
            end_char = min(end_char, len(text))
            start_char = min(section_start_offset, len(text))

            sections.append(
                SectionSpan(
                    page_number=page.page_number,
                    start_char=start_char,
                    end_char=end_char,
                    title=current_title,
                    text=section_text,
                )
            )
            current_title = None
            current_lines = []
            section_start_offset = end_char
            if end_char < len(text) and end_char < line_end_offset(up_to_line):
                section_start_offset = min(end_char + 1, len(text))

        for i, line in enumerate(lines):
            line_start = pos
            stripped = line.strip()
            line_with_nl = line + ("\n" if i < len(lines) - 1 else "")
            pos += len(line_with_nl)

            if not stripped:
                if current_lines:
                    current_lines.append("")
                continue

            if is_heading(stripped):
                if current_lines or current_title is not None:
                    flush(i - 1)
                current_title = stripped.lstrip("#").strip()
                if current_title.endswith(":"):
                    current_title = current_title[:-1].strip()
                section_start_offset = line_start
                current_lines = []
            else:
                if not current_lines and current_title is None and not sections:
                    section_start_offset = line_start
                current_lines.append(stripped)

        flush(len(lines) - 1)

        if not sections:
            sections.append(
                SectionSpan(
                    page_number=page.page_number,
                    start_char=0,
                    end_char=len(text),
                    title=None,
                    text=text.strip(),
                )
            )
        return sections

    def _merge_short_sections(self, spans: list[SectionSpan]) -> list[SectionSpan]:
        if not spans:
            return spans
        merged: list[SectionSpan] = [spans[0]]
        for span in spans[1:]:
            prev = merged[-1]
            same_page = prev.page_number == span.page_number
            if same_page and len(span.text.strip()) < self.min_section_chars:
                title_part = f"{span.title}\n\n" if span.title else ""
                new_text = f"{prev.text}\n\n{title_part}{span.text}".strip()
                merged[-1] = replace(
                    prev,
                    end_char=max(prev.end_char, span.end_char),
                    text=new_text,
                )
            else:
                merged.append(span)
        return merged


def is_heading(line: str) -> bool:
    """True if line matches any §8.2 heading heuristic."""
    stripped = line.strip()
    if not stripped:
        return False
    if _MARKDOWN_HEADING.match(stripped):
        return True
    if _NUMBERED_SECTION.match(stripped):
        return True
    if _is_medical_header(stripped):
        return True
    if _is_all_caps_heading(stripped):
        return True
    return False


def _is_medical_header(line: str) -> bool:
    normalized = line.strip().rstrip(":").lower()
    if normalized in _MEDICAL_HEADERS:
        return True
    words = normalized.split()
    return len(words) <= 4 and normalized in _MEDICAL_HEADERS


def _is_all_caps_heading(line: str) -> bool:
    stripped = line.strip().rstrip(":")
    if len(stripped) < 4 or len(stripped) > 80:
        return False
    letters = [c for c in stripped if c.isalpha()]
    if len(letters) < 4:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return upper_ratio >= 0.85 and _ALL_CAPS.match(stripped.upper())


def detect_sections(pages: list[PageText]) -> list[SectionSpan]:
    """Detect sections across all pages."""
    return StructureDetector().detect_pages(pages)
