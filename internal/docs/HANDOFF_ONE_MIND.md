# Handoff — ONE MIND: merge the agent loop and the honesty floor

**From:** Sunny via review session, 2026-08-21. **To:** dev session.
**Verdict (Sunny):** merge approved. The webapp's turn engine is rebuilt
from first principles; `agent.py`'s loop and `protocol.py`'s honesty
machinery are the PARTS BIN, not the blueprint.

## Read this first: the design authority

The design authority for this work is the SIX PRINCIPLES below — not
the current codebase. Explicit instruction from Sunny: do NOT start
from protocol.py and amend until it sort of works. Derive the turn
engine from the principles; reuse existing code where it genuinely
satisfies a principle; where existing code conflicts with a principle,
**the principle wins and the code changes**. If a principle cannot be
met, PARK it with the reason — do not half-implement it silently.

Diagnosis this rests on (verified in code, 2026-08-21): the webapp
runs three amnesiac minds — planner, goal-check, captioner — each a
forced single-shot JSON call at temperature 0; results NEVER enter
`session.history` (only a 1,500-char plan stub and the caption do);
each call sees a per-call display blob compacted to a 20k budget
(40 rows × 400 chars degrading to 5 × 160) and then discarded. The
model-tier experiment failed because a stronger amnesiac is still an
amnesiac. Meanwhile `agent.py` (ADR 0035, live on the MCP surface) is
already the other architecture: one conversation, full tool results in
history, invariants-only prompt. The two halves have never met.

## The six principles (normative — each is an acceptance property)

**P1 — One mind.** A single LLM conversation makes every decision in a
turn: what to do, whether results suffice, what the answer is. No
separate planner/goal-check/captioner minds. The
plan→execute→judge→caption pipeline of protocol.py is retired as the
conversation shape.

**P2 — Full evidence, persistent.** Complete tool results enter the
SAME conversation history and persist across rounds and turns. Context
management degrades gracefully as the window fills — oldest/largest
results compact first (to their stamped headline + totals, which are
never dropped); recent results stay whole. Budget sized to the model's
actual window, not a fixed 20k per-call amputation. The next question
in a conversation sees what the previous one surfaced — anaphora is a
property of memory, not a prompt rule.

**P3 — Thinking room.** The model may reason between tool calls. No
forced immediate JSON emission for decisions that require composition
(forced tool_choice is legal only where the output is genuinely a
form-fill, e.g. the final typed verdict). Composition happens in
reasoning; amputating reasoning amputates composition.

**P4 — Free composition over primitive tools.** The deterministic ops
(search, census, retrieve, compare, steps, report links, ...) are the
tool set; the model composes them freely. NO question-family control
flow anywhere — not in prompts, not in gates, not in stamps. The
system prompt contains invariants and tool semantics ONLY. The three
casebook prompts (PLANNER_PROMPT's shape rules, CAPTION_PROMPT's
mandatory-bridge clause, GOAL_CHECK_PROMPT's pointer doctrine) are
deleted, not ported: a mind that holds full evidence bridges and
follows pointers natively — the suite MEASURES whether that's true
instead of the prompt instructing it.

**P5 — Honesty at the boundary, not in the interior.** Everything
protocol.py got right survives, relocated to the boundary:
- every displayed result panel carries its code-stamped headline;
- the FINAL answer passes the caption gate and emits the typed verdict
  with machine-verified evidence_quote (this mechanism is good — keep);
- tools run behind the dispatch whitelist and the read-guarantee
  (only surfaced/user-named ids);
- writes ALWAYS plan-confirm (ADR 0050 unchanged for writes);
- round caps, token budgets, and the anti-flail bound stay AS CODE.
Nothing polices the model's intermediate reasoning. Honesty is
enforced where action meets the user, freedom everywhere inside.

**P6 — Failure is observation.** Tool errors return INTO the
conversation as results (infra errors named per the error-contract
philosophy); the model reads them and tries differently; the caps
bound flailing. No separate retry subsystem.

## Design consequences (derived, not negotiable back to the old shape)

- The webapp turn = an agent.py-style function-calling loop over the
  ops tool set, with protocol.py's boundary wrapped around it. UI
  shows operations live as they run, stamped — "operations are the
  product" becomes the trace-as-display; the plan card remains only
  for WRITES (confirm before any write executes).
- agent.py's MCP surface and the webapp SHARE the merged engine — the
  one-engine doctrine (ADR 0046) finally literal. One turn engine,
  two surfaces.
- Model requirement: the loop needs a tool-loop-capable model. The
  mini-vs-4o question is REOPENED under the new shape — the previous
  experiment tested the amnesiac harness and is void here. Re-measure
  both; document the result.
- Suite: same fixtures, same oracles, same 100%-honesty build-stopper.
  Cage tests (Floor 1) adapt to the new loop via a scripted chat_api.
  **The thesis test: bridge and anaphora must flip WITHOUT adding a
  single question-shape prompt rule.** If they only pass with new
  casebook lines, the merge has failed its own principle — report
  that honestly rather than shipping the lines.
- Latency: the loop adds calls; set and record a p50 budget (target
  < 5s end-to-end at dev scale) and show rounds live in the UI so
  waiting is legible.
- Grader calibration items already logged in the Round-4 RESULTS
  (verbatim-overlap oracle vs paraphrase; bridge honesty demand)
  ride along.

## ADR duties

- New ADR: "the one-mind turn" — supersedes the conversation shape of
  0036/0050 (three-call protocol) while explicitly keeping their
  floors (plan-confirm for writes, bounded rounds, stamps, gates,
  typed verdicts). Context section: the amnesia diagnosis + the
  refuted model-tier experiment + Sunny's inversion insight ("the LLM
  was never deciding too much — it was deciding blind").
- SPEC.md: E-group note — interior loop decisions are linguistic
  (spec:E3, measured by suite); boundary mechanisms remain tested.
  Version-bump the spec.

## PARKED (for Sunny)

- Any relaxation of write-confirmation (none proposed; flag if the
  design pressures it).
- Model-tier choice as a customer prerequisite once re-measured.
- Round-4 execution still awaits Sunny's tenant steps (unchanged).

## Reporting

Append per-iteration suite scorecards to
HANDOFF_REMATCH_ROUND4_GOAL.md's RESULTS log as before — the Round-4
goal continues; this merge is the path to it, not a detour.
