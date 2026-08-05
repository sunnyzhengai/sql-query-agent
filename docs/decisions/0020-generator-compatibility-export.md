# 0020 — Shape the LPG export to the query generator's habits

**Status:** Accepted
**Date:** 2026-08-05

## Context

After ADR 0017/0018 shipped (resolution-first instructions, USES_TABLE
closure), the Fabric NL2GQL generator was observed to be not merely weak
but **non-deterministic across runs with identical instructions**: one
evening it filtered `metricId` (correct); next morning, same question, it
filtered `name` with the schema-qualified string (0 rows) — while its
provenance footer claimed a "catalog query" it never ran. It has never
once emitted the two-phase resolve-then-traverse flow, a depth
quantifier, or a USES_TABLE hop on its own.

Its habits are stable even when its property choices are not:

1. Put the user's reference string into a `name` equality/CONTAINS filter.
2. Walk `CALCULATED_BY->READS_FROM` as a single-hop chain.

Instruction steering cannot fix a component that ignores instructions
stochastically. But we own the export, and the habits themselves are only
wrong **relative to the data shape**.

## Decision

Make the habitual query the correct query:

1. **`Metric.name` is exported schema-qualified** (identical value to
   `metricId`); the bare object name moves to `bareName`. A qualified
   reference now exact-matches `name`; a bare reference CONTAINS-matches
   both schema twins, surfacing the ambiguity instead of missing.
2. **`CALCULATED_BY` is exported as a materialized closure** — one edge
   from a metric to EVERY transformation in its calculation (same
   derivation as USES_TABLE, targeted at Transformations). The raw
   root-only edges remain in `graph_edges` (Delta) for pipeline code; the
   LPG export is a projection shaped for its one consumer, the generator.
   The shallow `CALCULATED_BY->READS_FROM` chain now returns the complete
   table set.

Local pipeline semantics are untouched: `graph_edges` still stores
root-only c2t; GraphTraverser, metric_logic, and USES_TABLE derivation
read the raw graph, not the export.

## Consequences

- The generator's habitual single-hop chain and name filters both go
  from silently-wrong to correct — no cooperation required from the
  black box.
- "Root steps" are no longer distinguishable inside the LPG (the export
  no longer carries a roots-only edge). No current question needs them;
  if one appears, export a separate HAS_ROOT_STEP edge.
- Step-count answers over the LPG change meaning: CALCULATED_BY
  cardinality is now total steps (88 for reports.USP_Severe_Sepsis),
  which matches what "how many steps" should mean to a user anyway.
- Precedent extended from ADR 0018: when the platform's generator has
  fixed habits, the export contract targets the habits, not the ideal
  schema. The ideal schema lives in the raw graph tables.
