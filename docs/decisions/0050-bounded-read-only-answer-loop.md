# 0050 — The bounded read-only answer loop (amends ADR 0036)

**Status:** Accepted (Sunny's verdicts, 2026-08-20 — HANDOFF_ANSWER_LOOP)
**Date:** 2026-08-20

## Context

The four-question dumb-trail (census / Sepsis Case Encounters / Sepsis
Case / severe-sepsis criteria): the honesty machinery held 4/4 — zero
fabrications — while three of four questions went unanswered. Root
cause: two constrained LLM calls per turn (one plan hop, one display
description), no loop, no goal check. ADR 0036 deliberately parked
autonomy ("auto-confirm policies are a FUTURE relaxation once the
confirmed-flow baseline exists"). That baseline now exists — gates,
stamped headlines, caption floor, full trace.

Sunny's ruling: "an LLM decision is acceptable only when its error
mode is visible and bounded." The loop's decision is "does the display
answer the question; if not, what next?" — under the bounds below its
error mode is one more visible, honest, read-only hop, or an honest
"couldn't answer; here's what I'd try." This is ADR 0035's
intelligence shape running inside ADR 0036's honesty frame — the
synthesis of the two designs that were each half right.

## Decision

1. **A — plan to the answer.** The planner emits the full chain
   (search → retrieve $1 → …) in ONE plan; the human confirms the
   whole plan once. Finding a thing is not answering a question.
2. **B — the caption IS the answer** (un-drifting the slogan). The
   captioner's contract: answer the user's question from displayed
   results, citing refs; if they can't answer, say which operation
   would. It also emits a TYPED verdict `{answered, missing_op}`
   beside the prose — machine-readable, graded by the conversation
   suite, logged per turn as the miss stream. A floored caption can
   never claim answered. Headlines + honesty gate remain the floor.
3. **C — bounded read-only auto-continue**
   (`protocol.continue_rounds`). Mechanical clauses, all CI-tested
   (tests/orchestrator/test_protocol.py::TestAutoContinue):
   - round cap: MAX_AUTO_ROUNDS (3);
   - READ_ONLY_OPS whitelist enforced in the EXECUTOR path before
     validation — never by prompt; a non-read-only proposal is refused
     with the refusal displayed; **writes always confirm**;
   - every auto-hop lands in the same outputs stream: stamped
     headline, visible errors, `auto_round` marker, full trace;
   - replay: same scripted decisions + same catalog ⇒ byte-identical
     trace;
   - exhaustion is honest: a code-stamped status line reports the
     rounds taken and, when unanswered, what was missing.
4. **D rejected.** Family plan-templates are dropped: a closed menu of
   question templates is ADR 0034 again. (Templates-as-priors may be
   revisited later, separately.)
5. **The conversation suite gates readiness** (ADR 0032 precedent):
   Floor 1 (exact, offline, CI) tests the cage; Floor 2
   (devtools/answer_evals.py, live dev LLM, headless, same entry the
   web UI calls) measures the mind — answer rate, honesty rate,
   bridge rate, mean rounds — graded on trace + data facts derived
   from the store, never on prose shapes. Honesty is not a metric:
   any fabrication stops the build. Manual web-UI testing resumes
   only after the suite clears thresholds (answer ≥ 80% per family,
   honesty 100%). Every future manual failure becomes a fixture
   before its fix ships; the four real corpses are the seed fixtures.

## Consequences

- The turn shape changes from translate-execute-describe to
  plan-execute-check-continue-answer, with every hop visible and every
  bound in code.
- `answered | unanswered` telemetry becomes the standing miss stream —
  the same flywheel that caught the census gap now measures answer
  quality continuously.
- ADR 0036's confirm-first doctrine is unchanged for anything that
  writes; what relaxed is only re-asking permission to READ, bounded
  and displayed.
