# ADR 0037: The Completed Algebra — Traverse, Result-Set Kernels, Closures as Cache

**Status:** Accepted (methodology amendment approved by Sunny, 2026-08-13)
**Date:** 2026-08-13

## Context

Sunny's completeness challenge exposed two errors in the ADR 0036
algebra as first stated: (1) in a graph model, relational JOIN is edge
traversal — the algebra lacked it as a primitive; (2) the claim that
transitive closure "provably required" build-time materialization
conflated first-order completeness with what the algebra may include:
add traversal with unbounded depth (the fixpoint/Kleene-star of graph
calculi) and reachability is expressible AT ASK TIME, correctly,
without precomputation.

## Decision

**Fourth graph primitive — registered in the methodology manifest:**

    traverse(from_nodes, edge_types, direction, depth: 1..N | *)

- depth 1 = join (follow one edge kind one hop)
- depth * = transitive closure (lineage, reachability)
- Deterministic BFS in code over graph_edges; starting nodes come from
  confirmed plans (surfaced/user-named ids only — guarantee 1 applies).
- Data-shaped justification: the store admits following edges; join
  and closure are the depth-1 and depth-* cases of one operation.

**Result-set kernels (deterministic code over DISPLAYED sets only):**
filter, project, sort, group/aggregate, and set-join across two
visible result sets (for value-relations that are not edges, e.g.
"stewards who are also developers"). Together with the three compare
kernels these give full local relational algebra over materialized
results.

**Completeness statement:** search(exact) ∪ retrieve ∪ traverse ∪
update + the local kernels express every first-order-plus-transitive-
closure query over the graph (the Datalog/GQL expressive core) as a
finite composition. Semantic search remains a deliberately
extra-algebraic finder (complete: false forever). Expressiveness, not
feasibility: pathological plans are declinable at confirmation — the
regulator bounds cost.

**Closures reclassified: cache, not architecture.** ADR 0018/0033's
materialized closures are ACCELERATIONS of traverse(depth=*) over hot
paths — standard materialized-view doctrine. Correctness comes from
the algebra; the cache becomes CHECKABLE: validation gains a
closure-vs-live-traverse consistency diff (stale-closure bugs,
previously undetectable in principle, become a computed health check
on the admin dashboard).

## Consequences

- op_traverse + the result-set kernels are registered in
  src/methodology.py (this ADR is their amendment reference);
  implementation follows the release-scoping rule (ROADMAP).
- The lineage question class ("what is downstream of table T") moves
  from unsupported-refusal to a one-primitive plan the moment
  op_traverse ships.
- ADR 0018/0033 stand, reinterpreted: materialization is optional
  performance engineering with a mandatory consistency check.

## Margin note (2026-08-20): the census gap

The completeness claim ("every first-order-plus-transitive question")
described the ALGEBRA; the exposed plan vocabulary could not express
plain enumeration ("how many metrics are there") until the census
primitive shipped (1.38.0) — demand-logged exactly as ADR 0034's punch
list predicted (`enumerate(kind, filter)` was its first entry). The
census closes that gap between the claimed algebra and the exposed
vocabulary; the remaining punch-list verbs stand.
