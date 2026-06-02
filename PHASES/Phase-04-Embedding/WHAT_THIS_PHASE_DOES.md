# Phase 4 — Embedding & Vector Store (Plain English)

## What this phase is about

Computers cannot “read” text the way humans do for search. We convert each chunk into a **list of numbers** (an embedding) that captures meaning. Similar medical topics get similar numbers.

Those numbers are stored in a **local folder on disk** called `chroma_db` — not in a cloud database. This matches the project rule: your data stays under your control.

We use the **BGE-large** model via Hugging Face (needs a free API token you will add later).

## What you will see when it is done

- A `chroma_db` folder that grows as documents are indexed  
- A small script to test “search for something similar to this question”  

## What we will NOT do yet

- No Groq chat answers (Phase 5)  
- No doctor verification screen (Phase 6)

## Technical architecture (detailed)

See [docs/architecture-phase-4-embedding.md](../../docs/architecture-phase-4-embedding.md) for full design before implementation.
