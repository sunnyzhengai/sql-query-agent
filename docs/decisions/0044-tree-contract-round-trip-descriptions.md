# 0044 — The tree contract: faithful decision trees, blind round-trip verification

**Status:** Accepted (contract locked before implementation; phases gated below)
**Date:** 2026-08-19

## Context

The 2026-08-18 deep trace ([TRACE_USP_ED_SEPSIS](../internal/TRACE_USP_ED_SEPSIS.md))
found the deterministic pipeline truthful (43/43 steps, every asserted
edge real) and the LLM description stage not (three fabricated filters,
invented codes). 1.25.0 removed the root cause (500-char fragment
truncation) and added a string-space grounding gate — which catches
invented literals mechanically but is blind to *meaning*: direction,
negation, attribution. Sunny named the paradox precisely: "we use LLM
because regex can't handle all variations; now we are using regex to
validate something we can't pre-define."

His proposal, four points, verbatim in substance:

1. "Mathematically, all SQL queries are trees, and exhaustively so" —
   SQL engines execute from ASTs; parseability is total for static SQL.
   (Confirmed: ScriptDom already yields the complete tree. The coverage
   ceiling identified in the preceding analysis was a property of
   *flattening* trees into fact-triples, not of trees. Dynamic SQL —
   `EXEC(@sql)` — is the one true exception and stays a counted gap.)
2. Implement parsing as a *faithful tree*. Today the graph keeps
   references (tables, columns, reads) but predicates survive only as
   raw `sql_fragment` strings handed to the LLM. The original design —
   WHERE clauses as graph nodes connected to their columns — was never
   built. Build it.
3. The tree is the shared heart: today it grounds descriptions;
   next phase it grounds self-service — NL question → LLM-translated
   intent tree → deterministic comparison against corpus trees →
   route the action (use existing report / adjust parameters /
   generate new SQL). One ground truth for both engines. (The diff
   kernel, [0043](0043-diff-kernel-comparison-shape.md), is the
   comparator prototype at coarser grain.)
4. Round-trip verification: translator LLM renders tree → description;
   a second LLM reverse-engineers the description (dictionary only,
   **never shown the SQL or the tree**) back into a tree; a
   deterministic diff compares reconstructed vs original; mismatches
   bounce back to the translator until they match.

The threat model is the notebook contract's ([0042](0042-notebook-contract.md)),
applied to epistemics: prompt instructions are intent, and intent
decays under model pressure — the trace proved "Ground every line in
the SQL above" was already in the prompt when the fabrications shipped.
Only mechanical enforcement survives. So the contract is written and
locked in CI **before** the redesign, and implementation is defined as
making its clauses pass.

## Decision

Adopt the tree architecture in four roles with strict information
boundaries — extractor (deterministic, ScriptDom AST → persisted
decision tree), translator (LLM; sees typed tree facts + dictionary,
never SQL), verifier (LLM; sees description + dictionary, never SQL or
tree), judge (deterministic tree diff, never an LLM) — with a
deterministic template renderer as the floor. And lock it with the
**Tree Contract**: six clauses, each an intention bound to a mechanical
check, enforced by `tests/test_tree_contract.py`.

| # | Intention | Mechanical enforcement |
|---|---|---|
| 1 | **Conservation of decision sites.** The persisted tree is lossless for static SQL: every decision-bearing AST node (WHERE / ON / HAVING / CASE WHEN / subquery) maps to exactly one tree node OR one counted `unextracted` row — `handled + unextracted == total`, no third bucket. Boolean shape (AND/OR/NOT nesting) is preserved, never flattened. | Side-by-side walk of ScriptDom's AST and our tree asserts the equation per proc; an unmodeled construct fails the count instead of vanishing (the 13k-suppression-counter lesson, promoted from observation to invariant). Every `unextracted` row (dynamic SQL, unmodeled constructs) ALSO lands in `ops_fallout` (stage `300_tree_unextracted`) and escalates to the human checklist per [ADR 0045](0045-escalation-contract-human-checklist.md) — visible on the admin dashboard, never only an internal counter. |
| 2 | **Translator blindness.** The description LLM's prompt is built from typed tree nodes + dictionary lines; raw `sql_fragment` is banned input. | Prompt-capture test asserts no fragment substring beyond declared literals reaches any prompt; the prompt builder's signature has no `fragment` parameter (AST plank, the 0042 regex-ban pattern). |
| 3 | **Verifier blindness.** The reconstruction LLM receives ONLY the description + dictionary. This is the clause that keeps round-trip from collapsing into circularity. | Prompt-capture + signature test: no SQL token, no tree serialization in the verifier's input; its builder accepts exactly (description, dictionary). |
| 4 | **The judge is never an LLM.** Tree comparison is deterministic code. | AST plank on the diff module: any LLM-client import or describe-callback parameter fails CI; identical inputs must produce identical output. |
| 5 | **Every decision is voiced or counted.** The renderer emits a ledger: each must-voice tree node ↔ one description line; unvoiced nodes are `ops_fallout` rows (stage `600_tree_coverage`), never silent omissions. | A description is accepted only if the ledger balances: `voiced ∪ unvoiced == must_voice`, disjoint. Funnel shows description completeness per run. |
| 6 | **Failure-polarity floor.** After N bounced round trips the output is the deterministic template render of the tree — stilted but true. Every published description carries `provenance ∈ {round_trip_verified, template_fallback, flagged}`. | Acceptance test feeds a never-converging translator and asserts the result is still 100% grounded template text with provenance `template_fallback` — the worst case is exercised, not assumed. No NULL provenance on described nodes (TABLE_REGISTRY invariant when the column ships). |

