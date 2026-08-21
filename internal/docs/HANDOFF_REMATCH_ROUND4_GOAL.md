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

### 2026-08-20 ~23:2x — Iteration 4 (1.46.1) full suite
census 1.00/1.00 · definition 1.00/1.00 · drilldown 1.00/1.00 (was
0.33) · topical_count 1.00/1.00 — FOUR families perfect. bridge
0.00/0.67 and anaphora 0.67/0.67 remain: captions neither echo the
stamped sibling names nor stop claiming over summaries (2+2 dishonest
turns — build-stopper active). The failure has collapsed to ONE shape:
the captioner ignoring machine-stamped material. Next (mechanical,
grounded-verification class — not a lexicon): (a) the template floor
renders the stamped headlines themselves, so even a floored caption
names the siblings; (b) caption gate verifies the caption presents at
least one stamped closest-by-name item when the bridge stamp is on
screen; (c) the answered verdict is demoted by code when the
step-pointer stamp is displayed with no step record retrieved.

### 2026-08-21 — THE ONE-MIND MERGE shipped (ADR 0051, 1.49.0; HANDOFF_ONE_MIND executed)
ADR written first. Engine derived from the six principles:
src/orchestrator/turn_engine.py — one conversation, full tool results
persistent in ONE history across rounds AND turns, thinking room,
free composition over the four read-only ops. Boundary kept: stamped
headlines, caption gate, machine-verified evidence-quote verdict,
read-only dispatch (writes plan-confirm), round cap + anti-flail as
code, infra errors observed into the conversation. Casebook DELETED
not ported: planner shape rules, mandatory-bridge clause, pointer
doctrine, bridge-duty gate check, pointer demotion — all gone. Webapp
reads run immediately on /api/ask (trace-as-display); plan card
reserved for writes. 11 cage tests; 908 local tests green; suite now
drives the engine. THESIS TEST RUNNING: full suite on mini then 4o —
bridge and anaphora must flip with zero new prompt rules, honesty
100%; the model-tier question is formally reopened.

