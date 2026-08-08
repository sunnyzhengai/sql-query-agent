# Fabric Semantic-Retrieval Surface — Verified Findings

**Date:** 2026-08-08 · **Decision:** [ADR 0030](../decisions/0030-layered-retrieval-search-terms-first.md)
All facts verified against live learn.microsoft.com pages; preview/GA
status noted per item. Re-verify flagged items before implementation.

## The constraint

At ask time, retrieval runs inside the Fabric Data Agent: it generates
and executes SQL/KQL/DAX/GQL — no custom code, no plugins. Semantic
similarity is possible only where the query language itself can (a)
store vectors, (b) rank by distance, and (c) **embed the user's phrase
in-query** (the agent cannot embed anything itself).

## Where similarity works, by engine

| Surface | Vector type/store | Distance fn | In-query embedding | Status |
|---|---|---|---|---|
| **Fabric Warehouse / Lakehouse SQL endpoint** (our Delta tables) | **None** ("Vector: no equivalent") | none | none (text AI_* fns only, preview) | dead end for vectors |
| **Fabric SQL database** (separate item; Data Agent source, T-SQL) | `VECTOR(n)` — GA | `VECTOR_DISTANCE` — GA | `AI_GENERATE_EMBEDDINGS ... USE MODEL` (external model + scoped credential) — preview-or-recent-GA, re-verify | best SQL path |
| **Eventhouse / KQL DB** (Data Agent source, NL2KQL GA) | `dynamic` + `Vector16` encoding — GA | `series_cosine_similarity` — GA | `ai_embeddings` plugin — **preview**; Fabric auth = user impersonation + `azure_openai` callout policy; asker needs OpenAI role | documented one-statement tutorial |

Key naming trap: the plugin is `ai_embeddings` (the older announced
`ai_embed_text` name has no reference page — don't build against it).

## Data Agent internals (GA)

- No automatic vector indexing of schemas/tables/descriptions. Routing =
  schema fetch + source descriptions + instructions.
- **Example query pairs (≤100/source) ARE vector-retrieved** — the one
  built-in semantic mechanism, and a steering lever: the semantic-search
  query *shape* can be taught via examples that are themselves retrieved
  by similarity to the user's question.
- **Azure AI Search index** is a supported source (preview): 3–20 chunks,
  hybrid/semantic search, citations — the sanctioned path for
  unstructured content, external index required.
- Sources as of 2026: Lakehouse/Warehouse/SQL DB/Mirrored (T-SQL),
  Eventhouse (KQL), semantic models (DAX), Graph Model (GQL, preview),
  Ontology (preview), Microsoft Graph, AI Search (preview).

## Build-time embedding options

- Notebook AI functions incl. **`ai.embed`** (pandas + PySpark), default
  built-in model `gpt-5-mini` via Fabric endpoint, BYO Azure OpenAI
  configurable; no preview banner (GA announcement not found — confirm
  if contractual).
- Our existing path: customer's Azure OpenAI embeddings deployment via
  `src/llm_client` in 07 (same key/endpoint plumbing as descriptions).

## Warehouse AI functions (for completeness)

`AI_CLASSIFY`, `AI_SUMMARIZE`, `AI_GENERATE_RESPONSE`, etc. — preview,
~10–30 rows/sec, generative only. No embeddings, no similarity. Not a
retrieval surface.
