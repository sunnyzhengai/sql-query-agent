# ADR 0003: Store sql_fragments, Not Full SQL Blobs

**Status:** Accepted — amended 2026-08-19 by [ADR 0044](0044-tree-contract-round-trip-descriptions.md): the fragment stays stored verbatim as provenance and audit trail, but it is no longer the description LLM's input; decision facts come from the persisted tree
**Date:** 2026-07 (recorded 2026-08-02)

## Context

Transformation-layer nodes could store either the complete SQL of each metric or
minimal per-step logic snippets.

## Decision

Each transformation node stores a minimal `sql_fragment` tied to one CTE/temp-table
step. The LLM assembles complete queries from fragments plus templates at question
time.

## Consequences

- The graph is composable and auditable: each logic step is individually
  inspectable, certifiable, and reusable across metrics
- Full SQL blobs would be brittle and hard to version; fragments diff cleanly
- Query assembly depends on LLM composition at runtime — acceptable because the
  fragments themselves are verbatim parser output (deterministic provenance)
