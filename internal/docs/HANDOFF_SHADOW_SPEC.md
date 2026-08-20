# Handoff — the shadow specification (Φ_AIVIA): adopt, dispute, bind

**From:** review session, 2026-08-19. **To:** dev session.
**Artifact:** `docs/architecture/SPEC.md` v0.2 — read it first; this handoff
is the adoption order, not a substitute.

## What happened

Sunny asked the review session for a way to stop the recurring drift between
the design in her head and the codebase — mathematically. Three motivating
incidents, all discovered by code-walking instead of by a failing check:

1. **Missing EMR join edges** — the technical layer was not the vendor's
   complete join map (since recovered: 1.28.0 ships the native-derived join
   map, HANDOFF_TREE_PHASE_1B; the incident stands as the motivating example
   for axiom C1).
2. **LLM components drifting into retrieval/query decisions** — the debate
   re-litigated several times before ADR 0046 settled it.
3. **Regex/sqlglot relapses** after ScriptDom was settled (since closed:
   the total native-parser law, ADR 0001 amendment + deletion, 1.28.0).

The answer is a formal specification — signature Σ + axiom groups A–H — in
which each incident class becomes a *named, checkable axiom violation*
instead of a discovery. The doctrine is the house doctrine (0042/0044):
every axiom binds to a mechanical check; an axiom without one is labeled
UNBOUND and is a debt, never a guarantee. Validation gate = model checker
for the data axioms (`G ⊨ Φ_data`); CI = model checker for the code axioms
(`Code ⊨ Φ_code`).

v0.2 already incorporates a blind round-trip review: Sunny reconstructed the
system in her own words; mismatches became axioms C4 (leaf grounding), E5
(filter grounding), E6 (presentation honesty), D3 (projections are functions
of the record), the T_org sort, and §13 (the double-sided τ/ρ function).

## Verdicts already made (Sunny, 2026-08-19 — do not re-litigate)

1. **Layer vocabulary pinned to the codebase's names**: technical /
   transformation / canonical (= metrics) / consumption (reports+measures);
   business terms = governance record projected into the graph. SPEC.md §4
   is the one table everyone uses.
2. **"Confidence" is banned display vocabulary** — the disclosed signals are
   closeness (relative), derived usage weight, certification status (spec:E6,
   consistent with ADR 0032/0046).
3. **Dialect frontier**: Fabric-native for the v1 Marketplace offering.
   Snowflake views and Databricks/dbt models are **explicit exclusion rows**
   in the C1 inventory — visible roadmap pressure (Sunny notes hospital
   adoption of both is growing), not silent scope. Each future dialect gets
   its own native parser (ADR 0001).
4. **The spec direction itself is endorsed** — Sunny wants this as the
   standing instrument against design drift. Cite `spec:<axiom-id>` when an
   architecture debate recurs (e.g., LLM composing retrieval → "violates
   spec:E2").

## Scope (in order)

1. **Read SPEC.md v0.2 adversarially.** Dispute any status label that
   overclaims (ENFORCED/GATED/PARTIAL/UNBOUND, each with file citations).
   Corrections go in the spec file directly, version-bumped.
2. **EXTRACTION_REGISTRY (spec:C1)** — the highest-value proposal. One row
   per source kind: extractor entry point, target node/edge kinds,
   conservation query (`|dom| = handled + fallout`), or an explicit
   exclusion row. Peer of TABLE_REGISTRY / NOTEBOOK_REGISTRY /
   SHAPE_REGISTRY. Acceptance test: the registry, run against the pre-1.28.0
   state, would have flagged the missing join map as a red row. Seed the
   Snowflake/Databricks exclusions.
3. **T_org declaration vehicle (spec:C4, spec:E5 dependency)** — decide how
   org-created reference tables (value sets, control parameters) are
   declared (dictionary extension vs org_config section). Without the
   distinction, a legitimate org value-set leaf is indistinguishable from an
   unknown leaf, and leaf grounding cannot be computed.
4. **C4 leaf grounding as a computed verdict** — per parsed file:
   `completely_parsed(f) ⟺ every leaf ∈ T_D ∪ T_org (else counted fallout)`.
   Candidate home: the funnel + ops_fallout (stage naming per 0044/0045
   conventions). New honest number: fraction of files fully grounded.
5. **CAPABILITY_REGISTRY (spec:G1–G3)** — generalize
   `test_native_parser_law.py`'s pattern: capability → sole owner module →
   sanctioned primitives (regex, parsers, LLM clients, embedding calls,
   Delta writes); CI asserts import-graph inclusion (`Uses ∖ S = ∅`) over
   src/. Friction by design: adding a capability row IS the review.
6. **Record the axiom system as an ADR** — Context: the three incidents;
   Decision: SPEC.md + its enforcement homes + the amendment rule (axiom
   changes require an ADR; status flips require only a file citation).
7. **Bind or demote every UNBOUND axiom** — standing rule: an UNBOUND axiom
   older than one release cycle is drift in the spec itself.

## Notes for the reader

- The spec is deliberately bilingual: every formula carries a plain-language
  gloss, and §2 is a notation primer. The formula is the law; the gloss is
  the teaching aid.
- §13 (the double-sided function) is the unification Sunny cares most
  about: one law `κ(ρ(τ(t))) = κ(t)` instantiated three times (descriptions
  / SQL stitching / definition creation, with judges: deterministic diff /
  ScriptDom / the human), and Tier 2 = Tier 1 + exactly one arrow
  (compile∘execute) — ADR 0046's "Pro adds one layer" as a formula.
- The F→E4 dependency (spec:E4 note) is the formal reason 0044 precedes
  0046: the human picks by reading descriptions, so round-trip-verified
  descriptions are load-bearing for the pick.
- v0.2 already accounts for 1.28.0 (sqlglot deletion, ADR 0001 total law,
  native join map) — no stale asks.