Two meta-clauses carried over from the contracts that held:

- **Fixtures are real corpses.** Acceptance fixtures are the actual
  captured fabrications (Base_Pop's invented triage filter, the
  123/456 codes) and real corpus constructs (the LDA OR-inside-AND,
  the systolic CONVERT/LEFT/CHARINDEX expression, the NOT EXISTS
  exclusion). Every future field fabrication becomes a fixture before
  its fix ships.
- **Version binding.** `TREE_CONTRACT_VERSION` participates in every
  description cache key (the `PROMPT_VERSION` mechanism): tightening
  the contract regenerates everything it governs; stale certified text
  cannot survive a stricter contract.

The joint property: **a false statement has no constructible path into
a published description.** Clause 2 — the translator can't copy an
error out of raw SQL it never sees. Clauses 3+4 — an error can't be
waved through by a sympathetic judge. Clause 5 — silence is counted,
not invisible. Clause 6 — exhausted retries degrade to truth, not to
hope. Clause 1 bounds it honestly: unmodeled constructs and dynamic
SQL exist as numbers on the funnel — supportable at a distance.

### Phases and exit gates

The clauses are checked in **red** as `strict` xfail skeletons in
`tests/test_tree_contract.py`. Strict xfail means CI *fails the moment
a clause starts passing* until its marker is removed — flipping a
marker is the exit gate, mechanically enforced, per phase:

1. **Persist the faithful tree** (extractor; predicate/join/window
   nodes; conservation counter; `unextracted` → fallout + checklist).
   Exit: clause 1 green. — **SHIPPED 1.26.0 (2026-08-19)**: sqlglot-AST
   extractor in `src/tree/extract.py`, conservation proven over all
   417 recorded corpus fragments, `graph_decision_sites` written by
   300, unextracted sites escalated via `ops_fallout`
   stage `300_tree_unextracted`.
2. **Tree-walking translator** (fact prompts + ledger accounting).
   Exit: clauses 2 and 5 green.
3. **Blind round-trip loop** (verifier, deterministic diff, template
   floor, provenance). Exit: clauses 3, 4, 6 green.
4. **NL-intent matching** (self-service; consumes the same tree +
   canonicalization). Out of description scope; separate ADR when
   phase 3 holds.

### Honest limits, stated up front

- **Dynamic SQL** has no static tree, ever. It is a permanent counted
  gap (clause 1's `unextracted`), surfaced on the funnel, the admin
  journey dashboard, and the human checklist
  ([ADR 0045](0045-escalation-contract-human-checklist.md)) — never
  described by guesswork, never silent.
- **Correlated LLM errors**: translator and verifier could make
  mirror-image mistakes on the same ambiguity. Blind reconstruction +
  deterministic diff makes this rare, not zero; using a different
  model for the verifier narrows it further (deployment option, not a
  contract clause).
- **Equality vs equivalence**: semantically equal trees rarely arrive
  structurally identical; the diff needs canonicalization (boolean
  commutativity, join order — the `_content_key` lineage). Phase 3
  scope; the contract requires only that the *comparison itself* is
  deterministic.

## Consequences

- The redesign has a definition of done that is not prose: six green
  clauses. Test-first at architecture scale.
- Descriptions stop being trusted-because-gated and become
  verified-by-reconstruction, template-true, or flagged — with
  provenance queryable per node.
- The round trip pressure-cooks prose toward unambiguous,
  reconstructible language — descriptions a second reader (human or
  machine) parses one way only, which is what a certified definition
  should be.
- Cost accepted: 2–3 LLM calls per changed step (translator + verifier
  + bounces), amortized by the existing content-hash cache; and the
  tree schema is new graph surface to maintain — priced against the
  self-service phase it also powers.
- Supersedes in part [0032](0032-deterministic-core-llm-edges.md)'s
  description flow (LLM reads raw fragments) — the "deterministic
  core, LLM edges" principle survives; the edge just got narrower:
  from *interpret the SQL* to *translate one fact at a time, then
  prove the translation round-trips*.
