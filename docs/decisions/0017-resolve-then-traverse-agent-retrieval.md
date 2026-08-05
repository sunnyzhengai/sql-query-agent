# 0017 — Resolve-then-traverse: anchor resolution before any graph query

**Status:** Accepted
**Date:** 2026-08-04

## Context

Round 2 of the Delta-vs-Graph rematch surfaced a family of agent defects with
one shared root: the NL2GQL query generator embeds the **user's raw string**
into query filters. Observed failures, each individually patched before the
pattern was recognized:

- Case-sensitive `CONTAINS 'sepsis'` missed `Sepsis` — "no sepsis metrics
  exist" (both agents, identically).
- A schema-qualified reference (`reports.USP_Severe_Sepsis`) exact-matched
  against the bare `name` property — 0 rows — false "not in the knowledge
  base." The mirrored failure: a bare reference auto-qualified by the agent,
  then matched against the bare property.
- The generator ignored three explicit instruction rules (case folding, depth
  quantifiers, identity property choice) — instruction-level steering of query
  synthesis has a low ceiling.

Users rarely type exact object names at all — they ask about **topics**
("sepsis screening compliance"). Topic-to-metadata matching is a semantic
task; a query language's string predicates are the wrong tool for it, and no
amount of WHERE-clause prescription makes them the right tool.

Prior art: the founder's earlier Neo4j implementation of AIVIA used exactly
this shape — LLM extracts words, words are searched across all nodes and
properties via full-text indexes, matched nodes become traversal anchors,
Cypher assembles connecting paths, ambiguity goes to a human. This is
anchor-based graph retrieval (the pattern GraphRAG later converged on).

## Decision

The agent NEVER puts a user-typed string into a traversal filter. Question
answering is a fixed two-phase flow:

1. **Resolve.** Deterministic retrieval produces candidates — today, a full
   catalog fetch per layer (`MATCH (m:Metric) RETURN metricId, name,
   description` — a query with no WHERE clause cannot miss); at scale, top-k
   from a search index. The **LLM matches semantically in context**: it is the
   fuzzy matcher (typos, synonyms, topic phrasing, case — all native LLM
   strengths, all failure modes of lexical predicates). Resolution is
   **breadth-first over all layer catalogs, never depth-first with early
   exit** — a phrase matching a metric description is not evidence it isn't a
   table name. Layer priority (metric > CTE > table > column) is a
   tie-breaker; token shape (identifier-like vs. topic-like) and question
   intent are ranking evidence; columns are only searched within
   already-anchored tables. Output: **certified keys + types**
   (`{type: Table, key: DBO.HOSPITAL_ENCOUNTERS}`), never prose.
2. **Traverse.** Anchor types + question intent select one of ~five
   pre-shaped path templates (metric→tables, table→metrics, metric↔metric
   shared sources, table→columns, metric→steps). The generator's only job is
   filling certified keys into a known-good shape. Exact matching is safe
   here — that is what keys are for.

Ambiguity that survives ranking (two metrics named `USP_ED_Sepsis`) is
**surfaced to the human**, never silently resolved — the HITL top-X from the
Neo4j design, in agent form.

### Scale path (decided, not yet needed)

Per-question resolution cost is O(catalog) **tokens** — one fetch covers all
search words in a question (~20k tokens at dev size; latency dominated by
orchestrator overhead, not data). When a layer's catalog outgrows the context
window (~1–2k rows), that layer swaps fetch-all for a **search index**:
lexical (folded exact/prefix/trigram — exact-name hits are the strongest
signal and embeddings are weak on underscored identifiers) UNION vector
similarity (for topic phrases; embeddings stored in a Delta table, brute-force
cosine in Spark — local to Fabric, no FAISS dependency to ship), LLM reranks
the shortlist. The architecture is unchanged; only candidate production swaps.
Embeddings are computed at build time, incremental by content hash.

## Consequences

- Instructions shrink from query-recipe prescriptions to principles; the LLM
  is empowered where it is strong (semantics) and removed from where it is
  weak (query synthesis, lexical matching).
- Case/typo/identity failure classes die structurally: no user string ever
  reaches a filter.
- The catalogs (names + descriptions per layer) become first-class product
  surfaces — see ADR 0019 for the CTE layer.
- Pairs with ADR 0018: templates stay single-hop because depth is
  precomputed.
- The Fabric Data Agent is the distribution vehicle, not the ceiling: the
  full Neo4j-style pattern (real full-text anchoring, ranked path assembly,
  HITL path selection) needs a retrieval layer we control — a natural premium
  tier, on the roadmap, not this build.
