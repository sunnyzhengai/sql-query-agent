# The Question Map — first principles, top-down

<!-- TIER: BLUEPRINT — generated marker, do not remove.
     Component key: question (src/trace_registry.py ARCHITECTURE_COMPONENTS)
     Enforced by tests/test_trace_registry.py hierarchy checks. -->

> **Blueprint tier.** This file satisfies axiom groups **axm:S**
> (Specification) · **axm:M** (Mind) from
> [AI_VIA_AXIOMS.md](../AI_VIA_AXIOMS.md), and is the architecture home
> for 5 decisions
> (see [TRACE_MAP.md](TRACE_MAP.md#the-blueprint-tier) for the full
> chain: decision → component → axioms → code → tests).

Derived 2026-08-18 (review session + Sunny; Layer 0 approved by Sunny).
The product exists to answer user questions about metadata. Everything
below derives from those questions — and the built system, which grew
bottom-up, passes this top-down audit with three named gaps.

> **RECONCILED 2026-09-01 — read this first.** The families below remain
> a useful *storage and coverage* audit: they answer "does the graph
> hold what these questions need?" They are **not** a runtime routing
> table, and clause 2 of the July doctrine has been superseded twice.
> ADR 0062 **abolished question types outright** ("classes ARE types,
> and types can never be enumerated" — Sunny's long-standing objection,
> now law): the answer's shape EMERGES from the matched subgraph, and
> no enumeration of question shapes may exist in the control path
> (`spec:R2`). ADR 0060 removed the LLM from routing entirely
> (`spec:R1`). Use this map to ask *what must the storage support*;
> never to ask *which route does this question take*.

## The governing model (as amended)

1. **Shape classes shape the STORAGE** — questions are unbounded.
   Storage anticipates classes, never individual questions. (Stands.)
2. ~~Questions are handled at runtime as LLM-planned compositions~~ —
   **SUPERSEDED by ADRs 0060 + 0062.** The LLM parses the sentence to
   entity phrases + relation words over a small closed lexicon; code
   composes the traversal; the reading is confirmed on glass before
   anything executes; the shape emerges from what matched. The LLM
   never routes, never composes a query, never authors a verdict.
   Shape-specific tools remain banned by CI (methodology tests) — that
   ban is now the weaker half of `spec:R2`.
3. **Precomputation is only verifiable cache** of hot algebra results
   (e.g. the uses_table closure), never per-question answer tables.
   (Stands — `spec:D1`.)

## Layer 0 — question families (APPROVED 2026-08-18)

| Family | Archetype question | Asked by |
|---|---|---|
| A. Meaning | What does this report/metric measure, exactly? | analyst, clinician |
| B. Provenance | Where does this number come from? | analyst, auditor |
| C. Impact | If I change this table/column/proc, what breaks? | developer, admin |
| D. Discovery | Does a report for X already exist? What exists about Y? | everyone |
| E. Trust | Who owns this? Certified? When did it last change? Stale? | steward, leadership |
| F. Consistency | Are these definitions the same? Why do A and B disagree? | the founding demo question |
| G. Health | What failed, what fell off, what's the coverage? | admin |

## Layers 1–4 — shape → storage → steps → notebooks

| Family | Answer shape | Storage | Built by | Status |
|---|---|---|---|---|
| A | card (prose + quoted criteria) | output_metric_logic (Delta, 1 row/entity) | 02→03→04, English 07/07b | SHIPPED |
| B | path (report→proc→steps→tables) | graph_nodes/edges (+ report layer) | 02, 12, 03 | SHIPPED |
| C | closure (reachable set) | graph edges + cached closures (uses_table) | 03, 05 | SHIPPED |
| D | ranked list (semantic) | semantic catalog + vector index | 11 | SHIPPED |
| E | card + timeline | gov_* event tables + card attributes | stewards, certification, publish log | PARTIAL — freshness missing (gap 2) |
| F | aligned diff of decompositions | step-grain fragments + the diff kernel | ADR 0043 (`src/graph/decomposition_diff.py`) | SHIPPED — gap 1 closed |
| G | funnel (counts → reasons) | fallout rows + funnel view | `src/governance/funnel.py` (ADR 0039) | SHIPPED — gap 3 closed |

## The three gaps of 2026-08-18 — all closed

Recorded here as lineage; none is open. (The handoff documents these
once pointed at have since been retired.)

1. **F / Comparison** — the founding question, once the least-served
   shape. CLOSED by **ADR 0043**, the diff kernel: a generic,
   step-aligned decomposition comparison composing with search/retrieve
   — not the banned `compare_*` tool. Its verdict shape is now also the
   content-hash partition the 0054 sweep and the 0060 lexicon's
   same/different primitive both build on.
2. **E / Freshness** — CLOSED by the content-hash lifecycle: ADR 0022
   pins certification to a version, so a drifted object flips its
   dependents to "definition changed since certification," disclosed in
   the answer (ADR 0021 — disclose, never gate).
3. **G / Funnel** — CLOSED by ADR 0039's error-to-contract lineage;
   the funnel and journey surfaces ship with counts and named reasons.

**Family F is now the product's wedge, not its gap** — the red-flag
sweep (ADR 0054) that finds contradictory definitions is what the
Estate X-Ray sells and what the Resolution Console resolves (ADR 0063).

## Traceability rule (structural, approved)

Every notebook's registry entry carries a `serves` field: the question
families it ultimately exists for. "Why does this notebook exist?" must
trace to Layer 0; a notebook serving no family is by definition a ghost.
(Mechanized by ADR 0042, the notebook contract.)

> **Built (1.18.0, ADR 0042):** `src/notebook_registry.py` carries
> `serves`; tests/test_notebook_contract.py enforces >=1 family per
> notebook; the per-notebook layer-4 projection is GENERATED at
> NOTEBOOK_MAP.md (family -> notebooks coverage table included).
