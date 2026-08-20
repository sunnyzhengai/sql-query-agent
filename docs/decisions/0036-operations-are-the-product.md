# ADR 0036: Operations Are the Product — Interpret, Confirm, Execute, Display

**Status:** Accepted
**Date:** 2026-08-13

> "Make the operations the product. The answer is a caption." — the
> session's slogan, Sunny-endorsed.

## Context

The demand-side first-principles review identified seven properties of
a good answer to an NL metadata question, and an audit showed every
live failure to date violated the two principles still enforced by
PROMPT rather than structure: **true to the question** (P2 — reference
and intent resolution) and **scoped honestly** (P3 — quantifiers
matching evidence). Three successive attempts to close them by
policing *language* — agent instruction casebooks, typed-intent
grammars, and finally a claim-shape gate with a quantifier lexicon —
were each rejected by Sunny as the same error: **pattern prediction
over unenumerable language.** The gate critique was decisive: "we
can't possibly predict all shapes."

The correction inverts the enforcement point. Instead of auditing
claims in prose AFTER execution, honesty is pinned BEFORE execution:
the human confirms the interpreted plan (including its completeness
parameters), watches the operations run, and sees the raw results.
Prose stops being load-bearing.

## Decision

Every NL question flows through one uniform loop — no simple/complex
special-casing (case-splitting is shape prediction again):

1. **Interpret** — the LLM translates the question into a PLAN of
   primitive components with visible parameters and a one-line
   rationale per component. Interpretation is the LLM's entire
   linguistic authority.
2. **Confirm** — the plan renders as a card; NOTHING executes until
   the human confirms (or edits) it. This is where P2 becomes
   structural: intent is validated by the only judge of intent.
   Completeness is a visible plan parameter (semantic top-K vs exact
   enumeration), which is where P3 becomes structural: you cannot
   claim "all" over a plan the user confirmed as "top 10".
3. **Execute + display** — code runs the components; raw results are
   first-class, selectable, session-registered objects (R1, R2, ...).
4. **Iterate** — the LLM captions what is on screen and proposes next
   actions over the visible results; the user composes freely.

**The primitive algebra** (store-shaped, minimal):

- `search(phrase, mode)` — mode `semantic` (vector closeness, top-K,
  NEVER a completeness instrument) or `exact` (literal enumeration,
  the only mode that can support "all"). One primitive; the old
  find_by_name/search_catalog split dissolves into a visible mode.
- `retrieve(ids)` — the full record per id; a metric's record includes
  its step inventory (get_facts/list_steps merged).
- `update(...)` — future governance writes (certify, assign steward);
  always plan-confirmed, no autonomy mode exempts writes.

**Result-set actions** — deterministic kernels, open orchestration:

- `compare(items, aspect?)` — exactly three kernels, composable over
  any selection: content-equality partition (any N; pairwise, ten-way,
  one-vs-many are all "partition this set"), set algebra (lists),
  scalar diff (fields). The LLM/user choose WHAT to compare — the
  kernels compute the verdicts. The LLM is the orchestrator, never
  the calculator.
- `explain(...)` — prose over results visible in the session (all
  prior rounds), with its input sets stamped by code.
- "dig" is not a primitive: it is the LLM proposing the next plan.

**Provenance:** the visible session IS the basis. The code-stamped
Basis footer of ADR 0035 is superseded by the interface — every
operation, parameter, and raw result on screen as it happens. (The
turn telemetry — decision shapes, traces — continues unchanged
underneath; gov_turn_events records plans and confirmations.)

## Consequences

- The claim-shape gate is NOT built (rejected as pattern prediction).
  decision_shape stays as post-hoc telemetry only.
- ADR 0035's agent loop is superseded as the conversation protocol;
  its tool layer refactors into the primitives (kernels, session
  guarantees, and infra-errors-as-results all survive). Its two
  dispatch guarantees persist: no unsurfaced reads; everything traced.
- The web surface rebuilds as a chat-workbench hybrid: plan cards
  (confirm/edit), result panels, action chips, running narration —
  "guide the user without ambiguity" (Sunny). This supersedes the
  chat-bubble surface and becomes the demo.
- The robustness suite regrades to plan quality: does interpretation
  produce the right components/parameters across paraphrases; are
  captions grounded in displayed sets.
- Autonomy modes (auto-confirm policies) are a FUTURE relaxation to
  design once the confirmed-flow baseline exists; writes never relax.

## Amendment (2026-08-20): the stamped headline — E6's last holdout closed structurally

A caption over-claim in live testing ("no metrics available" conjured
from an empty NAME-scoped search) re-posed the language-policing
question. A prose lint over "no/none/all/N" claims was built and then
correctly re-identified (review session, Sunny's verdict) as the
claim-shape gate this ADR already rejected — a lexicon cannot bound
English.

The structural fix is ADR 0032's provenance pattern applied to its
last holdout: every result panel's quantitative/existential sentence
is a STAMPED HEADLINE, rendered by code from the result's typed
metadata (count, scope, completeness, kind-vs-name redirect); the LLM
caption is commentary beneath it. A lying caption is contradicted on
screen, not caught. The lint stays as defense-in-depth, classified
MEASURED (flags/floors heuristically), never the basis of a soundness
claim. Recorded as the E6 amendment in SPEC.md; fixture = the
2026-08-20 transcript.
