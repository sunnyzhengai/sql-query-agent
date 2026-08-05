# 0018 — Materialize the metric→table closure as USES_TABLE edges

**Status:** Accepted
**Date:** 2026-08-04

## Context

The worst Round-2 defect was a **silent undercount presented as complete**:
"which metrics read HOSPITAL_ENCOUNTERS?" returned 5 of 13; "which tables
does USP_ED_Sepsis use?" returned 11 of 29. Local reproduction matched the
agent exactly: the generated GQL was single-hop
`CALCULATED_BY->READS_FROM`, but `CALCULATED_BY` links a Metric only to its
~3 ROOT steps — the full calculation is the transitive closure of
`DEPENDS_ON` (dozens of steps, 634 edges). Instruction fixes (depth-semantics
rules, `DEPENDS_ON{0,50}` patterns) were added, and the generator **still
emitted shallow patterns** — and worse, echoed the instructed pattern in its
provenance footer while executing a different query.

In Cypher terms the wish is "declare the destination, let the engine
traverse." But someone must still write the pattern, and here that someone is
an LLM with a proven shallow-pattern bias that we cannot retrain.

## Decision

**Compile the depth away.** We control the graph, and the build pipeline
already computes the closure deterministically (`GraphTraverser`). At export
time, materialize a derived edge:

    (Metric)-[:USES_TABLE]->(Technical table)   — the full DEPENDS_ON closure,
                                                  precomputed, count-verified

exported as `graph_edge_uses_table` alongside the raw edge tables. The raw
edges (`CALCULATED_BY`, `DEPENDS_ON`, `READS_FROM`) remain — step-level
questions still need them — but the two highest-traffic question shapes
(metric→tables, table→metrics) become **single hops**, which is precisely the
query shape the generator naturally writes. The generator's weakness becomes
harmless instead of wrong.

Guarantees:

- Derivation is pure, tested code under the same contract regime as every
  table (registry entry, reference invariants, postcondition gate in 05).
- **Count-oracle tests** pin the certified truth from recorded fixtures
  (13 readers of HOSPITAL_ENCOUNTERS, 32 tables under
  reports.USP_Severe_Sepsis, 7 readers of MEDICATION_ORDERS) — the exact
  numbers the agent must reproduce, so a silent undercount in the derivation
  itself is impossible to ship.

## Consequences

- Q4-class questions stop being depth traps; no `{0,50}` quantifier for the
  generator to forget.
- Intelligence moves out of fragile prompt rules into certified structure —
  the product thesis (the graph should be so well-shaped that a naive query
  cannot be wrong) applied to the agent's own queries.
- Cost: one more edge table (≈ metrics × avg tables ≈ hundreds of rows —
  trivial), one more Graph Model mapping, computed at build time where cost
  is amortized and testable.
- Precedent: when a question shape matters and the platform's generator is
  weak at it, prefer materializing the shape at build time over prompting
  around it.
