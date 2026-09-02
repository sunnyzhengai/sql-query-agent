# Axiom crosswalk — framework ↔ specification

<!-- TIER: BLUEPRINT — component key: crosswalk
     src/trace_registry.py ARCHITECTURE_COMPONENTS
     Enforced by tests/test_trace_registry.py hierarchy checks. -->

> **Blueprint tier.** This file satisfies axiom group **axm:S**
> (Specification) from [AI_VIA_AXIOMS.md](../AI_VIA_AXIOMS.md). It is
> the bridge between the two axiom systems — the artifact that makes
> "does SPEC descend from the framework?" a checkable question instead
> of an assertion.

**Audited 2026-09-01.** The two systems were correlated only by claim
until this file: `AI_VIA_AXIOMS.md` named SPEC.md as its proof, and
SPEC.md never cited the framework at all. This crosswalk states the
correspondence axiom by axiom and, more importantly, names where it
**fails**.

## The relationship, honestly stated

They are **not** two views of one thing, and the mapping is **not**
a bijection:

- **`AI_VIA_AXIOMS.md` is general.** 24 axioms about how *any* agentic
  system should be built. It is portable — nothing in it is specific to
  SQL, Fabric, or healthcare.
- **`SPEC.md` (Φ_AIVIA) is particular.** 48 axioms about *this*
  codebase, each binding to a mechanical check over these tables and
  these modules.

So the correct reading is **framework = law, spec = law applied here**.
One framework axiom can spawn several spec axioms (`axm:D2` "no
transformation defined twice" becomes `spec:A1`, `A3`, `G1`, `G2`,
`G3` — five different mechanisms for one principle). That is expected
and healthy: the spec is where a general principle acquires teeth.

## What "every entry" covers — and what it doesn't

**Scope, stated before the tables so nobody over-reads them.** The
crosswalk maps SPEC's **48 numbered axioms**. SPEC.md also contains
normative content that carries no axiom ID, and that content is **not**
covered by the checks below:

| Section | What it is | Traced? |
|---|---|---|
| §3b — the design-review clause | Three questions every new artifact class MUST answer before its first line of code | **Not by ID.** Its substance is `axm:D1` (inventory), `axm:R1` (conservation), `axm:R2` (drift) — and `spec:L3` now makes the drift question an axiom. The clause itself is a *ritual*, enforced by review, not a checkable sentence. |
| §7 — the graph identity theorem | `G = ⋃ F_k(handled_k)` — derived from B1 + C1 + C3 | **Yes, transitively.** A theorem, not an axiom: it inherits its parents from the axioms it is proved from. |
| §13 — the double-sided function | `κ(ρ(τ(t))) = κ(t)`, labelled "**THE LAW**" | **Yes, since 2026-09-01** — PROMOTED to **Group T** by ADR 0065 (T0 the law, T1–T3 the instances). Was the clearest un-numbered law: only instance 1 had an id, so the crosswalk covered a third of a section calling itself THE LAW. |
| §14b — the admin Σ-structure | A second model of the same groups | **Yes, by inheritance** — it explicitly carries over B1, C1, D3, H. |
| §14d — testing strata | L0–L3 verification levels | **Not by ID** — it is where `axm:J3` lands (recorded as meta). |

So the precise claim is: **every numbered axiom traces up; what remains
un-numbered is deliberately so.** After ADR 0065 promoted §13 to Group
T, exactly two sections carry normative weight without an id, and both
are correctly ritual rather than law: §3b (the design-review clause —
three questions a human answers at review, enforced by refusing to
proceed) and §14d (testing strata — where `axm:J3` lands). Neither can
become a checkable sentence without becoming something it isn't.

## Direction 1 — does every numbered SPEC axiom trace up? **Yes, all 48.**

