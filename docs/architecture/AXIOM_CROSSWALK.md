<!-- GENERATED FILE — do not edit.
     Sources: src/spec_registry.py (mappings + notes),
     src/trace_registry.py (AXM_UNMAPPED, grounding ADRs).
     Regenerate: python scripts/generate_docs.py
     CI fails if stale (tests/test_axiom_crosswalk.py). -->

<!-- TIER: BLUEPRINT — component key: crosswalk
     src/trace_registry.py ARCHITECTURE_COMPONENTS -->

# Axiom crosswalk — framework ↔ specification

The bridge between the two axiom systems, generated from the ledger
(ADR 0072; first audited by hand 2026-09-01, when the two systems were
correlated only by claim). **Framework = law; spec = law applied
here.** Not a bijection by design: one framework axiom legitimately
spawns several spec axioms (axm:D2 becomes five mechanisms). The two
id spaces collide on group letters B, D and R — always prefix
(`axm:` vs `spec:`).

**Scope:** the crosswalk maps SPEC's 48 NUMBERED axioms. SPEC's
remaining un-numbered normative prose is deliberately so: §3b (the
design-review ritual — humans answer it at review) and §14d (testing
strata — where axm:J3 lands). §13 was the exception and was promoted
to Group T (ADR 0065); the two one-time gaps (axm:R2, axm:R4) were
closed by Group L (ADR 0064).

## Direction 1 — every numbered spec axiom traces up (48/48)

Groups: A=Identity · B=Soundness · C=Completeness · D=Derived structure · E=Ask-time determinism · F=The round trip · G=Mechanism uniqueness · H=Escalation · L=The ledger · P=The one-mind turn · Q=Graph topology · R=Ask-time interpretation + run boundary · T=The double-sided function

