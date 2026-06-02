"""Phase 3 — document chunking pipeline."""

from pipeline.chunking.extractors import extract_document
from pipeline.chunking.models import (
    ChunkDraft,
    ExtractionResult,
    PageText,
    SectionSpan,
    TextUnit,
)
from pipeline.chunking.segmentation import pages_to_units, segment_structurally
from pipeline.chunking.structure import detect_sections
from pipeline.chunking.metadata import (
    drafts_to_chunk_records,
    document_to_chunk_records,
    format_chunk_id,
)
from pipeline.chunking.orchestrator import ChunkingOrchestrator, ChunkingResult
from pipeline.chunking.tokenization import pages_to_chunk_drafts, units_to_chunk_drafts

__all__ = [
    "PageText",
    "SectionSpan",
    "TextUnit",
    "ChunkDraft",
    "ExtractionResult",
    "extract_document",
    "detect_sections",
    "segment_structurally",
    "pages_to_units",
    "units_to_chunk_drafts",
    "pages_to_chunk_drafts",
    "format_chunk_id",
    "drafts_to_chunk_records",
    "document_to_chunk_records",
    "ChunkingOrchestrator",
    "ChunkingResult",
]
