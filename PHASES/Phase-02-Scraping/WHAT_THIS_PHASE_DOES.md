# Phase 2 — Scraping (Plain English)

## What this phase is about

We teach the computer to **automatically collect official medical documents** from three trusted sources:

1. **DHR** (Department of Health Research) — Indian health research publications  
2. **ICMR** — Indian national health reports and guidelines  
3. **Nature** — very recent global medical research (only papers from the **last 7 days**)

Documents are saved on your computer in a `data/corpus` folder. We keep at most **1,000 documents**; when full, the **oldest** are removed to make room for newer ones.

We also run text through a **privacy filter** so personal ID numbers are not stored.

## What you will see when it is done

- A list file (`manifest.json`) describing what was downloaded  
- PDF/HTML files in `data/corpus/`  
- A log proving Nature always used the “last 7 days” filter  
- Phase folder `GATE_REPORT.md` = **PASS**

## What we will NOT do yet

- No splitting documents into small search pieces (Phase 3)  
- No AI search index (Phase 4)
