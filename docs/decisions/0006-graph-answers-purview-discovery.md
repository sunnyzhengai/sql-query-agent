# ADR 0006: Knowledge Graph Answers Questions; Purview Discovers Reports

**Status:** Accepted
**Date:** 2026-07 (recorded 2026-08-02)

## Context

Purview already catalogs the organization's data estate. Could it ground the
Data Agent directly instead of a purpose-built knowledge graph?

## Decision

The knowledge graph is the brain (answers questions); Purview is the librarian
(finds existing reports). Every question consults both in parallel: the graph
assembles the certified answer, Purview surfaces dashboards that already cover
the topic.

## Consequences

- Purview is a metadata catalog, not a query engine — it stores facts *about*
  data but not the sql_fragments, transformation chains, or dimension filters
  needed to compute an answer; those live only in the graph
- Purview lookup reduces redundant report requests ("the Monthly ED Dashboard
  already tracks this")
- AIVIA complements rather than competes with Purview/Collibra — it fills their
  empty containers with extracted, certified definitions
