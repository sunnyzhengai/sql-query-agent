# Handoff — GOAL: the homegrown agent beats the Fabric agent, proven by Rematch Round 4

**From:** Sunny via review session, 2026-08-20. **To:** dev session.
**Mode: autonomous.** This is a GOAL handoff, not a work order — design
your own path. Sunny is away; the constitution governs, and anything
that is hers to rule gets PARKED, never decided.

## The goal

The homegrown agent (orchestrator + web UI) demonstrably outperforms
the Fabric Data Agent — the REFRESHED Fabric agent, so the win is
against its best configuration, not a stale one — proven by a recorded
Rematch Round 4 scorecard.

## Success criteria (all measurable, all oracle-scored)

1. **Conversation suite**: answer rate ≥ 90% per family across the
   paraphrase spread; **honesty 100% — any dishonest turn is a
   build-stopper, not a metric**; bridge and drilldown families pass.
2. **Rematch Round 4**: the same fixture families (census, definition,
   bridge, drilldown, anaphora, topical count + the historical rematch
   count-oracle questions) run once against BOTH surfaces, scored by
   the same oracles (required facts, exact counts, no fabrication,
   honest refusal). Homegrown ≥ Fabric on every family; scorecard
   recorded beside rounds 1–3.
3. **Guarantees intact**: replay determinism (spec:E2), all spec/CI
   gates green, stamped headlines and caption gate unchanged in force.
4. **Latency**: homegrown p50 stays under 3s end-to-end (the historical
   0.71s vs 19–47s advantage must not be spent).

## Pre-authorized (no need to wait for Sunny)

- **The model-tier experiment first**: point the ask-path LLM edges at
  the strongest available Azure OpenAI deployment; rerun the suite;
  record the per-family delta before any further prompt/harness
  iteration. Document the resulting minimum ask-path model tier as a
  product prerequisite if it clears.
- Suite iteration: new fixtures (every manual failure becomes a
  fixture), grader refinement, loop/planner/caption work within the
  ADR 0050 bounds.
- **The Fabric refresh** (data-shaped, instruction-light — the ADR 0020
  doctrine): metric_logic gains decision-site summary / step_count /
  table_count / twin-verdict columns (PHI gate applies);
  stepCount/tableCount as LPG Metric node properties (the open 0030
  item); semantic_search stored function as the schema-selected
  Eventhouse surface; instructions SHRINK to the verified resolve-first
  flow + principles. No casebook.
- Fabric-side evaluation ONLY via the scripted rematch protocol —
  fixed questions, run once, scored, recorded. Never casual chat.

## Constraints (the constitution, unchanged)

- All spec axioms and ADR rulings stand; cite spec:IDs in any design
  debate. No component violating spec:E2 enters a retrieval seat.
- Writes always confirm (ADR 0050); read-only auto-continue stays
  bounded and dispatch-enforced.
- Templates-as-a-closed-menu remains banned (D was dropped; the 0034
  lesson). Priors may be PROPOSED as a parked item, not shipped.
- Native-parser law, notebook contract, capability/extraction
  registries: all in force. Decisions recorded the moment made
  (ADR or handoff) — conversation-held decisions don't exist.

## PARKED for Sunny (record, don't decide)

- Any amendment to a Sunny ruling (D revival, autonomy-bound changes,
  gate-threshold changes).
- Any Marketplace-facing claim derived from Round 4 results.
- Anything touching governance writes, personal-layer data, or the
  access-control gate (ADR 0038).
- Recurring LLM spend beyond suite/rematch runs at the current scale.

## Reporting (so Sunny returns to evidence, not narrative)

- Every suite run's scorecard persisted (the answer_evals pattern);
  a running RESULTS section appended to THIS file per iteration:
  date, change, per-family delta, honesty status.
- Round 4 scorecard as its own file beside rounds 1–3.
- A PARKED list at the bottom of this file, one line per item.
- If honesty drops below 100% at any point: stop optimizing, fix,
  record the corpse as a fixture, then resume.

---

## RESULTS (running log, dev session)

### 2026-08-20 ~21:10 — Baseline: full suite on gpt-4o-mini (ask-path default), 1.43.0
| family | answer | honesty | n |
|---|---|---|---|
| census | 1.00 | 1.00 | 6 |
| definition | 1.00 | 1.00 | 6 |
| topical_count | 0.83 | 1.00 | 6 |
| drilldown | 0.33 | **0.83** | 6 |
| bridge | 0.00 | **0.67** | 6 |
| anaphora | 0.00 | 1.00 | 6 |

