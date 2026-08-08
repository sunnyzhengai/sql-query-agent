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

## Round 2 findings (2026-08-08, deep-dive on the L3 path)

- **AI_GENERATE_EMBEDDINGS on Fabric SQL DB:** documented with no preview
  banner (customer's own Azure OpenAI with key auth explicitly supported
  via DATABASE SCOPED CREDENTIAL + CREATE EXTERNAL MODEL); explicit GA
  statement exists only for Azure SQL DB/MI — treat Fabric as
  GA-equivalent-unconfirmed.
- **Exact scan is the documented pattern under 50k vectors** — our
  catalog (~10k rows at enterprise scale) needs no vector index. ANN
  indexes (CREATE VECTOR INDEX / VECTOR_SEARCH) are preview on Fabric
  SQL DB; not needed.
- **THE GATE (undocumented, needs a live probe):** the add-datasources
  doc says the agent's NL2SQL tool "executes the query through the SQL
  Analytics Endpoint" — for a Fabric SQL DB that would be the READ-ONLY
  OneLake-mirror surface where AI_GENERATE_EMBEDDINGS (and possibly
  VECTOR columns) do not exist. Whether SQL-DB sources run on the
  operational engine instead is not disambiguated anywhere. Probe: add a
  SQL DB source, seed an example pair containing
  `ORDER BY VECTOR_DISTANCE(emb, AI_GENERATE_EMBEDDINGS(...))`, inspect
  the run steps. If it executes: L3 is real. If not: L3 falls back to
  Eventhouse/KQL (ai_embeddings preview) or waits for platform support.
- **Example pairs:** retrieved by vector similarity, top 3–4 injected as
  few-shot (docs disagree on k); ≤100 pairs/source; pairs that fail
  schema validation are silently unused; agent instructions cap at
  15,000 chars; a fabric-data-agent-sdk exists (add_fewshots,
  evaluate_few_shots). Docs position examples as complements to
  instructions for shapes "hard to describe in plain instructions."
- **Nightly write path lakehouse → SQL DB is explicit** (no reverse
  mirroring): Spark connector (preview; Entra passthrough; use
  truncate not overwrite — overwrite drops VECTOR columns) or plain
  TDS. Recommended pattern: write TEXT columns, then in-database
  `UPDATE ... SET emb = AI_GENERATE_EMBEDDINGS(...)` (documented
  Example C) rather than shipping vectors through Spark.
- **Purview glossary:** multi-asset term assignment is GA (Data Map
  assignedEntities, stable 2023-09-01). Classic catalog is in support
  mode; Unified Catalog is the forward surface and its custom metadata
  (preview) supports NUMERIC attributes on terms — the home for usage
  weight (classic term templates have no numeric type; weight rides in
  the description meanwhile).

## PROBE RESULT (empirical, 2026-08-08) — beyond the docs

The undocumented gate is now answered first-hand: **Data Agent queries
against a Fabric SQL database run on the analytics-endpoint mirror,
not the operational engine.** Evidence: the agent's example-query
validator rejected `AI_GENERATE_EMBEDDINGS` ("not a recognized
built-in function name") AND could not see the `emb` column ("Invalid
column name") — the VECTOR column is dropped from mirroring, and the
agent's Data panel confirmed it (column absent from the schema list).
Direct execution in the same database worked perfectly (semantic match
correct, 1.1 s). L3-on-SQL-DB is not viable today; see ADR 0030 probe
verdict for the fork.

## Warehouse AI functions (for completeness)

`AI_CLASSIFY`, `AI_SUMMARIZE`, `AI_GENERATE_RESPONSE`, etc. — preview,
~10–30 rows/sec, generative only. No embeddings, no similarity. Not a
retrieval surface.
