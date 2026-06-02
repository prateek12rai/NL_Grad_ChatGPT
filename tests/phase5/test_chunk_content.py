"""Placeholder chunk detection and Nature boilerplate sanitization."""

from shared.chunk_content import is_placeholder_context, sanitize_display_context

SAMPLE_BOILERPLATE = """
/s41598-026-51801-7 Share this article Anyone you share the following link with will be able to read this content:
Get shareable link Sorry, a shareable link is not currently available for this article.
Copy shareable link to clipboard Provided by the Springer Nature SharedIt content-sharing initiative
Keywords Computed tomography Semantic segmentation Submanifold sparse convolutional networks
Cite this article Alonso-Monsalve, S., Whitehead, L.H. et al. Submanifold sparse convolutional networks for automated 3D segmentation.
Download citation Received : 06 August 2025 Accepted : 29 April 2026 Published : 01 June 2026
Abstract

Background: Kidney tumour segmentation from CT is challenging. Methods: We trained submanifold sparse CNNs.
Results: Dice score improved significantly. Conclusions: Automated segmentation is feasible.
"""


def test_is_placeholder_context():
    assert is_placeholder_context("Mock ingest content for Nature.")
    assert is_placeholder_context("fixture content for ICMR")
    assert not is_placeholder_context("Administer Bedaquiline under DOTS.")


def test_sanitize_display_context_strips_nature_share_boilerplate():
    cleaned = sanitize_display_context(SAMPLE_BOILERPLATE)
    assert "Share this article" not in cleaned
    assert "Get shareable link" not in cleaned
    assert "Springer Nature SharedIt" not in cleaned
    assert "Keywords Computed tomography" not in cleaned
    assert "Download citation" not in cleaned
    assert "Background: Kidney tumour segmentation" in cleaned
    assert "Results: Dice score improved" in cleaned
