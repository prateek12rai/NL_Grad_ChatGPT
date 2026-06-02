# PHASES — Build Progress Folder

This folder is your **monitoring dashboard** while the project is built step by step.

## How we work together

1. Before each phase, you get a **plain-English explanation** of what will happen.
2. You reply **yes** (or ask questions) before any code is written for that phase.
3. After the phase, we run the **Deep Test** (automatic checks + a short report).
4. Only when tests pass, we explain **Phase N+1** and ask permission again.

**Source of truth for technical details:** [docs/architecture.md](../docs/architecture.md)

## Free & fast (always)

This project targets **$0** on free tiers and **quick** local/CI runs:

- **Groq** (answers) + **Hugging Face** (embeddings only in Phase 4) — not during chunking  
- **Chroma on disk** — no cloud vector DB  
- **Structural chunking** — no extra AI model for splitting text  
- **≤1,000 documents** — keeps everything fast  

Details: [architecture.md §2.3](../docs/architecture.md#23-free--fast-alignment-non-negotiable)

## Folder map

| Folder | What it builds |
|--------|----------------|
| [Phase-01-Foundation](./Phase-01-Foundation/) | Project skeleton, empty apps, safety filters |
| [Phase-02-Scraping](./Phase-02-Scraping/) | Download medical documents from 3 websites |
| [Phase-03-Chunking](./Phase-03-Chunking/) | Split documents into searchable pieces |
| [Phase-04-Embedding](./Phase-04-Embedding/) | Turn pieces into numbers stored on your disk |
| [Phase-05-Backend](./Phase-05-Backend/) | Brain: search + Groq answers (Streamlit) |
| [Phase-06-Frontend](./Phase-06-Frontend/) | Screen for doctors to verify sources (Vercel) |
| [Phase-07-Scheduler](./Phase-07-Scheduler/) | Daily auto-update at 6 AM IST (GitHub) |
| [Phase-08-Integration](./Phase-08-Integration/) | Connect everything and final sign-off |

## Files inside each phase folder

| File | Purpose |
|------|---------|
| `WHAT_THIS_PHASE_DOES.md` | Simple explanation (non-technical) |
| `STATUS.md` | Current state: waiting / in progress / passed / blocked |
| `CHECKLIST.md` | Deep test items copied from architecture |
| `GATE_REPORT.md` | Filled in after tests — pass or fail |

## Current status

**Active phase:** Phase 2 — **COMPLETED (gate passed)**  
**Next:** Phase 3 — Chunking (waiting for your permission)  
**Last updated:** 2026-06-01
