"""Phase 1.4 — PII filter tests."""

import pytest

from shared.pii_filter import reject_if_pii, scan_text

# --- fixtures: samples that MUST be blocked ---
PII_POSITIVE_SAMPLES = [
    ("aadhaar spaced", "Patient ID 1234 5678 9012 for records"),
    ("aadhaar dashed", "UID 1234-5678-9012"),
    ("pan", "PAN ABCDE1234F submitted"),
    ("phone", "Call +91 9876543210 tomorrow"),
    ("email", "Contact researcher@example.org"),
    ("credential", "password: secret123"),
]

# --- samples that MUST pass ---
PII_NEGATIVE_SAMPLES = [
    ("clinical text", "For multi-drug resistant strains, monitor DOTS context."),
    ("year only", "Publication year 2026 guidelines update."),
    ("icmr url", "https://www.icmr.gov.in/reports"),
]


@pytest.mark.parametrize("label,text", PII_POSITIVE_SAMPLES)
def test_pii_detected(label: str, text: str):
    result = scan_text(text)
    assert not result.is_clean, f"Expected PII in: {label}"


@pytest.mark.parametrize("label,text", PII_NEGATIVE_SAMPLES)
def test_clean_text(label: str, text: str):
    result = scan_text(text)
    assert result.is_clean, f"False positive for: {label} -> {result.violations}"


def test_reject_if_pii_raises():
    with pytest.raises(ValueError, match="PII detected"):
        reject_if_pii("email me at user@hospital.in")
