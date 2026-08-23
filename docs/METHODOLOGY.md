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

## The enforcement lineage (prior art for the contract regime)

Recorded 2026-08-21 (Sunny's mandate) so future references have names.
No single framework contains this stack; every piece has a literature:

| Our invention | The tradition that formalized it |
|---|---|
| Table contracts, pre/postcondition gates | **Design by Contract** — Bertrand Meyer, Eiffel (1986) |
| SPEC.md, axioms, refinement, `G ⊨ Φ` | **Formal specification** — Z, VDM, Alloy, TLA+ |
| Reference/key invariants, conservation equations | **Database dependency theory** — TGDs/EGDs, the chase |
| TRACE_REGISTRY, ADR → code → test lineage | **Traceability matrices** — mandated by safety-critical standards |
| "Intentions decay; only enforcement survives" | **Poka-yoke** — Toyota mistake-proofing |
| Real-corpses rule, error-contract philosophy | **SRE postmortem culture** — Google (incident → class-level fix) |
| "Undeclared consumers", the consumer police | **"Hidden Technical Debt in ML Systems"** — Sculley et al., 2015 |
| Conversation suite, honesty as build-stopper | **Eval-driven development** — frontier-lab practice |
| Escalation contract, no silent residue, drift detection | **STAMP/STPA** — Nancy Leveson, systems safety |

Two umbrella standards worth reading for positioning (healthcare
buyers recognize them): **IEC 62304** (medical-device software
lifecycle — mandates requirements traceability, verification at every
level, configuration management, formal anomaly resolution: our
registries, trace contract, gates, and escalation contract, written by
a standards committee) and **DO-178C** (avionics — adds coverage
analysis: proving nothing exists outside the tested inventory, our
Group C). **STPA** is the proactive form of our drift lesson: systems
fail by silently migrating into states nobody chose, wherever a
feedback loop is missing — the generative question set behind the
design-review clause (SPEC.md §3b, the three questions).

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

## What can and cannot be proven (the mathematical footing)

**The algebra side — completeness is achievable.** Codd (1972): a
finite operator basis (relational algebra) provably expresses ALL
first-order queries — finite primitives covering infinite questions
is a theorem, not a hope. Our four are a workload-chosen SUB-basis of
that framework: retrieve/exact-search/compare-kernels/update are
algebra-expressible; semantic search is a deliberate extra-algebraic
finder (marked complete:false forever); general join is an unregistered
future kernel; transitive closure (lineage/reachability) is PROVABLY
inexpressible in first-order logic — which is why ADR 0018
materializes closures at build time, converting the provably-hard
class into a retrieve. Gaps fail LOUD at plan time ("no operation for
this"), never wrong at answer time; the human-approved raw-KQL escape
hatch is relationally complete as the last resort; the registry is
the regulated path toward full completeness.

**The translation side — completeness is impossible, provably so.**
(1) "All user questions" is not a formally definable set — nothing to
quantify over; (2) a learned model is an unspecifiable function —
universal properties of unwritable functions cannot be verified;
(3) the function is stochastic — only statistical statements exist.
The correct response, with real standing in logic, is the
PER-INSTANCE WITNESS (the structure of interactive proof): don't
prove the translator universally right; check each translation with
the only oracle of intent — the asker. Suites bound the error RATE;
confirmation bounds the error IMPACT.

**The asymmetry IS the methodology:** prove where proof exists (the
algebra, the kernels, the code); witness where it doesn't (the
translation, one confirmed plan at a time). The regulator is not a
concession — it is the load-bearing consequence of a theorem.

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
