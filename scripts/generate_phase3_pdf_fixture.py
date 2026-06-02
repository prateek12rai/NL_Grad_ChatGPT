"""One-time helper to create tests/fixtures/phase3/sample_guideline.pdf (requires fpdf2)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "phase3" / "sample_guideline.pdf"


def main() -> None:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        8,
        "Page 1. Introduction to national TB guidelines.\n\n"
        "Contraindications: For multi-drug resistant strains, administer Bedaquiline "
        "under strictly monitored DOTS context.",
    )
    pdf.add_page()
    pdf.multi_cell(
        0,
        8,
        "Page 2. Recommendations for drug-susceptible pulmonary tuberculosis.",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