| Spec axiom | Title | Framework parent(s) | Why | Grounding ADR(s) |
|---|---|---|---|---|
| spec:A1 | folding is idempotent | axm:D2 | one folding rule, one definition | 0016 |
| spec:A2 | metric_id is a key | axm:D3 | identity -> exactly one owner per metric | 0015 |
| spec:A3 | fold-collisions are rejected loudly | axm:D2 | one folding rule, one definition | 0016 |
| spec:B1 | witness totality (the anti-fabrication axiom) | axm:B1 | witness totality IS 'no claim without a witness' | 0005, 0044, 0048 |
| spec:B2 | description provenance is total and closed | axm:B1, axm:J4 | provenance closed -> every description judged | 0044 |
| spec:C1 | the frontier is enumerated (no undeclared source kind) | axm:D1 | the enumerated frontier -> nothing unreachable | 0001, 0048, 0052, 0053, 0054 |
| spec:C2 | conservation per extractor (no third bucket) | axm:R1 | handled + fallout = total (conservation) | 0041, 0044, 0045, 0053 |
| spec:C3 | images land in the graph | axm:R1 | handled + fallout = total (conservation) | 0039, 0042 |
| spec:C4 | leaf grounding (the termination axiom) | axm:R1, axm:D1 | leaf grounding: termination + reachability | 0014, 0047 |
| spec:D1 | materialized closures equal the fixpoint | axm:D4 | closure = shape-defined derivation | 0037 |
| spec:D2 | count oracles | axm:J1 | count oracles = founder-defined correctness | 0018 |
| spec:D3 | projections are functions of the record | axm:D3 | projections have one owning record | 0033, 0048 |
| spec:E1 | the path space is finite and enumerable | axm:S3 | the path space is data-shaped, hence enumerable | 0046 |
| spec:E2 | replay determinism for retrieval components | axm:J2 | replay determinism = the computable type | 0032, 0054, 0055 |
| spec:E3 | the decision typing rule (which decider is legal where) | axm:M5, axm:J2 | the decision-typing rule, verbatim | 0035, 0050, 0051 |
| spec:E4 | pick containment (the human picks, structurally) | axm:M5 | intent decisions bind to the human | 0044, 0046 |
| spec:E5 | filter grounding (the 123/456 lesson) | axm:B1 | filter values need witnesses | 0044, 0046 |
| spec:E6 | presentation honesty | axm:B2, axm:B3 | boundary honesty + bounded quantified claims | 0036, 0044, 0051 |
| spec:F | the round trip (ADR 0044 as equations) | axm:J4 | the round trip is the description's oracle | 0044 |
| spec:G1 | one owner per capability | axm:D2 | one owner per capability, mechanized | 0047 |
| spec:G2 | sanctioned powers only (import-graph inclusion) | axm:D2 | one owner per capability, mechanized | 0001, 0047 |
| spec:G3 | no undeclared power | axm:D2 | one owner per capability, mechanized | 0047 |
| spec:H1 | fallout resolution is total and closed | axm:R3 | novelty escalates | 0045 |
| spec:H2 | novelty always escalates | axm:R3 | novelty escalates | 0045, 0048 |
| spec:L1 | append-only is declared AND obeyed | axm:R4 | the ledger may only grow | 0064 |
| spec:L2 | aggregates are derived, never stored | axm:R4, axm:D3 | aggregates derived, never stored | 0064 |
| spec:L3 | every declaration has a firing mechanism | axm:R2 | every declaration has a firing mechanism | 0064 |
| spec:P1 | one conversation decides a turn; no separate planner/judge/c | axm:M2 | one mind, full evidence | 0051 |
| spec:P2 | full tool results enter the SAME history and persist across  | axm:M2 | one mind, full evidence | 0051 |
| spec:P3 | thinking room — no forced tool_choice except the final typed | axm:M3 | thinking room | 0051 |
| spec:P4 | no question-family casebook anywhere — invariants + tool sem | axm:M4 | no question-shaped control flow | 0051 |
| spec:P5 | honesty at the boundary only | axm:B2 | honesty at the boundary, never the interior | 0051 |
| spec:P6 | failure is observation | axm:M1 | failure as observation = loop-shape capability | 0051 |
| spec:Q1 | accounted connectivity | axm:D1 | accounted connectivity -> nothing unreachable | 0059 |
| spec:Q2 | edge soundness | axm:B1 | every edge provenance-mapped | 0059 |
| spec:Q3 | relative completeness | axm:B3 | completeness claims are conservation equations | 0059 |
| spec:R1 | Parse, never generate | axm:M4, axm:M5 | parse-never-generate: free composition + typing | 0060 |
| spec:R2 | No question types | axm:M4 | no question types | 0062 |
| spec:R3 | Interpretation confirms before it executes | axm:B4 | irreversible acts confirm - applied to interpretation | 0060, 0062 |
| spec:R4 | No dead ends | axm:R3 | no dead ends -> novelty escalates | 0062 |
| spec:R5 | Certain answers | axm:B3 | certain answers = bounded claims under ambiguity | 0062 |
| spec:R6 | Rows never enter model context | axm:B2 | rows never enter model context | 0061 |
| spec:R7 | Nothing is generated; the confirmed SQL is what runs | axm:B4 | confirmed-only execution | 0061 |
| spec:R8 | Sampling is machine-labelled | axm:B3 | machine-labelled sampling | 0061 |
| spec:T0 | the round-trip law | axm:J4 | the round-trip law: kappa(rho(tau(t))) = kappa(t) | 0065 |
| spec:T1 | Descriptions | axm:J4 | descriptions - blind verifier + kappa-diff | 0065 |
| spec:T2 | SQL stitching | axm:J4, axm:B1 | SQL stitching - parseability round-trips; kappa-diff is the stated gap | 0065 |
| spec:T3 | Definition creation | axm:M5, axm:J2 | definition creation - the human is the judge (L3 stratum) | 0065 |

**No orphans:** this codebase asserts no law the framework does not
authorize — enforced, not asserted
(tests/test_axiom_crosswalk.py::test_every_spec_axiom_has_a_framework_parent).

## Direction 2 — every framework axiom reaches down, except 3 meta-axioms

Laws ABOUT having a specification cannot be implemented AS spec axioms
without circularity; SPEC satisfies them by existing and being kept:

| Axiom | Why it cannot map / where it is satisfied |
|---|---|
| **axm:S1** | SPEC.md IS the Phi this axiom demands |
| **axm:S2** | amendment authority; SPEC section 16 change discipline |
| **axm:J3** | how to test; SPEC section 14d testing strata |

Every other framework axiom is implemented by at least one spec axiom
(test_every_framework_axiom_is_mapped_or_explained). A new spec axiom
without a parent, or a framework axiom left silently unimplemented,
is a red build.
