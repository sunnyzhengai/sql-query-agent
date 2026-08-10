# ADR 0033: System of Record + Projections — Delta Is the Record; Graph Engines Are Read Models

**Status:** Accepted
**Date:** 2026-08-10

## Context

ADR 0002 chose Delta tables over an external graph database, with a planned
hybrid (Fabric Graph for deep traversal). Two developments forced a deeper
re-examination:

1. **The graph will not stay a SQL-lineage graph.** The product vision adds
   users (~10,000 in a large org), roles, and security nodes, plus usage and
   endorsement edges (each user touching 100+ nodes). Published research is
   also correct that native graph engines (index-free adjacency) beat SQL
   joins for deep, unbounded, ad-hoc traversal — so "is Delta still right?"
   deserved a first-principles answer, not a re-assertion.
2. **The ultimate goal is self-service reporting, not governance-at-rest.**
   Users certify personal variants of metrics (ADR 0024), building personal
   definition libraries — and the system must eventually stitch certified SQL
   fragments into coherent, *executable* SQL, not return half-finished
   snippets. Storage must be judged against that end state.

Note on comparisons: Neo4j appears in our discussions only as the familiar
reference point for "a graph database." It is not a candidate — the product
ships inside the Microsoft ecosystem (BYOT, ADR 0007), so the graph engine in
scope is the Fabric Graph Model, whose LPG export we already build (ADR 0020).

## Decision

**Delta tables are the system of record. Every specialized engine is a
projection (read model) built from that record — never a second source of
truth.**

- The record: `graph_nodes`, `graph_edges`, closures, `output_metric_logic`,
  governance/event tables — durable, versioned (Delta time travel = free audit
  history, material for a governance product), governed by the customer's
  Entra, readable by every Fabric engine.
- Projections in production today: the Eventhouse semantic catalog (vector
  search) is a projection; the LPG export tables for Fabric Graph are a
  projection. Future projections join the same way — fed from the record,
  rebuildable at will, zero migration of the record itself.
- **Graph-engine workloads are welcome as projections.** Exploratory
  discovery UIs ("show everything connected to this"), recommendations
  ("analysts like you certified…"), and community detection over the usage
  graph are the workloads where index-free adjacency genuinely wins. When
  those ship, they run on the Fabric Graph Model projection — not by
  migrating the record.

### Why the growth projection does not change the storage choice

Separate the new node types by workload, not by count:

- **Usage/endorsement data is a stream, not a graph problem.** Picks and
  confirmations are append-only events (`gov_usage_events`, ADR 0023);
  weights are *derived by aggregation* — exactly the workload columnar
  tables crush and a graph engine serves poorly. Millions of rows/year is
  trivial for append-only Delta/Eventhouse.
- **Security resolution is shallow policy joins.** "Can user U see metric M"
  is user → role → group → metric: 2–3 hops over small dimension tables,
  not deep traversal.
- **The traversal-shaped workload — the step DAG — scales with procs, not
  users.** 1,500 SQL files ≈ 30,000 steps regardless of headcount. Users
  never sit inside calculation chains; they sit beside them in event tables.

### Honest ranking of the original reasons (recorded per feedback: keep the why)

Performance was never the primary reason for Delta. The real order:

1. **Ops and trust (BYOT):** no new server/license/security-review in a
   healthcare tenant; native Fabric, customer's Entra, backed up, auditable.
2. **Determinism and testability:** facts precomputed and verified at build
   time (ADR 0018) beat runtime traversal that can silently go wrong — the
   5/13 undercount made this empirical, not theoretical.
3. **Engine-agnosticism:** one copy of the truth feeds Spark, SQL, KQL,
   Power BI, and any future projection.
4. Performance — and only because the workload was *arranged* so ask-time
   deep traversal never occurs (closures at build time, ADR 0018). For
   workloads where that arrangement is impossible (ad-hoc pathfinding,
   real-time graph analytics), a graph engine is the right tool — as a
   projection, above.

### The stitching goal is a compiler problem, not a database problem

Composing executable SQL from certified fragments = extract ONE metric's
chain (3–50 steps), topologically order it, rewrite fragments into a CTE
pipeline, validate, execute. The working set is tiny and per-request; the
store's only job is indexed fragment lookup by `metric_id`, which Delta
already does. No storage choice makes stitching easier or harder — the hard
work lives in the **Tier-2 certified semantic layer compiler**:

- The topological walk already exists: ADR 0019's description generator
  orders every chain bottom-up today; the stitcher is the same walk emitting
  SQL instead of prompts.
- ADR 0003 stored fragments *specifically* so chains could be reassembled.
- The genuinely hard problems are fragment fidelity: parameter handling,
  temp-table→CTE conversion, cross-database references.
- The safety net is mechanical verification: parse the stitched query back
  through ScriptDom (round-trip), then execute it against data. Compiled and
  validated, never generated and hoped (ADR 0032's spirit, applied to SQL).
- Personal libraries (ADR 0024) are the compiler's second input: personal
  variants compile beside enterprise ones.

## Consequences

- ADR 0002 stands, extended: "Delta vs graph DB" was never either/or — the
  record is Delta; graph engines join as projections when their workloads
  (discovery, recommendations) ship.
- Conditions that would add a graph projection (not migrate the record):
  an exploration UI, recommendation features, or graph analytics over the
  usage graph. Conditions that would revisit the record itself: none
  identified — every engine in the Fabric ecosystem reads Delta.
- The Tier-2 compiler becomes the named home for the stitching goal:
  build-time compilation with ScriptDom round-trip + execution gates. Its
  design is future work; its feasibility no longer depends on storage.
- User/role/security growth lands in event tables and small dimensions, not
  in the traversed graph — the ADR 0018 build-time memory budget is
  unaffected by headcount.
