"""Phase 3.2 — structure detection."""

from pipeline.chunking.structure.detector import StructureDetector, detect_sections

__all__ = ["SectionSpan", "StructureDetector", "detect_sections"]

# Re-export model for convenience
from pipeline.chunking.models import SectionSpan  # noqa: E402
