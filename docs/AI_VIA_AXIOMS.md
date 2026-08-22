# AI via Axioms (AIVIA) — a framework for designing agentic systems

**Version:** 0.1 — 2026-08-21
**Authors:** Sunny Zheng (axioms, groups 1–3, the mandate) with the
review session (groups 4–6, theorems, formalization)
**Reference implementation:** AIVIA, the SQL Intelligence Agent — every
axiom below descends from a documented incident in its construction or
a proof in its specification (`docs/architecture/SPEC.md`). The name is
the thesis: **AI VIa Axioms** — the product is the framework's proof.

## The claim, honestly scoped

This framework offers **conditional guarantees**: *if* a system
satisfies the axioms, *then* the theorems in §5 hold — a false
statement has no constructible path to the user, completeness is
checkable against a declared frontier, nothing fails silently. What no
framework can offer, and this one refuses to pretend to, is a proof of
intelligence: **honesty is provable; intelligence is only measurable;
residue is ownable.** A framework claiming more is fraud; one claiming
less is a blog post.

## 1. The eight parts (what every agentic system consists of)

| # | Part | Role |
|---|---|---|
| 1 | **World** | the ground-truth substrate: system of record, witnesses, projections |
| 2 | **Mind** | the LLM in a loop; capability = model × context × loop-shape |
| 3 | **Algebra** | closed, typed, deterministic operations with declared completeness |
| 4 | **Boundary** | honesty enforced where thought becomes action or answer |
| 5 | **Regulator** | the human, owning exactly the intent-typed decisions |
| 6 | **Ledger** | append-only events; provenance; derived weights |
| 7 | **Immune system** | contracts, registries, conservation, drift detection, escalation |
| 8 | **Measure** | the verification strata: tested / measured / judged |

Dependency laws: the Mind asserts only what the World witnesses; the
Mind's quantified claims are bounded by the Algebra's completeness
declarations; decisions bind to deciders by type; every human
interaction feeds the Ledger; every artifact class enters through the
Immune system's three questions; every claim of quality lives at the
lowest Measure stratum that can carry it.

## 2. The axioms

Format per axiom: statement · gloss · descent (the incident or proof
it comes from) · enforcement shape.

### Group D — Data (Sunny's axioms, 2026-08-21)

**D1 — No data is unreachable.** Every artifact class is reachable
through a declared operation or carries an explicit exclusion row.
*Descent:* the 7%-reachability incident — a graph of 6,528 nodes whose
ask-surface reached 472, and nobody had decided that. *Enforcement:*
reachability registry + CI closure check.

**D2 — No transformation is defined more than one way.** One owner per
capability; a second implementation of an owned capability is a
registry validation error. *Descent:* the parser relapses (regex,
sqlglot) — settled tools quietly re-entering under deadline pressure.
*Enforcement:* capability registry; import-graph inclusion
(`Uses ∖ S = ∅`).

**D3 — All data has exactly one owner.** One writer per store; human
layers are owned by humans and never overwritten by pipelines.
*Descent:* the purged UsageTracker (mutating graph state per query);
the terms-live-in-governance-tables ruling. *Enforcement:* owner
column in the contract registry; single-writer checks.

**D4 — Every transformation is defined by data shapes first.** Input
and output shapes are declared as registry rows before implementation
exists. *Descent:* Design by Contract, enforced as the design-review
clause after two frontier incidents. *Enforcement:* contract registry
rows precede code; gates are derived from the registry, never
hand-listed.

### Group S — Specification (Sunny's axioms, 2026-08-21)

**S1 — The world has a formal specification.** A theory Φ exists; the
system is correct exactly when its state models it (`G ⊨ Φ`); drift is
a named axiom violation, never a feeling. *Descent:* the shadow spec —
built after design-in-the-head diverged from code three separate ways.
*Enforcement:* validation gate as data model-checker; CI as code
model-checker.

**S2 — The founder defines the start state, the end state, and every
transformation step.** The specification precedes and outranks the
implementation (refinement); code that disagrees with the spec is
wrong by definition until an amendment is ratified. *Enforcement:*
amendment rule — axiom changes require a recorded decision; spec
version participates in cache keys.

**S3 — States are data shapes.** All state that matters is observable
as data — because only data-shaped state can be model-checked,
conserved, and owned. *Descent:* "counted is not owned" — funnel bars
vs. checklists. *Enforcement:* no load-bearing state in logs, prose,
or memory; state tables carry contracts.

### Group J — Judgment (Sunny's axioms; J2 amended by accepted ruling)

**J1 — The founder defines correctness for every output.** Acceptance
is authored before the transformation ships, never inferred after.
*Enforcement:* oracle-first development; fixtures precede fixes.

**J2 — Every judgment is typed** — computable, linguistic, or intent.
Mathematical definition is MANDATORY for computable judgments;
measurement protocols with thresholds for linguistic judgments; human
protocols for intent judgments. Misfiling a judgment's type is itself
an axiom violation. *Descent:* three rejected language-gates
(casebooks, typed grammar, quantifier lexicon) — attempts to
mathematically define linguistic judgment, each defeated by the
unenumerability of language. *Enforcement:* every judgment declares
its type at design review; the type dictates its stratum (§4).

