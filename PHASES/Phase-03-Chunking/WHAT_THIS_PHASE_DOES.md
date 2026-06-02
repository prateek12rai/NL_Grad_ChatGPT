# Phase 3 — Chunking (Plain English)

## What this phase is about

Long PDFs are hard to search as one block. We **cut each document into smaller meaningful sections** (not random cuts), so a drug warning or guideline does not get split in the middle.

Rules from the project:

- Each piece is at most **512 tokens** (roughly a few paragraphs)  
- Neighbouring pieces **overlap slightly** (80 tokens) so context is not lost  

Each piece stores the **exact original sentence** used later for highlighting when a doctor verifies a source.

## What you will see when it is done

- Chunk files under `data/chunks/` (or similar)  
- Every chunk tagged “unverified” until a human approves it in Phase 6  

## What we will NOT do yet

- No vector / embedding numbers (Phase 4)  
- No chat answers (Phase 5)

## Technical architecture (detailed)

See [docs/architecture-phase-3-chunking.md](../../docs/architecture-phase-3-chunking.md) for full design before implementation.
