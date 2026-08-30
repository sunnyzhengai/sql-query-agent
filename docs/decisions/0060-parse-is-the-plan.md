# ADR 0060 — The parse is the plan: deterministic traversal, parser-only LLM

**Status:** ACCEPTED 2026-08-28 — designed in review session with
Sunny; all three open calls RULED same-day (§7): confirm every
parse; lexicon promotes by usage threshold with steward veto;
frontier parser for the pilot. Build is GATED on the corpus
experiment (§6) — no engine change ships before the measurement.
**EXPERIMENT CLOSED 2026-08-30** (queue-2 order): the full gating
measurement ran on the live shapes estate incl. Sunny's 15 walk
phrasings through both systems — PROPOSED dominates every metric
(routes 2/2 vs 1/2 · oracles 7/7 vs 5/7 · floors 0 vs 6 total ·
fails closed vs guessed census · all 15 phrasings composed vs 5
floors). Full record: internal/docs/PARSE_EXPERIMENT.md. The
planner already serves production via 0062's card-everywhere; the
gate this ADR set is formally satisfied with data.

## 1. The problem, measured

The 2026-08-28 re-walk on the shape estate produced the evidence:

- **Routing inconsistency:** one question class ("how is X
  different from Y" / "same as") took three distinct routes in one
  session — lineage-coarse + floor, compare-exemplar, retrieve +
  lineage with grain disclosure. The route is a dice roll because
  the LLM chooses it.
- **Template captions:** the commentary forces answers into a
  memorized skeleton ("1. Source Tables: 2. Calculation Logic:
  3. Subqueries:") regardless of the question, and narrates
  structure (counts, enumerations) no operation computed.
- **Mass floor collapse:** the honesty gate — correctly — floors
  the narrated structure (seven "invented numbers" in one answer
  were the ordinals 3–9 of a template list), leaving the user a
  raw dump. The gate is the healthiest organ involved; the disease
  is upstream.
- **The enumeration objection (fatal in principle):** question
  shapes are unbounded. Any pre-defined shape list loses to the
  first combination it didn't anticipate. Routing cannot be
  enumerated; it must be composed.

Every deterministic stage — lookups, graph queries, stamps, gate —
behaved correctly all day. Both failures live in the two seams the
LLM owns: route choice and caption authorship. This ADR removes
both seams.

## 2. The decision (proposed)

**The LLM is demoted two ranks: never the router, never the
author — only the parser.** It translates the user's sentence into
a small closed vocabulary; everything after the parse is
deterministic.

The pipeline:

```
NL question
  → PARSE (LLM): entities + relation primitives   [closed vocabulary]
  → CONFIRM (glass): the parse is displayed as the plan
  → TRAVERSE (code): anchors + primitives compose the KQL
  → DISPLAY (stamped): the map is the answer
```

### 2a. Entity grounding — tiered: exact, then semantic, then closed

*(AMENDED 2026-08-28 after Sunny's challenge: exact-only grounding
fails concept phrases; vector search joins as the candidate tier.)*

- **Tier 1 — exact:** a user token equal to a name/id in the
  universe (metrics, steps, tables, columns) grounds with
  certainty. Identifiers deserve exactness — fuzzy-matching an
  identifier silently answers about the wrong object.
- **Tier 2 — semantic candidates:** concept phrases ("the
  registry", "lab criteria", typos) go to vector/lexical search
  over names + business names + DESCRIPTIONS + captured phrase
  mappings (§2f). Output is ranked CANDIDATES, never a silent
  decision: the confirm step displays the chosen grounding and the
  runners-up. Safe precisely because of call 1 (confirm every
  parse): fuzzy may NOMINATE, only the user's click EXECUTES.
  Vector retrieval is deterministic given a fixed index; residual
  opacity is bounded by confirmation.
- **Tier 3 — fail closed** with the vocabulary offer (§2e).

The correction flywheel (§2f) feeds tier 2: every confirmed
correction becomes an indexed phrase mapping. DEPENDENCY: tier 2
is only as good as the description surface — see the RW-6 data
order (palette descriptions for every node type; the search op
already scopes descriptions, but the demo estate never authored
them for metrics/steps).

### 2b. The relation lexicon — small, closed, composable

The non-entity words are the question. They map to a **closed set
of relation primitives**, each bound to edge types or derived
computations:

| primitive (surface forms) | binds to |
|---|---|
| same / different / match / drift | compare(logic) — hash partition + diff |
| ways of / variants / versions | cluster node + logic-group partition |
| reads / uses / comes from / feeds | lineage edges (reads-grain, stamped) |
| flags / issues / wrong / conflicts | flag nodes (0054 sweep layer) |
| defines / criteria / logic of | record + decision sites + steps |
| who owns / who stewards | ownership edges (Sphere human shell) |
| grain / per-what / level | compare(grain) |

This is NOT question shapes returning by the back door: shapes
enumerate whole questions (unbounded); the lexicon enumerates
relation WORDS (small, closed). Combos compose — entities anchor,
primitives select edges and computations, the traversal is the
query plan. "Endless combos" are covered by composition, not
enumeration.

### 2c. Derived computations as virtual edges

Φ_AIVIA law: facts are never deduplicated; **sameness is always
derived**. DIFFERS is not stored in the graph — so pure traversal
cannot answer it. Two legs:

- **Materialized derived layer:** where the 0054 sweep has run,
  clusters, flags, and hash groups ARE nodes (provenance class
  `derived`, per 0059 G2). Traversal reaches them like any fact.
- **Virtual edges:** for pairs/aspects the sweep has not
  pre-judged, the primitive invokes the computation (compare,
  partition, diff) deterministically at traversal time. Same
  stamps, same honesty; computed on demand, never narrated.

### 2d. The parse is the plan — confirm before traverse

Plan-confirm-execute-display, applied for the first time to the
INTERPRETATION itself. The parse renders on glass before
execution:

> reading your question as: **compare(logic)** over
> {Active Diabetic Patients, Diabetes Registry (Composite)}

One click confirms; one click corrects. The correct behavior is
not a parser that never misreads — it is a parser whose
misreadings are **visible before execution and cost one click**.
(Sunny's slogan was the architecture all along; operations had the
loop, interpretation didn't.)

### 2e. Fail closed, honestly

A question the parser cannot map to the vocabulary is not routed
by guess. It fails closed with the honest refusal: here is the
vocabulary, here is what I can ask the graph (W10 posture). A
governed product may say "say it with these words"; it may not
improvise.

### 2f. The correction flywheel — the lexicon is grown, not frozen

Every parse correction is CAPTURED (0056 decision capture: the
correction is an assert-class event with provenance) and reused:
that user's phrase maps deterministically next time; corrections
that repeat across users harden into the estate lexicon. Canonical
born bottom-up, usage-weighted — the same flywheel as the rest of
the governance philosophy. The hand-authored lexicon of §2b is the
seed, not the ceiling.

### 2g. Captions shrink toward zero

If nothing is authored, there is no answer shape to pre-define.
The displayed, stamped map IS the answer; residual prose (if any)
stays under the existing gate unchanged. This dissolves the
template problem as a side effect rather than patching it.

## 3. What this is NOT

- **NOT NL2GQL.** The demoted Fabric agent composes queries with a
  model; we parse to a closed vocabulary and let code compose.
  Parse, don't generate. A model-composed query cannot be stamped;
  a parse can be confirmed.
- **NOT a relaxation of the gate.** The gate stays exactly as
  strict; this makes honesty achievable rather than dishonesty
  permissible.
- **NOT a removal of the LLM.** Translation to a closed vocabulary
  is the task LLMs are reliable at, and the confirm step bounds
  the damage of the residual error rate. A mini model with context
  and a repair loop beat a bigger brain without one, 13–8.

## 4. Why AIVIA can read intent (the three transferable mechanisms)

Intent-reading in practice is context + exposure + memory, not
magic:

1. **Context that accumulates** — the graph + 0056 capture know
   the asker (persona, ownership, history); the user's world
   disambiguates their words. Basic tier is quietly building this
   context with every captured decision.
2. **Exposure before action** — §2d; misreadings surface at
   confirm time, not verdict time.
3. **Memory of corrections** — §2f; an error corrected once never
   recurs for that user.

The model-intelligence gap is real but is the smallest of the four
ingredients, and the only one that cannot be engineered.

## 5. Consequences

- Same question → same parse → same traversal, every time.
  Route-consistency by construction.
- Honesty by construction for everything retrieved; stamps and
  gate cover the derived computations.
- **Display pressure rises:** deterministic traversal returns
  subgraphs; without the presentation layer (RW-1/RW-3, 0056
  post-capture batch, map-not-verdict) the answer is a neighborhood
  dump. This ADR DEPENDS on the presentation doctrine landing.
- The parser can be small; the frontier tier is not required for a
  closed-vocabulary translation with confirm.
- New failure mode to watch: lexicon gaps read as refusals. The
  flywheel (§2f) is the mitigation; refusal telemetry is the
  measure.

## 6. The experiment (gates the build)

Instrument: the shape corpus IS a question set with planted
oracles — plus Sunny's own paraphrases from the 2026-08-28 walk,
which are the valuable half (they broke the current router).

Protocol: run CURRENT (LLM-routed) vs PROPOSED (parse-traverse
prototype) over the full question set. Metrics:

1. **Route consistency** — identical parse/route across paraphrases
   of one intent (current baseline: 3 routes / 1 class).
2. **Oracle correctness** — answer grain matches the planted
   oracle (DIFFERS with E11.80; 10 members / 10 logics; grain
   CONFLICT).
3. **Floor-collapse rate** — answers reduced to "results above are
   the answer" (current baseline: 2 in ~8 questions).
4. **Detour load** — rows displayed vs rows the verdict cites.
5. **Refusal honesty** — unmappable questions fail closed with the
   vocabulary offer, zero guessed routes.

The 2026-08-28 walk scorecard is the current algorithm's baseline
measurement, already recorded in WALK_VERDICTS_SHAPES.md.

## 7. Open calls (Sunny's)

1. **Confirm cadence:** RULED by Sunny 2026-08-28 — **confirm
   every parse.** No auto-execute path; every question's
   interpretation renders on glass and waits for the click.
2. **Lexicon governance:** RULED by Sunny 2026-08-28 — **option B:
   usage-threshold automatic promotion with steward veto.** A
   personal mapping promotes to the estate lexicon once enough
   distinct users converge on it; stewards can veto or reverse.
   Bounded by call 1: every parse still confirms on glass, so a
   bad default is visible before execution. (Mirrors the
   never-gate-on-certification stance; stewards follow uses.)
3. **Parser model tier:** RULED by Sunny 2026-08-28 — **option A:
   frontier model for the pilot** to isolate architecture failures
   from parse failures (one variable at a time). If the
   architecture passes, swap in mini and measure the delta as its
   own step. Production tier is a later, separate decision
   informed by that measured delta.

## 8. Relations

- **0054:** the materialized derived layer traversal depends on.
- **0056:** decision capture is the correction flywheel's storage;
  confirm-parse is a new captured decision type.
- **0057 (Sphere):** "sameness is always derived" (§2c); the human
  shell supplies asker context (§4); map-not-verdict is the
  display contract (§5).
- **0059:** virtual-edge computations are provenance class
  `derived`; captured parse corrections are `asserted`.
- **Fabric agent demotion:** the anti-pattern this design refuses
  (§3).
