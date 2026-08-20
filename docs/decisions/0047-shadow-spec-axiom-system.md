# 0047 — The shadow specification: Φ_AIVIA as the standing instrument against design drift

**Status:** Accepted (adopted from the review session's handoff, 2026-08-19)
**Date:** 2026-08-19

## Context

Three recurring deviation classes were discovered by code-walking instead
of by a failing check: (1) the technical layer silently wasn't the vendor's
complete join map (recovered 1.27.0/1.28.0); (2) LLM components repeatedly
drifted into retrieval/query decisions until ADR 0046 settled it; (3)
collaborators defaulted back to regex/sqlglot after ScriptDom was settled
(closed by the ADR 0001 total law, 1.28.0). Sunny asked the review session
for a way to stop design-vs-code drift *mathematically*; the answer is
[`docs/architecture/SPEC.md`](../architecture/SPEC.md) — a signature Σ and
axiom groups A–H in which each incident class becomes a named, checkable
axiom violation.

## Decision

1. **SPEC.md is adopted** as the shadow design: the theory the system is a
   model of. Correctness is one judgment, split across two model checkers:
   the validation gate checks `G ⊨ Φ_data` (per run, over the Delta
   instance); CI checks `Code ⊨ Φ_code` (per commit, over the AST and
   recorded fixtures).
2. **Every axiom binds to a mechanical check** (the 0042/0044 doctrine).
   The status vocabulary is ENFORCED / GATED / PARTIAL / UNBOUND; an
   UNBOUND axiom older than one release cycle is drift in the spec itself.
3. **Enforcement homes shipped with this ADR (1.29.0):**
   - `src/extraction_registry.py` + `tests/test_extraction_registry.py` —
     spec:C1, the completeness frontier (functor XOR exclusion per source
     kind; the missing-joins incident pinned as its acceptance test;
     Snowflake/Databricks exclusions per Sunny's ruling).
   - `ORIGIN` column on `input_dict_tables` — the T_org vehicle
     (spec:C4/E5 dependency): vendor|org, NULL = vendor.
   - `src/governance/leaf_grounding.py` + 500 wiring — spec:C4 as a
     computed per-file verdict (`completely_parsed ⟺ every leaf ∈ T_D ∪
     T_org`), fallout stage `500_leaf_grounding`, escalated per ADR 0045.
   - `src/capability_registry.py` + `tests/test_capability_registry.py` —
     spec:G1–G3 (one owner per capability; `Uses ∖ S = ∅` over src/;
     banned parsers ownerless forever).
   - `tests/test_spec_gates.py` — strict-xfail exit gates for E1/E5
     (land with the 0046 engine).
   - A1 idempotence property test (the audit found its citation missing).
4. **The amendment rule**: changing an axiom requires an ADR; flipping a
   status label requires only the check's file citation, recorded in
   SPEC.md's changelog. Tightening an axiom that governs generated
   artifacts revs the relevant `*_CONTRACT_VERSION` cache keys.
5. **Adversarial audit findings folded into v0.3** (the audit is part of
   adoption, not a formality): A1 overclaimed ENFORCED (no idempotence
   test existed — now it does); E6 stated no gap while its
   probability-vocabulary ban was prompt-text only; Σ/D3 described Term
   projection as current — Term nodes and `implements` edges do NOT exist
   yet (gov record + mining do), recorded as an EXTRACTION_REGISTRY
   exclusion until the projection builder lands.

## Consequences

- Drift is now a named violation with a citation (`⊭ spec:C1 — source
  kind k has no functor and no exclusion`), never a code-walk discovery.
- Architecture debates that recur terminate at an axiom id (LLM composing
  retrieval → violates spec:E2) instead of re-litigating.
- The registries now number five: TABLE / NOTEBOOK / SHAPE / EXTRACTION /
  CAPABILITY — each one converting a class of silent drift into a
  one-page review with CI teeth.
- Cost accepted: every new source kind, capability, or axiom is friction
  by design — the row/ADR IS the review.
