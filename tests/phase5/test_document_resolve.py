"""Manifest title matching for clarification follow-ups."""

from api.rag.document_resolve import (
    extract_publication_date,
    resolve_document_id_from_query,
    title_match_score,
)


def test_title_match_score_high_for_embedded_title():
    title = "Gentrification, measures of neighborhood change, and infant mortality in Michigan"
    query = (
        "Gentrification, measures of neighborhood change, and infant mortality in Michigan\n"
        "Published: 01 June 2026\n"
        "i want main findings"
    )
    assert title_match_score(title, query) >= 0.5


def test_resolve_finds_manifest_document():
    title = "Gentrification, measures of neighborhood change, and infant mortality in Michigan"
    query = f"{title}\nPublished: 01 June 2026\nmain findings"
    doc_id = resolve_document_id_from_query(query)
    assert doc_id == "sha256:d141e5d4de08eeec"


def test_resolve_returns_none_for_unknown_article():
    query = (
        "Validating the ADFSCI hypotension symptom domain as a scalable patient "
        "reported outcome measure in spinal cord injury\n"
        "Published: 01 June 2026\n"
        "i want main findings"
    )
    assert resolve_document_id_from_query(query) is None


def test_extract_publication_date_from_published_line():
    d = extract_publication_date("Published: 01 June 2026\nmain findings")
    assert d is not None
    assert d.isoformat() == "2026-06-01"
