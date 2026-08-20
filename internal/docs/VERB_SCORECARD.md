# Verb Scorecard — paper test of the conversational entry edge

**Date started:** 2026-08-10
**The deal:** Sunny asks questions in as many shapes as they can; each is
scored against the PROPOSED structure (below) — no code changes during the
game. If the final score is satisfactory, the refactor is green-lit with
this scorecard as its acceptance criteria; every question here becomes a
test fixture.

## The contract being scored

One conversational entry edge: the LLM sees the recent conversation
(last answer, last candidate list) plus the new question, and emits ONE
typed call from this closed menu. Code validates the call and executes
deterministically. The LLM never composes a query; invalid calls degrade
to search.

| Call | Computation (all fixed/deterministic) |
|---|---|
| `search(phrases[1..3])` | semantic_search per phrase → candidate list → human picks |
| `detail(sql\|owner\|tables\|link, target)` | projection of cached/assembled facts; target bound from context |
| `variants(name)` | family lookup → content-hash partition → diff |
| `compare(concepts[], bindings)` | resolve/bind each side → narrate_many over fact sets |
| `pick(n\|name)` / `decline` / `confirm(y/n)` | conversation moves on the visible list/answer |
| `refuse` | nothing sufficiently related (ADR 0005) |

Facts available per node (what any answer can be made of): description,
SQL fragment / calculation logic, steward + developer, source tables,
report name + URL, parent metric, step counts.
Known NOT yet exposed as verbs: enumerate (list all X), lineage
(what feeds X / closure), usage (who uses X, how often), and anything
requiring DATA VALUES (tier-2 analytics) or write actions.

## Contract amendments made during the game

1. (Q2) `compare` must never ask the LLM to judge sameness. When the
   question is "are X and Y the same?", code computes: content-hash
   equality of normalized logic + step-name overlap + per-shared-step
   variants check. Narration receives the computed verdict as facts.
2. (Q2 follow-up) A comparison has THREE slots: subject A, subject B,
   and the ASPECT compared — "are these two using the same ED sepsis
   definition" is not "are these two identical". The call is
   `compare(A, B, on=<concept>)`; the engine resolves the concept
   INSIDE each subject (same semantic_search, scoped to that metric's
   steps), the human picks per side if ambiguous (no bypass; the pick
   is flywheel signal), and the equality kernel runs on the picked
   parts — never the wholes. Whole-proc equality answers a question
   the user didn't ask.
3. (Q4) Field comparison is TYPED: scalar fields (developer, steward,
   report) compare as equality; list fields (source tables, step names)
   compare as set algebra — shared / only-in-A / only-in-B — computed
   from precomputed closures (ADR 0018), never narrated from raw text.
4. (Q6) The menu includes `unsupported(reason)` for the closed list of
   recognized-but-unbuilt intents (lineage, enumerate, usage, data
   values): honest refusal naming the gap, instead of degrading into a
   semantically-adjacent pick list (refuse-over-guess at the verb
   level, ADR 0005). Unsupported classifications are logged per verb —
   the punch list gets demand-ranked by real misses.