**J3 — Coverage matches type.** Fixtures for the tested, suites with
paraphrase spread for the measured, recorded walk protocols for the
judged; every judgment has its cases, and every field failure becomes
a case before its fix ships (the real-corpses rule). *Enforcement:*
corpse-to-fixture discipline; suite scorecards persisted.

**J4 — Every transformation carries formal judgment.** No step ships
without its oracle: postconditions, count oracles, or a declared suite
family. *Descent:* the 5-of-13 undercount — a silent wrong answer
presented as complete, undetectable because no oracle pinned the
truth. *Enforcement:* count-oracle tests; postcondition gates.

### Group M — Mind (added by accepted ruling, 2026-08-21)

**M1 — The capability equation.** capability = model × context ×
loop-shape; a near-zero factor zeroes the product regardless of the
others. *Descent:* the refuted model-tier experiment — a stronger
model changed nothing inside an amnesiac harness; the one-mind merge
changed everything at the same model.

**M2 — One mind, full evidence.** A single conversation makes every
decision of a turn — what to do, whether results suffice, what the
answer is — with complete tool results persisting in its context.
Evidence degrades gracefully as the window fills; it is never
amputated per-call. *Descent:* the three amnesiac minds (planner /
goal-check / captioner passing 1,500-char stubs); anaphora flipping
0→1.00 on memory alone. *Enforcement:* prompt-capture tests assert
round-2 requests carry round-1's full results.

**M3 — Thinking room.** The mind may reason between actions; forced
immediate emission is legal only for form-fills (e.g. a final typed
verdict). *Descent:* composition lives in reasoning tokens; single-
shot JSON amputated it. *Enforcement:* captured request parameters.

**M4 — Free composition; no question-shaped control flow.** The mind
composes primitive operations freely; enumerated question shapes are
banned from prompts, gates, and tool names alike — pattern
predefinition is chance with extra steps. *Descent:* three disguises
of the same anti-pattern, each caught; the census gap (a missing
primitive shows up as a category error, not a prompt problem).
*Enforcement:* prompt line budgets; banned-vocabulary checks; pinned
prompt hashes; closed operation registry with data-shaped
justifications.

**M5 — The decision-typing rule.** Decisions bind to deciders by
type: computable → code, intent → human, linguistic → model. A
stochastic component may hold a decision only where its error mode is
visible and bounded; anything with a right answer computable from data
must be decided by a process that always gets it right. *Descent:* the
2026-08-09 agent failures (a stochastic generator owning retrieval);
the runtime pivot. *Enforcement:* replay determinism tests on
computable seats; AST planks banning LLM clients from deterministic
modules.

### Group B — Boundary (added by accepted ruling, 2026-08-21)

**B1 — No claim without a witness.** Every fact presented traces to
ground truth produced by a deterministic operation; the mind may
arrange and summarize evidence, never add to it. *Descent:* fabricated
filters and invented codes in generated descriptions; the unscoped
platform agent inventing a dataset. *Enforcement:* witnessed edges;
machine-verified evidence quotes; grounding gates.

**B2 — Honesty at the boundary, never in the interior.** Enforcement
lives where thought becomes action or answer — stamped provenance,
gates, typed verdicts — and nothing polices intermediate reasoning.
Constraining the interior buys safety by amputating cognition;
constraining the boundary buys safety and keeps the mind. *Descent:*
the whole arc: "safe but dumb" (interior constraint) versus "smart but
lying" (no constraint) versus the merge. *Enforcement:* headlines
rendered by code from result metadata; caption gates on final answers
only.

**B3 — Quantified claims are bounded by declared completeness.**
"All", "none", and counts are legal only over results whose
completeness is declared; incomplete evidence cannot source them.
Every operation declares whether its results are complete. *Descent:*
top-K search counts asserted as totals; the "6 metrics" truncation
lie. *Enforcement:* completeness declarations on every result set;
honesty gate floors over-claims.

**B4 — Irreversible acts confirm.** Reads may auto-continue within
bounded rounds; writes and outward actions always require human
confirmation; no autonomy mode exempts them. *Enforcement:* dispatch-
level whitelist (never prompt-level); plan-confirmation for writes.

### Group R — Residue & Ledger (added by accepted ruling, 2026-08-21)

**R1 — Conservation.** `handled ⊎ fallout = total` for every
transformation — no third bucket, anywhere, ever. *Descent:* 13,000
silently suppressed parse items; the conservation counter that turned
suppression into arithmetic. *Enforcement:* conservation equations
asserted per extractor; fallout rows landed, not logged.

**R2 — Drift fires mechanically.** When reality diverges from a
declaration, a mechanism fires — a red build, a checklist row, a
funnel bar. "Someone would notice" is the definition of a missing
feedback loop. *Descent:* STPA's lesson, lived twice (EMR joins, the
7% surface). *Enforcement:* registry closure checks in CI; dashboards
computed from state tables.

