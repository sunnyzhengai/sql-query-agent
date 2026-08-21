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

## Ratification of SPEC §3b (the design-review clause)

This ADR **ratifies SPEC.md §3b** (v0.6, mandated by Sunny
2026-08-21): every new artifact class answers the three questions
before its first line of code, and the answers become its registry
rows. The reachability work is the clause's first live use; its three
answers, as the clause requires a design review to cite:

1. **Inventory (spec:C1):** `src/reachability.py` — every NodeLayer ×
   EdgeType × catalog kind carries exactly one row: a named op whose
   implementation text CI verifies, or an exclusion with a reason and
   queue position. 24 payloads, no undeclared frontier.
2. **Conservation (spec:C2):** the transform equation, verified live:
   **432 transform nodes = 413 catalog steps ⊎ 19 `__final_select__`
   terminals** — the residual is fully named (structural passthrough
   terminals, deliberately uncataloged), no third bucket. At the node
   level: 6,528 graph nodes = reachable-layer rows ⊎ excluded-layer
   rows, with columns and decision→column lineage as the recorded
   exclusions.
3. **Drift (STPA):** two mechanical loops. Enum-level:
   `tests/test_reachability.py` — a new NodeLayer/EdgeType/catalog
   kind without a row is a red build before any data exists.
   Store-level: `devtools/reachability_audit.py` — run after any
   pipeline rerun, exits 1 naming every store payload without a
   declaration and every uncatalogued transform that is not a
   `__final_select__` terminal (a vanished step, not an exclusion).

**Calibration finding (recorded per the clause's own instruction):**
the clause was straightforward to satisfy here EXCEPT that one
enforcement point cannot live in CI — store-level conservation needs
a live connection, so the drift answer splits into a CI leg (enums,
free, always on) and an audit leg (store, run on rerun/export
events). Artifact classes whose frontier exists only in tenant data
should expect the same split; the audit script is the pattern.

## Consequences

- The 2026-08-21 backfill order (Sunny): decisions → report links →
  columns → SQL-text. Each work item flips its exclusion rows to
  reachable rows in the same commit that wires the op — the contract
  records the frontier moving.
- Decision-site content crossing into ask-path prompts passes the
  ADR 0025 PHI gate (export-side and read-time) before the layer's
  row flips.
