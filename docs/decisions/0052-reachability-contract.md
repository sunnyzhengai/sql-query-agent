# 0052 — The reachability contract: no graph payload invisible by accident

Date: 2026-08-21
Status: accepted
Category: architecture
Axioms: C1 (reflexive application)

## Context

The 2026-08-21 ask-surface audit found the graph faithfully holding
6,528 nodes while the engine's ops reached 472 — 7% — and nobody had
decided that. Layers landed in the graph (decisions, columns, report
edges) with no op to the ask-surface and no exclusion on record. The
frontier was undeclared, and it was discovered the same way the
EMR-joins gap was: a human tripped over it (Sunny's "how is IP_SEPSIS
defined" returning "cannot be provided" while the graph held
tech:reporting.ip_sepsis).

Sunny's ruling (relayed from the review session): the audit is spec:C1
violated reflexively — the search surface is a projection of the
graph, and there was never a declared inventory of what the projection
covers versus excludes. Make the audit permanent before (or alongside)
the backfill.

## Decision

`src/reachability.py` holds one row per graph payload — every
NodeLayer, every EdgeType, every catalog kind. Each row is one of two
honest things:

- **reachable** — names the op(s)/query constant(s) that touch it and
  a marker string; `tests/test_reachability.py` verifies the marker
  appears in the actual implementation text. A row that claims reach
  the code doesn't implement fails CI.
- **excluded** — a stated reason and, where ruled, the queue position.
  An exclusion is a decision on record, never an accident.

Totality is enforced: adding a NodeLayer, EdgeType, or catalog kind
without a row fails CI. The hand audit is now a query that cannot rot.

## Consequences

- The 2026-08-21 backfill order (Sunny): decisions → report links →
  columns → SQL-text. Each work item flips its exclusion rows to
  reachable rows in the same commit that wires the op — the contract
  records the frontier moving.
- Decision-site content crossing into ask-path prompts passes the
  ADR 0025 PHI gate (export-side and read-time) before the layer's
  row flips.
