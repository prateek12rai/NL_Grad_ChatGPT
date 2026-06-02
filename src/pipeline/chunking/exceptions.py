"""Extraction errors (architecture §7.7)."""


class ExtractionError(Exception):
    """Base extraction failure."""


class FileNotFoundExtractionError(ExtractionError):
    """Corpus file missing on disk."""


class EmptyDocumentError(ExtractionError):
    """No extractable text after normalization."""


class EncryptedPdfError(ExtractionError):
    """PDF requires password / encrypted."""
