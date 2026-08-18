# The Question Map — first principles, top-down

Derived 2026-08-18 (review session + Sunny; Layer 0 approved by Sunny).
The product exists to answer user questions about metadata. Everything
below derives from those questions — and the built system, which grew
bottom-up, passes this top-down audit with three named gaps.

## The governing model (July doctrine, restated)

1. **Shape classes shape the storage** — questions are unbounded, answer
   shapes are few and stable (six). Storage anticipates classes, never
   individual questions.
2. **Questions are handled at runtime** as LLM-planned compositions of
   deterministic primitives (the ADR 0037 algebra) over that storage —
   plan, confirm, execute; the answer is a caption (ADR 0036).
   Shape-specific tools are banned by CI (methodology tests).
3. **Precomputation is only verifiable cache** of hot algebra results
   (e.g. the uses_table closure), never per-question answer tables.

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
| F | aligned diff of decompositions | step-grain fragments (data exists); needs a DIFF KERNEL primitive | — | GAP (gap 1) |
| G | funnel (counts → reasons) | fallout rows + funnel view | in flight | IN FLIGHT (gap 3) |

## The three honest gaps

1. **F / Comparison** — the founding question is the least-served shape.
   Direction (doctrine-compliant): not a compare_* tool (banned) but a
   generic diff KERNEL primitive composing with search/retrieve.
   → ../internal/HANDOFF_COMPARISON_SHAPE.md
2. **E / Freshness** — "when did this logic last change?" is derivable
   (extraction hashes) but reaches no card.
   → ../internal/HANDOFF_FRESHNESS_TO_CARDS.md
3. **G / Funnel** — confirmed load-bearing by derivation.
   → ../internal/HANDOFF_FUNNEL_AND_FALLOUT.md

## Traceability rule (structural, approved)

Every notebook's registry entry carries a `serves` field: the question
families it ultimately exists for. "Why does this notebook exist?" must
trace to Layer 0; a notebook serving no family is by definition a ghost.
(Folded into ../internal/HANDOFF_NOTEBOOK_CONTRACT.md.)

> **Built (1.18.0, ADR 0042):** `src/notebook_registry.py` carries
> `serves`; tests/test_notebook_contract.py enforces >=1 family per
> notebook; the per-notebook layer-4 projection is GENERATED at
> NOTEBOOK_MAP.md (family -> notebooks coverage table included).
