# ADR 0034: The Conversational Entry Edge — Language to the LLM, Computation to Code

**Status:** Accepted
**Date:** 2026-08-10

## Context

Three consecutive live sessions each exposed a question the orchestrator
mishandled: "show me its sql" (follow-up projection), "are they all using
the same definition?" (set-subject computation), "how is this different
from an ED sepsis?" (context-bound comparison). The first and third were
patched with deterministic *linguistics* — a filler-word list, keyword
sets, a proposed special-case intent. Sunny named the pattern: "you
cannot pre-build every shape" — and for the linguistic layer, that
critique was correct. Keyword matching cannot enumerate English.

The resolution came from re-reading ADR 0032's own division of labor:
"the LLM translates." Reading a conversation and resolving *this / it /
they / these two* IS translation — the one job that cannot be pre-built
and the one job the LLM is natively for. The mistake was applying
determinism to language instead of confining it to computation.

The contract was validated before implementation by an 8-question paper
test (docs/internal/VERB_SCORECARD.md): Sunny fired question shapes,
each was scored against the proposed structure, and five contract
amendments were extracted. Verdict: green-lit, scorecard = acceptance
criteria.

## Decision

**One conversational entry edge.** Every turn, the LLM receives
code-built conversation state (the last answer, the visible candidate
list — labels carry ids) plus the new question, and emits ONE typed
request from a closed menu:

| Form | Executed by |
|---|---|
| plain lines (DEFAULT) | search: semantic_search per phrase → pick → assemble → narrate |
| `DETAIL: sql\|owner\|tables\|link` | projection of cached facts — no LLM, no re-resolution |
| `VARIANTS: <name>` | family lookup → content-hash partition (ADR 0032-era build) |
| `COMPARE: A \| B [\| on=aspect]` | the fixed comparison panel (below) |
| `UNSUPPORTED: lineage\|enumerate\|usage\|data-values` | honest named refusal, logged |

Structural validation on every form; anything malformed degrades to
search — a misbehaving model can only ever produce the default flow.
The LLM chooses and binds; it never composes a query and never answers.

**The compare panel (scorecard amendments 1-3).** `compare(A, B)` runs
the same full checklist regardless of phrasing: scalar fields
(developer, steward, report) → typed equality verdicts; list fields
(source tables, step names) → set algebra (shared / only-A / only-B);
whole-logic content-hash equality; per-shared-step-name hash check (the
variants kernel) separating shared-by-name from shared-by-logic. A
concept aspect ("ED sepsis definition") resolves INSIDE each subject's
steps via the same semantic_search scoped by ref, with a human pick
when a side is ambiguous, and the equality kernel runs on the matched
pair — never the wholes. The LLM narrates computed verdicts; it never
judges sameness (a language model's impression of two 2,000-line SQL
bodies is not a measurement).

**Typed misses (amendments 4-5).** Verb-gaps refuse by name and are
logged — the miss stream demand-ranks the punch list of unbuilt verbs.
Fact-gaps say "not recorded here" and route to the fact's canonical
home when known (table ownership → the customer's catalog, ADR 0006).

## Consequences

- Deterministic-linguistics code deleted: the filler-word list, the
  keyword detail matcher, the plural-token entry function. New
  phrasings and bindings never require code again; only new
  COMPUTATIONS do (bounded by what facts can be combined) and new
  FACTS (bounded by what the parser extracts).
- The scorecard's questions are regression fixtures
  (tests/orchestrator/test_compare.py); classification quality across
  paraphrases is the robustness suite's job to measure live.
- Punch list (demand-logged from misses): `enumerate(kind, filter)` —
  one verb subsuming lineage ("metrics using table X" is a closure-
  membership filter) and by-field listing ("metrics Smith wrote");
  table names joining the resolution path.
- The pick and confirm prompts remain structural (digit / exact name /
  y-n parsed by code, escape hatch to a new question) — they are
  conversation *moves*, not language to interpret.
- The entry edge is surface-agnostic: the web chat and Teams surfaces
  (ROADMAP: one backend, two faces) inherit it unchanged.
