# Operations Are the Product (OAP)

**The AIVIA methodology. Coined 2026-08-13 (Sunny + Claude), bound in
ADR 0036, mechanically enforced by `src/methodology.py` +
`tests/test_methodology.py`.**

## The four lines

> Data can be operated on three ways: **search** (semantic|exact),
> **retrieve**, **update** — plus three **compare kernels** over results.
> The **LLM translates** questions into plans of those operations.
> The **human regulates** — every decision visible, confirmable,
> interceptable.
> Everything **displays** — results are the answer; prose is the caption.

Core law: **translated by LLM, regulated by human.** Complexity lives
only in composition — generated per question, discarded after. Simple
is a discipline, not a state.

## Lineage

The method descends from a real tradition and adds one new element:

| Year | Inventor | The inherited idea |
|---|---|---|
| 1952 | Grace Hopper (A-0, the compiler) | human-shaped language is TRANSLATED into sequences of primitive machine operations — intent is human, execution is operations |
| 1958 | John McCarthy (Lisp) | a complete language from a handful of primitives — minimal operation sets plus composition beat feature enumeration |
| 1970 | E. F. Codd (relational algebra) | a small closed operator algebra generates every query; completeness lives in the algebra, not in enumerated cases |
| 2026 | this project | the translator is now STOCHASTIC — so the loop adds a REGULATOR: every translation is confirmed by the human before execution |

## The anti-pattern this exists to kill: pattern predefinition

Enumerating language — question shapes, claim shapes, comparison
shapes, keyword lists, filler words, quantifier lexicons — and wiring
the enumeration into the control path. It failed here three times, in
three disguises, each caught by the regulator:

1. Agent instruction casebooks (question templates) — 2026-08-08
2. Typed-intent grammar + keyword detail matcher — 2026-08-10
3. Claim-shape gate with quantifier lexicon — 2026-08-13

The disguise evolves; the move is identical. Hence mechanical guards.

## The guards (what CI enforces, every run)

1. **No user-English in the control path** — literal string
   collections in control files must be registered SYSTEM vocabulary
   (our ops, modes, fields); multi-word phrase lexicons are banned
   outright. (Would have caught all three historical incidents.)
2. **Closed operation registry** — every `op_*` in the control path
   must be registered with a *data-shaped* justification ("the store
   admits...") and an ADR. Question-shaped function names are banned.
3. **Prompt budgets** — line cap and quoted-example cap on the system
   prompt. Instruction creep is pattern predefinition in prose.
4. **Observation is not control** — language lexicons are legal only
   in declared observer modules (telemetry watches; it never decides).
5. **Manifest integrity** — the four lines and the control-file list
   are asserted present and real.

## The amendment rule (the honest limit)

No guard fully binds its own author: Claude writes the tests and
could, in principle, rewrite them. Therefore bypasses are made LOUD,
not impossible, and legitimacy comes from the loop itself:

- A failing methodology test is NEVER fixed by editing
  `src/methodology.py` — that is a silent amendment, forbidden.
- Amendments (new operations, new vocabulary, raised budgets, new
  control files) require an ADR and **Sunny's explicit approval**,
  requested in plain language, before the manifest changes.
- The methodology governs its own repo the same way the product
  governs answers: translated by Claude, regulated by Sunny.
