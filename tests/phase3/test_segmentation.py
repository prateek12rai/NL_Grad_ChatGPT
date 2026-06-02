"""Phase 3.3 — structural segmentation tests."""

from pathlib import Path

from pipeline.chunking.extractors import extract_document
from pipeline.chunking.models import PageText, SectionSpan
from pipeline.chunking.segmentation import pages_to_units, segment_structurally, split_sentences
from pipeline.chunking.segmentation.semantic_segmenter import DEFAULT_SOFT_MAX_TOKENS
from pipeline.chunking.structure import detect_sections
from pipeline.chunking.tokenization import count_tokens


def test_split_sentences_respects_abbreviations():
    text = "Dr. Smith reviewed cases. e.g. contraindications apply in DOTS programs."
    sents = split_sentences(text)
    assert len(sents) >= 2
    joined = " ".join(sents)
    assert "Dr." in joined
    assert "e.g." in joined
    assert "Dr. Smith" in sents[0]


def test_segment_keeps_contraindication_block_together():
    section = SectionSpan(
        page_number=1,
        start_char=0,
        end_char=200,
        title="CONTRAINDICATIONS",
        text=(
            "For multi-drug resistant strains, administer Bedaquiline under strictly "
            "monitored DOTS context. Do not use with strong CYP3A4 inducers."
        ),
    )
    units = segment_structurally([section], soft_max_tokens=400)
    assert len(units) == 1
    assert "Bedaquiline" in units[0].text
    assert "CYP3A4" in units[0].text
    assert units[0].token_count <= 400


def test_segment_splits_when_exceeds_soft_max():
    long_body = " ".join(["Sentence about clinical management."] * 80)
    section = SectionSpan(
        page_number=1,
        start_char=0,
        end_char=len(long_body),
        title="Background",
        text=long_body,
    )
    units = segment_structurally([section], soft_max_tokens=100)
    assert len(units) >= 2
    for unit in units:
        assert unit.token_count <= 100 or unit.sentence_count == 1


def test_units_never_merge_across_sections():
    sections = [
        SectionSpan(1, 0, 50, "Introduction", "First section sentence one. Sentence two."),
        SectionSpan(
            1,
            50,
            150,
            "Contraindications",
            "For Bedaquiline use DOTS. Monitor liver enzymes.",
        ),
    ]
    units = segment_structurally(sections)
    titles = {u.section_title for u in units}
    assert "Introduction" in titles
    assert "Contraindications" in titles
    intro_units = [u for u in units if u.section_title == "Introduction"]
    contra_units = [u for u in units if u.section_title == "Contraindications"]
    assert all("Bedaquiline" not in u.text for u in intro_units)
    assert any("Bedaquiline" in u.text for u in contra_units)


def test_pages_to_units_html_pipeline(sample_html_path: Path):
    pages = extract_document(sample_html_path, "html").pages
    units = pages_to_units(pages)
    assert len(units) >= 2
    assert all(u.token_count <= DEFAULT_SOFT_MAX_TOKENS for u in units)
    assert all(u.text for u in units)


def test_guideline_structure_fixture():
    fixture = (
        Path(__file__).resolve().parents[1] / "fixtures" / "phase3" / "sample_guideline_structure.txt"
    )
    page = PageText(page_number=1, text=fixture.read_text(encoding="utf-8"), source_path="f.txt")
    sections = detect_sections([page])
    units = segment_structurally(sections)
    assert len(sections) >= 3
    assert len(units) >= 3
    all_text = " ".join(u.text for u in units)
    assert "Bedaquiline" in all_text


def test_count_tokens_nonempty():
    assert count_tokens("clinical guidance") > 0