**R3 — Novelty escalates.** What neither code nor model can resolve
reaches a human with a name, a reason, and a place to mark it
handled; an empty checklist is a verified all-clear, not an absence of
news. *Enforcement:* terminal-state law on fallout
(`auto_resolved | escalated`, no NULL); the human checklist as a
query.

**R4 — The ledger.** Every interaction is an append-only event; all
aggregates are derived, never stored; the event log is the ground
truth from which governance, weights, and personal layers are
rebuilt. *Descent:* the purged in-place usage counter; the flywheel.
*Enforcement:* append-only contracts; recomputability tests.

## 3. The entry ritual (the three questions)

Every new artifact class answers, before its first line of code:

1. **Inventory** — the complete frontier, enumerated as data, with
   exclusion rows for everything deliberately outside (D1's shape).
2. **Conservation** — the equation proving nothing vanishes, and where
   fallout lands (R1's shape).
3. **Drift** — what mechanically fires when reality diverges (R2's
   shape).

The answers become registry rows; a design review that cannot cite
them does not proceed. Prior art: IEC 62304 / DO-178C traceability and
coverage analysis; STPA control-loop hazard analysis.

## 4. The verification strata

| Stratum | What | Epistemic type |
|---|---|---|
| L0 | contracts & kernels | tested — exact, CI |
| L1 | structure & information flow (prompt capture, AST, registry closure) | tested — exact, CI |
| L2 | behavior under a live model (suites, paraphrase spread) | measured — thresholds; honesty violations stop the build, they are never a metric |
| L3 | human acceptance (recorded walk protocols) | judged |

Laws: every capability declares its checks at every stratum before
shipping; never measure what you could test; never ask L3 eyes to
discover what L2 should have caught; L3 rejections become L2 cases
before their fixes ship.

## 5. The theorems (conditional guarantees)

- **T1 (no fabrication).** Under B1 + B2 + M2: a false statement has
  no constructible path to the user — the mind cannot copy an error
  from evidence it never sees, cannot exceed witnessed facts past the
  gate, and silence is counted, not invisible.
- **T2 (frontier completeness).** Under D1 + R1: the system is
  provably complete relative to its declared inventory, and the gap
  between built and declared is an enumerable list, never a surprise.
- **T3 (owned residue).** Under R1 + R2 + R3: nothing fails silently;
  every unresolved outcome has a human owner of record.
- **T4 (replay).** Under M5: every computable seat is
  replay-deterministic — same inputs, byte-identical outputs — so
  drift in the deterministic core is detectable by comparison.
- **T5 (typed-decision soundness).** Under M5 + J2: no computable
  decision ever rests on a stochastic decider, and no linguistic
  judgment is ever claimed as proven.

## 6. Honest limits

1. The framework cannot force conception: question 1 makes the
   frontier a finite reviewable list; a human must still review it.
2. Intelligence is measured, never proven (J2); a conforming system
   can be honest and unhelpful — the Measure exists to drive the
   second property, not to certify it.
3. Correlated model errors (a translator and verifier making mirror
   mistakes) are made rare by information-flow boundaries, not zero.
4. These axioms are themselves versioned and amendable — by recorded
   decision, loudly, like everything they govern.

## 7. The reference implementation's receipts

| Incident (documented) | Axiom it produced |
|---|---|
| Missing EMR join edges — undeclared frontier | D1, D4, the three questions |
| 7% ask-surface reachability — undecided invisibility | D1, R2 |
| Parser relapses (regex/sqlglot) under pressure | D2 |
| Fabricated filters & invented codes in descriptions | B1, the round-trip discipline |
| 5-of-13 undercount presented as complete | J4, B3 |
| Three amnesiac minds; the four-question dumb trail | M1–M4 |
| Model-tier experiment refuted (stronger amnesiac ≠ smarter) | M1 |
| Three rejected language-gates | J2, M4 |
| 13k silent parse suppressions | R1 |
| In-place usage counters purged | R4 |
| One-mind merge: suite 0.17 → near-sweep in one day, honesty 1.00 throughout | T1–T5, demonstrated |
| Round-laziness variance (scores bouncing 0.83/0.67/0.50 on identical code) — a computable continuation decision resting on a stochastic decider; moved to code, variance gone | M5, first live diagnostic use |
| Humble-but-blind residual — the mind declining a hop to evidence it was pointed at; resolved by materializing decision evidence inline on the metric record (zero prompt machinery; anaphora ≥ bar, stamp-contradiction telemetry 0 across consecutive runs). Two corpses en route: the exhausted-turn verdict lie and the anchorless bridge synthesis, both caged | M2 typed and measured; the M5 fix's boundary holes convicted by the ratified honesty line |

The reference implementation's specification (`SPEC.md`), methodology
(`METHODOLOGY.md`, Operations Are the Product), and suite scorecards
are the framework's evidence base: every axiom above has a scar or a
proof, and the dates are in the ADRs.
