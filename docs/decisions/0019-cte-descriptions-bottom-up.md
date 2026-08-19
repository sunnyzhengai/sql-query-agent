# 0019 — CTE descriptions, generated bottom-up, before metric descriptions

**Status:** Accepted — amended 2026-08-19 by [ADR 0044](0044-tree-contract-round-trip-descriptions.md): bottom-up ordering, content-hash caching, and metric-from-roots composition survive; the step input changes from raw `sqlFragment` to typed decision-tree facts, and acceptance changes from string-space grounding to blind round-trip verification
**Date:** 2026-08-04

## Context

A CTE is where a developer **named a business concept** (`EligibleEncounters`,
`FirstLactateDraw`). The metric is the deliverable; the CTE is the smallest
certified unit of business definition — questions like "how do we define an
eligible encounter?" anchor at the Transformation layer, not at a Metric or a
table. Resolution (ADR 0017) therefore needs a searchable Transformation
catalog. Today Transformation nodes carry `name` + `sqlFragment` but **no
description** — searchable only when the developer named the CTE well, blind
when they didn't (`cte2`, `tmp_final`).

## Decision

Generate descriptions for every Transformation, and generate them **before**
metric descriptions, walking the DAG bottom-up in topological order:

1. **CTE description** ← its own `sqlFragment` + the names/descriptions of
   its direct dependencies (already described, by ordering). Dependencies
   provide *context, not content* — each description must stay grounded in its
   own fragment so a bad description cannot cascade up the chain.
2. **Metric description** ← composed from its root CTEs' descriptions — the
   LLM summarizes ~3–30 certified one-liners instead of hundreds of lines of
   raw T-SQL: cheaper, more faithful, and vocabulary-consistent (a shared CTE
   is described once, and every metric built on it inherits the phrasing).

Generation mechanics:

- **Incremental by content hash** — keyed on the fragment's hash (`sql_hash`
  machinery), so re-runs only describe new or changed CTEs.
- **LLM boundary:** a batch API call (first pass: OpenAI-compatible endpoint
  via devtools, key in gitignored `.env`; production: the customer's Azure
  OpenAI, behind the `AgentBackend` protocol — we never ship a key). The Data
  Agent is the *consumer* of descriptions, never the generator.
- **Anonymization/leak gate is mandatory** before any fragment leaves the
  tenant — `sqlFragment` is the payload most likely to carry embedded
  literals (dates, thresholds, identifiers). First real consumer of the
  PHI-scanning-at-ingestion work.
- Recorded as cassettes (record/replay) so tests and CI run offline.

## Consequences

- The Transformation catalog (432 rows at dev size) joins the resolution
  funnel as the middle layer: 28 metrics → 432 CTEs → tables → columns.
- Metric descriptions improve and get cheaper at the same time (summaries of
  summaries).
- Governance bonus: semantically described CTEs make logic-reuse and
  inconsistency detection queryable — same-name-different-logic and
  same-logic-different-name across the corpus is steward-queue material no
  human SQL review would find.
- Adds a build-time LLM dependency to 07 (already the LLM notebook); dev cost
  ~432 calls once, then pennies via hash-keyed cache.
