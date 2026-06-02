"""Extractor protocol — Phase 3.1."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pipeline.chunking.models import ExtractionResult


class BaseExtractor(ABC):
    """Extract normalized PageText list from a corpus file."""

    name: str

    @abstractmethod
    def extract(self, path: Path) -> ExtractionResult:
        """Return non-empty pages or raise EmptyDocumentError."""