Read: the three "reading" families hold at scale; under paraphrase
pressure the mini model went DISHONEST 2/6 on bridge and 1/6 on
drilldown — over-claiming exactly where composition is required. The
build-stopper is active; no optimization proceeds on mini. The
model-tier experiment's gpt-4o leg auto-started (identical suite,
LLM_MODEL override only — zero harness/prompt changes between the
runs).

### 2026-08-20 ~21:5x — Fabric refresh shipped (1.44.0, CI green) + Round-4 runner built
- output_metric_logic gains decision_summary (PHI-redacted, honest
  cap) / table_count / twin_verdict; 400 consumes
  graph_decision_sites (contract-declared — the consumer police
  caught the undeclared read). Drill-down/sameness/count questions
  are now single-row reads on the Data Agent surface (ADR 0020).
- LPG export: stepCount/tableCount as Metric node properties — the
  open 0030 item CLOSED; count questions are property reads.
- Data Agent instructions updated to read the new surfaces (net
  growth minimal; no casebook).
- devtools/rematch_round4.py: both-surface scripted runner, same
  oracles as the suite + the historical count-oracle family
  (step_count derived live), latency p50, scorecard writer. Fabric
  side runs via the MCP adapter headlessly.

## PARKED (for Sunny)

- Round-4 EXECUTION is blocked on tenant work only Sunny can do:
  publish env with the 1.44.0 wheel, rerun 400→800, re-Load the
  Graph Model, republish the Data Agent with the updated
  instructions. The runner refuses stale surfaces by protocol.
- Any Marketplace-facing claim from Round-4 results (constitution).
- Minimum ask-path model tier: will be RECORDED as a prerequisite
  doc once the experiment clears — the tier CHOICE (which deployment
  customers must provision) is Sunny's pricing/product call to
  ratify.

### 2026-08-20 ~22:1x — Model-tier experiment COMPLETE: hypothesis REFUTED
Identical suite, LLM_MODEL=gpt-4o on all ask-path edges, zero other changes.

| family | mini (ans/hon) | gpt-4o (ans/hon) | delta |
|---|---|---|---|
| census | 1.00 / 1.00 | 1.00 / 1.00 | — |
| definition | 1.00 / 1.00 | 0.67 / 1.00 | WORSE answer |
| bridge | 0.00 / 0.67 | 0.00 / 0.50 | worse honesty |
| drilldown | 0.33 / 0.83 | 0.33 / 1.00 | better honesty, same answer |
| topical_count | 0.83 / 1.00 | 0.67 / 1.00 | worse |
| anaphora | 0.00 / 1.00 | 0.17 / 0.83 | mixed |

Findings, stated plainly:
1. Scale did NOT fix composition; the stronger model trades humility
   for confidence — bridge went 3/6 DISHONEST on 4o (confident
   synthesis without the required facts), the exact failure the typed
   verdict exists to catch.
2. Two grader-model interactions identified (recorded, to fix):
   the definition oracle counts VERBATIM word overlap and 4o
   paraphrases more fluently — some "misses" may be style; and the
   bridge grade demands declared_answered, but a correct bridge
   honestly declares answered=false while naming the siblings.
3. Consequence: NO minimum-tier prerequisite is documented — there is
   no evidence a higher tier helps this harness. Ask-path default
   stays gpt-4o-mini. The bottleneck is harness/oracle-shaped;
   iteration resumes within ADR 0050 bounds, now with measured
   justification (the "stop sharpening prompts for mini" directive is
   answered by the experiment it asked for: sharpening was and
   remains the right lever).

### 2026-08-20 ~22:4x — Iteration 3 (1.45.0) full suite + iteration 4 (1.46.0) shipped
Iter-3 scorecard (mini, n=6): census 1.00/1.00 · definition 0.83/1.00 ·
topical 1.00/1.00 · anaphora 0.00→0.67 (re-point + display fix) ·
bridge 0.00 (hon 0.67) · drilldown 0.33 (hon 1.00). Transcript findings:
(a) ALL four drilldown "misses" carried the required facts — graded
down only for humble answered=false → grader calibration 2: facts
score, the verdict only polices honesty; (b) bridge material was on
screen but the captioner synthesized over it → the containment set is
now STAMPED in the search headline ("Nothing is NAMED 'X' exactly;
closest by name: ..."), and retrieve headlines stamp the step pointer.
1.46.0 shipped with both + tests; iteration-4 full suite running.
