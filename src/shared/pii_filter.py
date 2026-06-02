"""Block PII patterns from ingest/chunk pipelines (architecture §7.4, PRD §4.1)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Aadhaar: 12 digits, optional spaces/dashes
AADHAAR_RE = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")

# PAN: AAAAA9999A
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE)

# Indian mobile: +91 optional, leading 6-9
PHONE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}\b")

# Email
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    re.IGNORECASE,
)

# Common password/credential patterns in text
CREDENTIAL_RE = re.compile(
    r"\b(password|passwd|api[_-]?key|secret[_-]?key)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PiiScanResult:
    is_clean: bool
    violations: tuple[str, ...]


def scan_text(text: str) -> PiiScanResult:
    """Return whether text is free of configured PII patterns."""
    violations: list[str] = []
    if AADHAAR_RE.search(text):
        violations.append("aadhaar")
    if PAN_RE.search(text):
        violations.append("pan")
    if PHONE_RE.search(text):
        violations.append("phone")
    if EMAIL_RE.search(text):
        violations.append("email")
    if CREDENTIAL_RE.search(text):
        violations.append("credential")
    return PiiScanResult(is_clean=len(violations) == 0, violations=tuple(violations))


def reject_if_pii(text: str) -> None:
    """Raise ValueError if PII detected."""
    result = scan_text(text)
    if not result.is_clean:
        raise ValueError(f"PII detected: {', '.join(result.violations)}")
