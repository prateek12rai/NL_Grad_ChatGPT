# Phase 3.2 — Structure Detection — COMPLETED

| Field | Value |
|-------|--------|
| **Status** | COMPLETED |
| **Spec** | [docs/architecture-phase-3-chunking.md](../../docs/architecture-phase-3-chunking.md) §8 |
| **Date** | 2026-06-01 |

## What was built

| Module | Purpose |
|--------|---------|
| `src/pipeline/chunking/models.py` | `SectionSpan` dataclass |
| `src/pipeline/chunking/structure/detector.py` | Heading heuristics + per-page algorithm |
| `src/pipeline/chunking/structure/__init__.py` | `detect_sections(pages)` |
| `scripts/structure_preview.py` | Extract + section preview on manifest |
| `tests/phase3/test_structure.py` | Automated tests |

## Heading signals (§8.2)

- Markdown `#` headings  
- Numbered sections (`1.`, `2.3`)  
- Known medical headers (Contraindications, Recommendations, …)  
- ALL CAPS lines (4–80 chars)  
- Sections &lt; 20 characters merged into previous section  

## Verify

```powershell
$env:PYTHONPATH="src"
pytest tests/phase3/test_structure.py tests/phase3/test_extraction.py -v
python scripts/structure_preview.py
```

## Next

**Phase 3.3 — Semantic segmentation** (`segmentation/semantic_segmenter.py`)