| SPEC | Framework parent | Note |
|---|---|---|
| A1, A3 | axm:D2 | one folding rule, one definition |
| A2 | axm:D3 | identity ⇒ exactly one owner per metric |
| B1 | axm:B1 | witness totality *is* "no claim without a witness" |
| B2 | axm:B1, axm:J4 | provenance closed ⇒ every description judged |
| C1 | axm:D1 | the enumerated frontier ⇒ nothing unreachable |
| C2, C3 | axm:R1 | `handled ⊎ fallout = total` |
| C4 | axm:R1, axm:D1 | leaf grounding: termination + reachability |
| D1 | axm:D4 | closure = shape-defined derivation |
| D2 | axm:J1 | count oracles = founder-defined correctness |
| D3 | axm:D3 | projections have one owning record |
| E1 | axm:S3 | the path space is data-shaped, hence enumerable |
| E2 | axm:J2 | replay determinism = the computable type |
| E3 | axm:M5, axm:J2 | the decision-typing rule, verbatim |
| E4 | axm:M5 | intent decisions bind to the human |
| E5 | axm:B1 | filter values need witnesses |
| E6 | axm:B2, axm:B3 | boundary honesty + bounded quantified claims |
| F | axm:J4 | the round trip is the description's oracle |
| G1, G2, G3 | axm:D2 | one owner per capability, mechanized |
| H1, H2 | axm:R3 | novelty escalates |
| L1 | axm:R4 | the ledger may only grow |
| L2 | axm:R4, axm:D3 | aggregates derived, never stored |
| L3 | axm:R2 | every declaration has a firing mechanism |
| T0 | axm:J4 | the round-trip law: κ(ρ(τ(t))) = κ(t) |
| T1 | axm:J4 | descriptions — blind verifier + κ-diff (ENFORCED) |
| T2 | axm:J4, axm:B1 | SQL stitching — parseability round-trips; κ-diff is the stated gap |
| T3 | axm:M5, axm:J2 | definition creation — the human is the judge (JUDGED, L3) |
| P1, P2 | axm:M2 | one mind, full evidence |
| P3 | axm:M3 | thinking room |
| P4 | axm:M4 | no question-shaped control flow |
| P5 | axm:B2 | honesty at the boundary, never the interior |
| P6 | axm:M1 | failure as observation = loop-shape capability |
| Q1 | axm:D1 | accounted connectivity ⇒ nothing unreachable |
| Q2 | axm:B1 | every edge provenance-mapped |
| Q3 | axm:B3 | completeness claims are conservation equations |
| R1 | axm:M4, axm:M5 | parse-never-generate: free composition + typing |
| R2 | axm:M4 | no question types |
| R3 | axm:B4 | irreversible acts confirm — applied to interpretation |
| R4 | axm:R3 | no dead ends ⇒ novelty escalates |
| R5 | axm:B3 | certain answers = bounded claims under ambiguity |
| R6 | axm:B2 | rows never enter model context |
| R7 | axm:B4 | confirmed-only execution |
| R8 | axm:B3 | machine-labelled sampling |

**No orphans.** Every spec axiom descends from at least one framework
axiom, which is the property that matters most: this codebase asserts
no law the framework doesn't authorize.

## Direction 2 — does every framework axiom reach down? **Yes, but for 3 meta-axioms.**

*(At first audit this read "No — 5 of 24 don't." Two of those five were
real gaps and were closed the same day by ADR 0064; the three below
cannot be closed by construction.)*

### (a) Meta-axioms — unmappable by construction (3)

These are laws *about having a specification*, so a spec axiom
implementing them would be circular. SPEC satisfies them by
**existing and being maintained**, not by containing a sentence.

| Axiom | Why it cannot map | Where it is actually satisfied |
|---|---|---|
| **axm:S1** — the world has a formal specification | SPEC.md *is* the Φ this axiom demands | The file's existence + `G ⊨ Φ` framing in §1/§14 |
| **axm:S2** — the founder defines the states; spec outranks code | A rule about amendment authority, not system state | SPEC §16 change discipline: axiom changes require an ADR |
| **axm:J3** — coverage matches type | A rule about how to test, not what holds | SPEC §14d testing strata (L0–L3) |

### (b) Genuine gaps — CLOSED 2026-09-01 by ADR 0064

The audit originally found two. Both are now closed by **SPEC Group L**
(§14h), so Direction 2 holds: every non-meta framework axiom reaches a
spec axiom.

| Was | Closed by | Status |
|---|---|---|
| **axm:R2** — drift fires mechanically | **spec:L3** — every declaration has a firing mechanism | ENFORCED by citation (the seven registry closure checks, the funnel, reachability — the ADR 0059 Q3 precedent: the equations predated the axiom) |
| **axm:R4** — the ledger (append-only; aggregates derived, never stored) | **spec:L1** (append-only declared AND obeyed) + **spec:L2** (aggregates derived, never stored) | ENFORCED — `tests/test_ledger_contract.py`, four checks |

**Why this mattered.** SPEC §1 claims the spec is **closed** — "an
absence is visible as a gap in a finite list, not as a surprise found by
reading code." A law that code enforces but the spec never states is
exactly the failure that claim promises to prevent. Both were live
counterexamples; the claim is true again.

**What the closure actually cost.** L3 was free — the mechanisms
existed and only needed naming. L1 required a real check: `write_mode`
had been a *declaration nothing verified* since the beginning (39
overwrite / 10 append, label legality checked, obedience never). L2
pinned the purged UsageTracker as a regression fixture, which had no
guard at all.

**One design correction worth remembering.** ADR 0064's draft proposed
an AST check over `src/` — which would have scanned an empty set and
reported green forever, because **`src/` contains no Delta writes**.
They live in `*.Notebook/notebook-content.py`. A check must be proven
against an injected violation before it is trusted; see ADR 0064 §6b
for the verification record.

## How to keep this true

`tests/test_axiom_crosswalk.py` enforces:

1. every spec axiom id in this table exists in `SPEC_AXIOMS`;
2. every framework parent exists in `AXM_AXIOMS`;
3. every spec axiom appears — a new one without a parent fails CI;
4. every framework axiom is either mapped or listed above as meta/gap
   with a reason.

So the crosswalk cannot silently rot: adding an axiom to either
document forces an entry here.
