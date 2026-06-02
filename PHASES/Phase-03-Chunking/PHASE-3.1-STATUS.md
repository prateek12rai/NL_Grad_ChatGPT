# Phase 3.1 — Text Extraction — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [docs/architecture-phase-3-chunking.md](../../docs/architecture-phase-3-chunking.md) §7 |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `src/pipeline/chunking/models.py` | `PageText`, `ExtractionResult` |
| `src/pipeline/chunking/extractors/normalize.py` | NFC, CRLF, space collapse, control strip |
| `src/pipeline/chunking/extractors/pdf_extractor.py` | pdfplumber → pypdf fallback |
| `src/pipeline/chunking/extractors/html_extractor.py` | BeautifulSoup, section per heading |
| `src/pipeline/chunking/extractors/__init__.py` | `extract_document(path, content_type)` |
| `scripts/extract_preview.py` | Preview extraction on manifest |
| `tests/phase3/test_extraction.py` | Automated tests |

## How to verify

```powershell
cd C:\Users\Acer\Downloads\NL_Grad_ChatGPT
pip install -r requirements.txt
$env:PYTHONPATH="src"
pytest tests/phase3/test_extraction.py -v
python scripts/extract_preview.py
```

Optional PDF fixture:

```powershell
pip install fpdf2
python scripts/generate_phase3_pdf_fixture.py
```

## Next sub-phase

**Phase 3.2 — Structure detection** (`src/pipeline/chunking/structure/detector.py`)
