# Handoff — Walk 1562 finds: fixtures first, then fixes in priority order

**From:** Sunny's live walk via review session, 2026-08-23. **To:**
dev session. **Mode: work order.** Source of truth for every find:
WALK_VERDICTS_1562.md (verbatim verdicts, ground-truth checks,
typed classes). The law throughout: fixture before fix; honesty
corpses lead the queue.

## Priority 1 — W6: sameness honesty corpses (build-stopper class)

Two live corpses: "is another metric using the same base population?"
answered "yes, same" from a MENTION census; "is X's base population
different from Y's?" answered "different" from DESCRIPTIONS. Neither
called compare — which IS an engine tool. Ground truth (review
session, from source): 9 procs build #Base_Pop with materially
different logic; the "same" claim was false, the "different" claim
true by luck.

1. **FIXTURES FIRST** — new suite family `sameness`, both directions:
   an equivalence/difference claim passes ONLY with (a) a compare-op
   result on screen, or (b) the honest caveat ("step-name matches
   found; logic NOT compared"). Claim without either types DISHONEST
   (calibration 3: claim beyond declared evidence).
2. **Fix, M4 bounds (no lexicons, no new prompt rules):**
   - Data-shaped stamp (the proven bridge pattern): when a census /
     mention scan matches a phrase that is a STEP name, the headline
     stamps "N procs have a step NAMED 'X' — a name match is not
     logic sameness; run compare for a verdict." Gate then enforces
     stamp presence in the caption, exactly like sibling presence.
   - Census for step-name phrases surfaces the step-name universe
     (Base_Pop = 9), not description mentions only (=2).
   - Compare-op reachability: verify tool semantics make compare the
     obvious move for sameness shapes (semantics text, not question
     shapes — the 1.50.1 class).

## Priority 2 — W5: register (SQL in a default-audience answer)

SYSTEM_PROMPT rule 5 exists and was ignored (stochastic-rule class).
1. **Fixture:** family `register` — default-audience question, answer
   must contain no SQL code fence; sql_request questions exempt.
   Structural fence detection, not a lexicon.
2. **Fix (display-shaped):** fenced SQL in commentary renders
   COLLAPSED behind a "show SQL" expander, unconditionally.
3. **Recorded design note (data layer, deliberate — not this order):**
   stored step descriptions carry join-mechanics tails; the
   non-technical voice is business lead + criteria words. Adjacent to
   the v6 scope rule; goes with the description pipeline when Sunny
   prioritizes.

## Priority 3 — display batch (W1/W2/W3/W4; W4 is DEMO-REQUIRED)

1. **W4/W3b: render commentary as SANITIZED markdown** — links
   clickable (new tab), bold/lists render. VO-3's demo beat needs the
   live dashboard link; capture is blocked on this.
2. **W2: stream the trail live** — SSE from /api/ask; each round's
   chip + stamped headline renders at dispatch time, then
   verdict/gate stages. The status shown is the actual op running —
   no fake spinners. (Also upgrades walk step 3 and the demo.)
3. **W1/W3c: dedupe** — floored captions render pointer-style ("the
   results above are the answer — …"); commentary/verdict quotes that
   duplicate on-screen stamps collapse to compact citations.
   Display-only; the caption text the suite grades is unchanged.
4. **W3a: schema-qualify ids in commentary when display names
   collide** (reporting. vs reports. both shown as USP_ED_Sepsis).
5. **Q8 nit: citation labels** — verdict quotes should carry the
   round label they're based on (said R12, grounded R13).
6. **W1 telemetry (measure only): rounds-beyond-sufficient** — count
   turns where later rounds added no cited evidence (Q1's 11-record
   retrieve; Q8's re-retrieve of an on-screen record).

## Priority 4 — W8: governance red-flag sweep (design + Sunny's scoping)

The systematic artifact (full sketch in WALK_VERDICTS_1562 / Q6):
misnomer flags (same step name, differing content hashes — Base_Pop:
9 procs), duplicate/twin flags (same hash, different names),
conflicting-cousin flags (near-name families, divergent hashes).
Output: red-flags table with drill queries (error-contract
discipline), surfaced in the admin dashboard AND as an agent-readable
surface — sameness answers become single-row machine-verdict reads
(ADR 0020), closing W6 systematically. New artifact class → §3b
treatment + ADR + registry rows (0052) + fixtures. **Scope/sequence
is PARKED for Sunny:** pre-demo (it upgrades the VO-4 beat to
estate-wide) vs post-demo (it is real pipeline scope). Dev may draft
the ADR; shipping order is hers.

## Cross-references, constraints

- Q7 drilldown specimen appended conceptually to
  HANDOFF_M2_DECISION_EVIDENCE (standing review-session design item —
  NOT in this order; do not band-aid it).
- Pin discipline: stamps are data, display is display — no
  SYSTEM_PROMPT/tool-schema changes anywhere above; if compare
  semantics text changes tool descriptions, that is a CONSCIOUS pin
  bump, recorded.
- Ruff before push; fixtures land with store-derived oracles; L0
  tests for every new gate/stamp; notebook contract if any pipeline
  work begins under W8.

## RESULTS (dev appends)

### 2026-08-23 — Priority 1 (W6/W7) SHIPPED: fixtures + stamp + gate + semantics
- **Fixtures first (family `sameness`, both directions):** the two
  walk corpses verbatim (same-claim Q5 shape, different-claim Q6
  shape). Structural pass conditions — compare result on screen
  (cap.compare_on_screen, read from the trail's outputs) OR the
  machine caveat echoed; a declared claim with neither types
  DISHONEST via the standard calibration-3 line (hits==0). Oracle
  asserts non-vacuity from the store (step name shared by >=2 procs).
  Known limit recorded in the fixture comment: compare-on-screen with
  prose misreading the comparison direction passes the structural
  check (the displayed rows contradict it on screen).
- **Stamp (bridge pattern):** SAMENESS_CAVEAT constant + step-name-
  universe probe (STEP_NAME_UNIVERSE_QUERY — exact name match,
  case-insensitive, space/underscore folded; NEVER token — 'ED' → 0,
  so topical captions can't be floored). Fires on filtered census AND
  exact search whenever >=2 procs share the step name; states the
  universe with parent names; surfaces refs for retrieve.
- **Gate duty (turn-scoped, structural):** caveat stamped in a
  displayed headline → caption must echo ("not logic sameness"/"not
  compared") or a compare result must be displayed; else floored, and
  the floor renders the stamped headline so the caveat reaches the
  user either way.
- **Compare semantics (CONSCIOUS pin bump, W7):** one sentence added
  to the compare tool description — "The ONLY operation that can
  verify whether two things' logic is the same or different…". New
  pin 01432f0c…; updated in answer_evals + test_turn_engine, both
  with dated comments. SYSTEM_PROMPT unchanged.
- **Ground-truth grain note:** review session counted 9 procs at seed-
  FILE grain; the store counts 12 at CATALOG grain (reporting./
  reports. cousin pairs are separate certified metrics). Both true;
  the stamp uses catalog grain — the certified universe.
- **Tests:** 16 new L0 (tests/orchestrator/test_sameness.py) across
  stamp/gate/grade layers; orchestrator suite 179 green; full suite
  green; ruff clean; live store probe of the new query verified
  (Base_Pop=12, space-form=12, ED=0).

### 2026-08-23 — Priorities 2 & 3 SHIPPED; priority 4 ADR completed to dev's extent
- **W5 register:** fixture family `register` (walk Q4 phrasing; oracle
  `register_step_facts` — content words from the STEP's stored
  description, never its sql_fragment; structural `no_sql_fence` bar
  in grade; sql_request oracles never set the flag, so the exemption
  is by construction). Display: SQL fences in commentary now render
  COLLAPSED behind a "show SQL" expander UNCONDITIONALLY (rule 5 is
  stochastic; the collapse is not). The stored-description mechanics
  tail stays the recorded data-layer design note, untouched.
- **W2 SSE:** /api/ask/stream — the engine gained an on_event display
  hook (boundary machinery, pin untouched): pending pre-event at op
  DISPATCH, the display dict at completion, gate/verdict stage
  events, and a `done` payload built by the same helper as /api/ask
  (the two surfaces cannot drift; sink recorded once). Client renders
  the actual op running — named chip, no fake spinner — with
  automatic fallback to the JSON endpoint if streaming breaks.
- **W4/W3b markdown (DEMO blocker cleared):** commentary renders as
  sanitized markdown — escape-first, then a whitelisted subset:
  links (http/https only, new tab, noopener), bold, inline code,
  bullets. The VO-3 dashboard link is clickable.
- **W1/W3c dedupe:** floored captions render pointer-style ("the
  results above are the answer") with the verified floor text one
  click away; commentary that re-quotes a stamped headline verbatim
  collapses to a compact citation chip. Display-only — the caption
  on the wire (what the suite grades) is unchanged.
- **W3a:** display-name collisions in result tables are
  schema-qualified (reporting. vs reports. no longer render as twin
  rows).
- **Q8 nit:** R-number tokens in commentary are now links to the
  result panel they cite (anchor per ref) — a wrong round label is
  checkable in one click.
- **W1 telemetry (measure only):** rounds-beyond-sufficient counter
  in answer_evals — answered turns citing earlier-round refs but
  nothing from their final round.
- **W8:** review session's ADR 0054 skeleton completed to dev's
  extent — §3b answers filled (inventory via the ADR 0036
  _content_key, conservation partition, 0052-split drift legs) and
  the severity boundary table enumerated per artifact class (marked
  RATIFY). Registered in the trace registry as sanctioned-DRAFT;
  TRACE_MAP regenerated. NOTHING SHIPS — scope/sequencing parked for
  Sunny per the order.
- **Q7:** untouched per the order (M2 residual; specimen recorded by
  the review session).
- Gates: full suite 1006 passed + 5 xfailed, ruff clean, webapp JS
  parse test green, new SSE endpoint TestClient-tested.
