# ADR 0006: Knowledge Graph Answers Questions; Purview Discovers Reports

**Status:** Accepted — amended 2026-08-19: since [ADR 0040](0040-consumption-layer-reports-measures.md), reports extracted from TMDL lineage are first-class graph nodes and the graph answers report-coverage questions natively; Purview remains the librarian for estate assets *outside* the extracted corpus (optional adapter per ADR 0009)
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
