# ADR 0003: Store sql_fragments, Not Full SQL Blobs

**Status:** Accepted
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