5. (Q7) Misses are TYPED. Verb-gap: computation not built →
   unsupported, logged. Fact-gap: fact not in schema → say "not
   recorded here" and ROUTE to the fact's canonical home when known
   (table ownership → the customer's catalog, per ADR 0006), optionally
   offering the nearest fact we do hold. Never guess, never
   half-answer; a refusal may still be useful.

## Scoring rubric (adversarially honest)

- ✅ **HANDLED** — a call on the menu answers it correctly from available facts
- 🟡 **HONEST-MISS** — not answerable, but the structure refuses or degrades
  honestly (acceptable per refuse-over-guess; noted for the punch list)
- ❌ **FAIL** — would mis-answer, half-answer, or need a computation that
  breaks the model (these are the thesis-killers)

## Scorecard

| # | Question (as asked) | Typed call the edge should emit | Score | Notes |
|---|---|---|---|---|
| 1 | what metric defined ED sepsis | `search(["ED sepsis"])` | ✅ | Two ED sepsis metrics exist (screening vs regulatory) — pick surfaces the ambiguity instead of guessing. Polish: rank kind=metric ahead of steps when the question says "metric". |
| 2 | are these two metrics using the same ED sepsis definition | `compare(A, B, on="ED sepsis definition")` | ❌→✅ | TWO contract defects found: (a) compare-as-narration would let the LLM *judge* sameness of big SQL bodies — amended: code computes equality; (b) the aspect slot was missing — "same sepsis definition" ≠ "identical metrics"; concept aspects resolve via scoped search + human pick, then the equality kernel runs on the picked parts. |
| 3 | were these two metrics written by the same developer | `compare(A, B, on="developer")` | ✅ | Zero amendments. "developer" is a schema FIELD, not a concept: the panel computes field-by-field equality across ALL scalar fields in one loop, always. Every "same X?" where X is a schema field is already answered by the same panel — novel phrasing, nothing to build. The field list in the LLM's menu is generated from the schema, never hand-predicted. |
| 4 | what tables do these two metrics share | `compare(A, B, on="source tables")` | ✅ | Amendment 3 (generalizing): field comparison is TYPED — scalar fields → equality; list fields (tables, steps) → set algebra (shared / only-A / only-B), computed from the ADR 0018 closure. Closes the whole set-question family in one rule. |
| 5 | which steps do these two metrics share | `compare(A, B, on="steps")` | ✅ | Zero amendments — covered by amendments 1+3 combined. Two depths, both computed: shared BY NAME (set algebra) and shared BY LOGIC (per-shared-name hash check). Corpus proof this matters: 6 procs share the name Base_Pop_Severe_ED_Scores; 5 different logics hide behind it. Name-only sharing would over-state alignment. |
| 6 | which metrics are downstream of the ADT table | `unsupported("lineage")` today; `lineage(table)` when built | 🟡 | Known-missing verb (pre-declared). Data ALREADY precomputed: reverse read of the ADR 0018 closure — one fixed query once tables join the resolution path. Amendment 4: without an explicit unsupported classification, degraded search would show semantically-adjacent steps — a pick menu into the wrong question. Refusals logged per missing verb = demand-ranked punch list. |
| 7 | who owns the ADT table | `detail(owner, "ADT table")` → fact-gap response | 🟡 | Different miss TYPE than Q6: the verb exists, the FACT doesn't — ownership attaches to metrics (ADR 0027), tables carry none. Honest routing per ADR 0006: table ownership is catalog territory (Purview); offer the nearest held fact (stewards of every metric reading ADT, via the closure). Amendment 5: misses are typed — verb-gap vs fact-gap. |
| 8 | show me all metrics that a specific developer wrote | `enumerate(metrics, where developer=<name>)` | 🟡 | PUNCH LIST COLLAPSED: Q6 "lineage" and Q8 "enumerate" are ONE verb — enumerate(kind, filter), filter = field equality OR closure membership (same typing as amendment 3). Value resolves against the field's distinct values (pick if ambiguous). Set-subject: the list IS the answer. Honest-coverage rule: report unattributed counts ("12 by Smith; 214 with no developer recorded") — absence must not masquerade as inventory. |

## Verdict

**Called by Sunny 2026-08-10: "i think we are pretty good shape." —
REFACTOR GREEN-LIT.**

Final tally over 8 questions: 4 ✅, 1 ❌→✅ (two contract defects found
and amended), 3 🟡 (all honest misses). The misses consolidated rather
than sprawled: all three map to ONE unbuilt verb (enumerate with typed
filters — subsumes "lineage") plus ONE schema fact-gap (table
ownership → routed to Purview per ADR 0006). Amendments per question
trended 2 → 0 → 1 → 0 → 1 → 1 → 0 with each amendment more general
than the last.

This scorecard is the acceptance criteria for the conversational entry
edge refactor: every question above becomes a test fixture; the typed
calls in column 3 are the expected classifications.
