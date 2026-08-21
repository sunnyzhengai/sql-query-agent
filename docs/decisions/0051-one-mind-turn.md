# 0051 — The one-mind turn: one conversation decides, the boundary enforces

**Status:** Accepted (Sunny's merge verdict via the review session,
2026-08-21 — HANDOFF_ONE_MIND). Supersedes the CONVERSATION SHAPE of
ADR 0036/0050 (the three-call plan→execute→judge→caption protocol)
while explicitly keeping their floors.
**Date:** 2026-08-21

## Context

The diagnosis, verified in code: the webapp ran three amnesiac minds —
planner, goal-check, captioner — each a forced single-shot JSON call;
tool results never entered the conversation history (only a 1,500-char
plan stub and the caption did); each call saw a freshly compacted
20k-char display blob, then forgot it. Six suite iterations patched
the symptoms of that amnesia: stamps to carry what memory should have
carried, casebook prompt rules to instruct what evidence should have
taught, a goal-check to re-derive what the mind should have known.
The model-tier experiment failed BECAUSE of this shape — a stronger
amnesiac is still an amnesiac.

Sunny's inversion insight, recorded verbatim in spirit: **the LLM was
never deciding too much — it was deciding blind.** Meanwhile agent.py
(ADR 0035) already implemented the other architecture on the MCP
surface: one conversation, full tool results in history,
invariants-only prompt. The two halves had never met.

## Decision — the six principles (normative; each is an acceptance property)

1. **One mind.** A single LLM conversation makes every decision in a
   turn — what to do, whether results suffice, what the answer is.
   The separate planner/goal-check/captioner minds are retired.
2. **Full evidence, persistent.** Complete tool results enter the SAME
   history and persist across rounds and turns. Context compaction
   degrades gracefully — oldest results compact to their stamped
   headline + totals (never dropped); recent results stay whole;
   budget sized to the model window, not a per-call amputation.
   Anaphora is a property of memory, not a prompt rule.
3. **Thinking room.** The model may reason between tool calls. Forced
   tool_choice is legal only for genuine form-fills (the final typed
   verdict). Composition happens in reasoning.
4. **Free composition over primitive tools.** The deterministic ops
   are the tool set; the model composes them freely. NO
   question-family control flow anywhere — not in prompts, not in
   gates, not in stamps. The casebook prompt rules (planner shape
   rules, mandatory-bridge clause, pointer doctrine) are DELETED, not
   ported. The suite MEASURES whether a mind holding full evidence
   bridges and follows pointers natively; the thesis test is that
   bridge and anaphora flip with zero new prompt rules.
5. **Honesty at the boundary, not in the interior.** Kept, relocated:
   stamped headlines on every displayed panel; the final answer passes
   the caption gate and emits the typed verdict with machine-verified
   evidence_quote; dispatch whitelist + read-guarantee; writes ALWAYS
   plan-confirm (ADR 0050 unchanged for writes); round caps, budgets,
   anti-flail AS CODE. Nothing polices intermediate reasoning.
6. **Failure is observation.** Tool errors return into the
   conversation as named results; the model adapts; the caps bound
   flailing. No separate retry subsystem above the transport layer.

## Consequences

- One turn engine (src/orchestrator/turn_engine.py), two surfaces:
  the webapp and the ADR 0035 MCP loop share it — the one-engine
  doctrine (ADR 0046) finally literal.
- The UI shows operations as they ran, stamped — "operations are the
  product" becomes trace-as-display; the plan-confirm card remains
  only for writes.
- The model-tier question is REOPENED: the refuted experiment tested
  the amnesiac harness and is void under this shape. Both tiers get
  re-measured; the result is documented (tier choice as a customer
  prerequisite stays PARKED for Sunny).
- Iteration-5's interior enforcement (the bridge-duty gate check and
  the pointer verdict demotion) is REMOVED with the casebook: those
  were question-family control flow in gate clothing. Their protection
  is replaced by memory (P2) and measured by the suite; the
  evidence-quote proof (boundary) remains the dishonesty kill.
- Latency: the loop adds calls; p50 budget target < 5s end-to-end at
  dev scale, recorded per suite run.
- Failure honesty: if bridge/anaphora only pass WITH new casebook
  lines, the merge has failed its own principle — that result is
  reported, not papered over.