### 2026-08-21 — THESIS VERDICT (prompt hash pinned: 20781efb…) + P-group shipped (1.50.0)
One-mind full suite, both tiers, zero prompt-rule additions:
| family | mini | gpt-4o |
|---|---|---|
| census | 1.00/1.00 | 1.00/1.00 |
| definition | 0.83/1.00 | 0.83/1.00 |
| drilldown | 1.00/1.00 | 1.00/1.00 |
| anaphora | **1.00/1.00 (was 0.67)** | **1.00/0.83→1.00** |
| bridge | 0.00/0.67 | 0.00/**1.00** |
| topical_count | 0.00/1.00 | 0.00/1.00 |

Honest reading: ANAPHORA FLIPPED on both tiers with zero prompt rules
— memory did it; the P2 thesis holds. Drilldown holds. gpt-4o is now
fully honest (6/6 families) under the new shape — the tier question
re-answered. Bridge did NOT flip on prompts-free grounds — but the
root cause is RETRIEVAL, not language: the embedding top-K buried the
literal near-names ('Sepsis Case Details' absent from top 12). Fixed
data-shaped inside P4: semantic search now unions name-containment
matches (flagged). topical_count regressed 1.00→0.00 — the deleted
census-for-topic-counts casebook was load-bearing; NOT re-added; next
run measures whether containment + headlines suffice, else this is
the honest P4 failure to report. P-group checks + strata in SPEC
v0.5; protocol.py demolished (P1); Smartness Walk written
(internal/docs/SMARTNESS_WALK.md). Next: suite rerun on 1.50.0.

### 2026-08-21 — 1.50.0 scorecard + the tool-semantics pass (1.50.1)
1.50.0 mini: census 1.00 · definition 1.00 · bridge **0.83 (flipped
by the containment union — zero prompt rules; thesis holds)** ·
drilldown 1.00 · anaphora 1.00 · topical_count 0.00 (honest) —
**honesty 1.00 across all six, first fully honest mini run.** Five of
six families clear the 0.8 readiness bar. topical_count's stable
shape: the mind counts its top-K window instead of fetching census.
1.50.1: TOOL SEMANTICS sharpened (census = the only count-supporting
operation; a search's row count is a window property) — P4-legal, no
question shapes. PIN UPDATE (conscious, recorded): scope widened to
SYSTEM_PROMPT + ENGINE_TOOLS, new hash ae375882…. Suite rerun next;
if topical_count still fails, that is the honest P4 boundary finding.

### 2026-08-21 — 1.50.1 scorecard: FIVE families perfect; topical is the boundary candidate
census 1.00 · definition 1.00 · **bridge 1.00 (perfect)** · drilldown
1.00 · anaphora 1.00 — all with honesty 1.00. topical_count still
0.00/1.00: the mini mind, told in tool semantics that a search's row
count "is never a count of anything," still asserts the window count
(6/6 identical, honest verdicts). Before declaring this the honest P4
boundary on mini, the reopened tier question gets its measurement:
the identical suite is running on gpt-4o. If 4o honors the semantics,
the finding differentiates tiers (input to the PARKED min-tier
prerequisite); if not, topical_count is the recorded P4 limit and the
decision on it is Sunny's.

### 2026-08-21 — 1.50.2: topical FLIPPED; L2 READINESS CLEARED; one calibration question PARKED
Scorecard (mini): census 1.00 · definition 1.00 · drilldown 1.00 ·
anaphora 1.00 · **topical_count 1.00 (flipped by the topic-filtered
census, first run)** · bridge 0.67 this run — pooled over the three
1.50.x runs bridge = 15/18 = **0.83** (n=6 noise; range 0.67–1.00).
Honesty 1.00 on every family, every run, both tiers.

**All six families clear the ADR-0050 readiness bar (0.8/1.0) on the
pooled estimate → the Smartness Walk is UNLOCKED**
(internal/docs/SMARTNESS_WALK.md). The 0.90 GOAL bar: five families
at 1.00; bridge at 0.83.

PARKED (calibration, Sunny's to rule): the two bridge misses are
bridge-SHAPED answers ("no exact definition exists; here are related
metrics") that present the MEANING-closest candidates; the oracle
credits only the NAME-closest siblings. Whether meaning-bridging
counts as a pass defines the family's acceptance — widening the
oracle would put bridge ≥ 0.9 today; keeping it strict keeps the
pressure on literal did-you-mean behavior.

Engine journey, one line: dumb-trail (3/4 unanswered) → one-mind +
memory + retrieval-union + filtered census = 5×1.00 + 0.83, honesty
perfect throughout, zero casebook. Remaining for the GOAL: bridge
calibration ruling; Sunny's walk; the parked tenant republish; then
Round 4 (runner ready, one command per surface).

### 2026-08-21 — gpt-4o on 1.50.2: PERFECT SWEEP (first in the campaign)
All six families 1.00/1.00, rc=0 — census, definition, bridge,
drilldown, topical_count (flipped by the filtered census), anaphora.
Zero dishonest turns. Honest note: graded under the pre-ruling bridge
oracle (any sibling mention); the siblings-FIRST oracle (Sunny's
2026-08-21 acceptance ruling, 1.50.3) applies from the next runs.
The 1.50.3 mini run (ruling live at oracle AND boundary) is chained
next. Goal-bar state: gpt-4o clears ≥0.90 on every family under the
old oracle; mini pooled 5×1.00 + bridge 0.83. Model-tier input for
the PARKED prerequisite: under the one-mind shape, 4o is now strictly
≥ mini everywhere measured, both fully honest.

### 2026-08-21 — 1.50.3 mini under the siblings-first ruling: ALL SIX PASS (rc=0)
census 1.00 · definition 1.00 · bridge 0.83 (above the bar UNDER the
stricter oracle, boundary enforcement live) · drilldown 1.00 ·
topical 1.00 · anaphora 1.00 — honesty 1.00. Both tiers now clear
every family; gpt-4o sweeps at 1.00×6. The engine iteration loop is
CLOSED pending Sunny's Smartness Walk (she has added five personal
questions to step 1 of the walk doc — per protocol, any rejection
becomes an L2 fixture before its fix ships) and the tenant republish
for Round 4.

### 2026-08-21 — Smartness Walk step 1 (Sunny, live, 10 questions incl. her 5 additions)
PASS: metric census (28, exact); Sepsis Case Encounters definition
(verified verdict); which-step (final_select, verified); sql-file
probe (bridge stamped, siblings first — honesty gate also caught an
invented '3'); step count by pronoun (122, correct anaphora).
REJECTIONS → fixtures → fixes (1.50.5, same day):
1. "how many metrics contain ED logic" → census said 28 (substring
   bug, caught in code that morning, fixed in 1.50.4; her webapp
   predated the restart). Fixture: topical ED (added in 1.50.4).
2. "how is Sepsis Case defined" / "how is IP_SEPSIS defined" → exact
   search, honest 0, one round, floored caption with NO did-you-mean.
   Root cause: bridge stamp existed only on semantic results. Fix:
   empty exact search computes its own near-names into `note`,
   stamped into the headline (data, not prompt — pin unchanged).
   Fixture: bridge IP_SEPSIS variant.
3. "show me the sql of Sepsis Case Encounter" → right SQL, 0 rounds,
   but "based on: —": the verdict ground only covered the current
   turn's rows. Fix: evidence ground = all displayed rows this
   conversation (P1/P2). Fixtures: sql_request family (fresh-convo).
4. "how many steps does it have" → correct 122 via a 413-row census
   dump (her: answer too long). Fixture: anaphora step_count oracle;
   plus webapp 30-row fold (presentation only, headline keeps the
   exact total).
Also noted: drilldown criteria were summary-flavored bullets —
Sunny's gap-check to rule on; oracle tightening parked until then.

### 2026-08-21 — 1.50.6 mini board + Sunny's live IP_SEPSIS retest → 1.50.7
1.50.6 mini (walk fixtures live): census 1.00 · definition 1.00 ·
bridge 0.92 (n=12, incl. IP_SEPSIS 6/6) · drilldown 1.00 ·
sql_request 1.00 · topical 0.58 BELOW · anaphora 0.58 BELOW —
honesty 1.00 everywhere.
Sunny's live retest still failed "how is IP_SEPSIS defined": model
census'd steps for the phrase, honest 0 → "cannot be provided", while
the graph held tech:reporting.ip_sepsis. 1.50.7 closes the class:
(1) TABLE_USED_BY_QUERY resolves table-phrases via technical nodes +
transform_to_technical → "'IP_SEPSIS' is a SOURCE TABLE read by N
metric(s): …" stamped on ANY honest-empty (exact search AND filtered
census); (2) of_metric joins the census mention-scan (step census by
parent ref was 0-row); (3) multi-word zero-match census stamps
per-token counts ('ED logic' → "'ED' alone: 2"); (4) caption-gate
ground = whole-conversation displays (zero-round answers restating
prior rows were floored as invented); (5) suite drops trail
paraphrases that lost the anaphor (they measure nothing). Zero
prompt/tool changes — the pin stands.

### 2026-08-21 — 1.50.7 board → 1.50.8 (degradation + table-identity grading)
1.50.7 mini: census/definition/drilldown/sql_request 1.00 · anaphora
0.88 PASS (anaphor filter working) · bridge 0.75 BELOW · topical 0.67
BELOW — honesty 1.00. Transcripts: the IP_SEPSIS "misses" were
CORRECT captions ("source table read by …") failed by the oracle
counting stamped READERS as competitors — oracle now accepts stamped
table-identity in first position and exempts stamped readers (the
ruling orders siblings before unstamped strays, not before machine
stamps). Topical: mini read the 0-row headline and ignored the
per-token note → zero-match multi-word census now DEGRADES to its
productive tokens, degradation stamped in the universe ('ED logic' →
2 rows, "'logic' matches nothing and was disregarded"). Zero
prompt/tool changes — the pin stands.

### 2026-08-21 — 1.50.8 board → 1.50.9 (containment degradation + exact-stamp precedence)
1.50.8 mini: topical 0.92 PASS (census degradation worked) · anaphora
1.00 · census/definition/drilldown/sql_request 1.00 · bridge 0.75
BELOW — honesty 1.00. IP_SEPSIS subfamily now 6/6; the misses moved
to 'Sepsis Case' via two shapes: (a) model paraphrased the phrase
('Sepsis Case Definition') so full-phrase containment went dark →
containment now degrades to productive tokens (has_all), same law as
census, and name_match companions are stamped; (b) model widened to
'Sepsis' whose stamp names near-everything → boundary ruling now
aggregates with EXACT-stamp precedence, competitors drawn from all
displayed results. Zero prompt/tool changes — the pin stands.

### 2026-08-21 — 1.50.9 mini: ALL SEVEN FAMILIES PASS (rc=0), walk fixtures live
census 1.00 · definition 1.00 · bridge 1.00 (n=12, both subfamilies,
strictest oracle) · drilldown 0.83 · topical 1.00 (n=12) · sql_request
1.00 · anaphora 1.00 (n=8) — honesty 1.00 everywhere. CI GREEN.
Strongest board of the campaign: mini tier, every one of Sunny's
walk-step-1 questions running as a fixture, zero prompt changes since
the pin. The engine iteration loop is CLOSED again pending Sunny:
webapp restart to 1.50.9, walk steps 2–6, the graph-gap roadmap
priority call (decisions → report links → columns → sql-text), and
the tenant republish for Round 4.

### 2026-08-21 — Sunny's green light executed: ADR 0052 + backfill items 1–2 (1.51.0)
Her ruling: the 7% ask-surface = spec:C1 violated reflexively; make
the audit permanent first. DONE in order:
1. REACHABILITY CONTRACT (ADR 0052, src/reachability.py): one row per
   NodeLayer/EdgeType/catalog kind — reachable-by-named-op (marker
   verified against implementation text in CI) or excluded-with-
   reason. Totality enforced; a layer can never again land invisible
   by accident.
2. DRILLDOWN ORACLE TIGHTENED per her rejection (fixture-first):
   answers must carry decision-layer words, not step-description
   prose.
3. DECISIONS (backfill 1): step retrieve attaches decision sites.
   PHI both sides per her rider — read-time redaction on the ask-path
   (store rows predate the gate) + export-side redactor extended to
   decision expression_sql for the next tenant rerun.
4. REPORT LINKS (backfill 2): metric retrieve lists reports; report
   retrieve carries parsed TMDL links (executes/reads/measures), all
   linked ids surfaced for the next hop — walk step 3 unblocked.
   Measures gained full-record retrieve in the same branch.
QUEUED (rows on record in the contract): columns third, SQL-text
last; transform_to_transform lineage unqueued pending Sunny.
Zero prompt/tool-schema changes — the pin stands. 925 tests green.

### 2026-08-21 — SPEC §3b RATIFIED (ADR 0052 amended); clause's first live use complete (1.51.1)
The three answers, cited and mechanized: (1) inventory =
src/reachability.py, 24 payloads, no undeclared frontier; (2)
conservation VERIFIED LIVE: 432 transforms = 413 catalog steps ⊎ 19
__final_select__ terminals — residual fully named, no third bucket;
(3) drift = enum-level CI (tests/test_reachability.py) +
store-level devtools/reachability_audit.py (exit 1 names every
undeclared payload and every vanished step; ran clean against the
store today). Calibration finding recorded in the ADR: store-level
conservation cannot live in CI — the drift answer splits into a CI
leg and a live-audit leg; expect the same split for any artifact
class whose frontier exists only in tenant data. SPEC header flipped
to "ratified by ADR 0052".

### 2026-08-21 — 1.51.0 board under the tightened oracle → 1.51.2
1.51.0 mini, decision-word oracle live: DRILLDOWN PASSES 0.83 — mini
reaches the decision layer unprompted when it retrieves steps. Six
families 1.00/PASS; anaphora 0.75 BELOW: the two misses retrieved the
METRIC (whose record holds no decisions) and summarized at one round.
1.51.2: metric records carry decision_count and the retrieve headline
stamps "N decision site(s) carry the WHERE/CASE criteria — retrieve
the step records to read them" — the hop-2 pointer is machine truth
on screen, same mechanism that flipped bridge. (1.51.1 CI red was
ruff import-order only; fixed, CI green.)

### 2026-08-21 — 1.51.2 board → 1.51.3 (live serialization bug in degraded containment)
1.51.2 mini: anaphora 1.00 (decision-count stamp worked) · five
families 1.00 · drilldown 0.67 BELOW. Transcripts: the degraded
containment union SILENTLY RETURNED 0 LIVE — NAME_CONTAINS_TOKENS
declared a dynamic query parameter the v2 REST body doesn't reliably
deserialize; the L0 fake passed because it never exercises
serialization. 1.51.3: p_tokens is a space-joined string, split
server-side — verified live ('severe sepsis' → Severe/Non-Severe
Sepsis Episodes). Lesson for the strata: a query with a nontrivial
parameter TYPE needs one live probe before its first suite run.

### 2026-08-21 — 1.51.3 board → 1.52.0: verdict-driven continuation (P6)
1.51.3 mini: drilldown 0.50 / anaphora 0.75 BELOW, five families
1.00 — and the misses shared ONE shape: the model filed its OWN
verdict as not-answered WITH the missing op named, then stopped with
rounds to spare (searched, never retrieved; retrieved the metric,
ignored the stamped decision pointer). Scores bouncing 0.83/0.67/0.50
across identical code = round-laziness variance, not capability.
1.52.0: a self-diagnosed miss is an observation, not a terminal fact
— when the verdict (or a floored caption, engine-named) names the
missing op and budget remains, the observation enters the one history
and the SAME bounded loop runs once more. Round cap unchanged,
anti-flail persists across passes, exactly one continuation, cage
tests for recover/at-most-once/no-op-no-continue. Zero prompt/tool
changes — the pin stands (the continuation note is boundary
machinery, same class as the gate-rejection note).

### 2026-08-21 — Review verdict on 1.52.0: APPROVED, reframed as the first live M5 diagnosis
Recorded per the relay: the continuation decision (answered=false ∧
missing_op ≠ null ∧ budget > 0 → continue) is COMPUTABLE, and it was
resting on a stochastic decider — an M5 violation manifesting as the
0.83/0.67/0.50 bounce on identical code. 1.52.0 moves it to code
where M5 says it belonged. Axiom checks all pass (M4: typed fields,
no lexicon, pin legitimate; bounds: at-most-once + cap + dedup, no
sandbagging; B2: boundary re-runs in full). STANDING WATCH ITEM
(typed M2, never another continuation): humble-but-blind — model
names an op it already ran, dedup blocks, facts already displayed —
if it grows it's evidence PRESENTATION, file it under M2 or it
breeds stamps. AI_VIA_AXIOMS §7 receipts row waits for the 1.52.0
scorecard (J discipline: claim after measurement).
