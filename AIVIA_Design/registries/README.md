# Registries — code-consumed data (Design-to-Code step 2)

The seven design registries as stamped JSON, converted 2026-09-05 from
the `_DRAFT.xlsx` workbooks by `convert_from_xlsx.py` (deterministic —
no hand-typed content; rerunning is byte-identical). These files are
what `graph/metamodel.py` and the lens/flow registries load at build;
code and tests consume THESE, never the doc's prose.

**Status: converted, NOT yet ratified.** Every stamp says
`ratified: false`. The ratification pass (Sunny) flips it per registry
after reviewing the conversion log below.

## Conversion log

- **Transcribed:** every sheet, verbatim, keyed by its header row.
- **Rulings applied at conversion** (recorded verdicts the DRAFTs
  predated — each cited inline in the JSON):
  - kg1_technical: grain OPEN→opportunistic (doc 09-04 + D11);
    contains-direction note replaced by the ratified two-part
    convention (doc 09-05 + D13).
  - kg3_artifacts: usage `asked` carries outcome, no about on
    no-match (H5).
  - lenses: three catalog rows added — referenced-keys (D12),
    correspondence (H7, deferred from v1), demand (H5, deferred
    from v1) — reads/yields from the L2 Code Structure Map.
- **All conversion flags RULED 2026-09-05** (Sunny, adopting the
  draft reads) and landed the same day:
  - RG-1: comparison-op AND quantifier are predicate-node
    PROPERTIES, never roles — roles stay a pure edge vocabulary;
    the Roles sheet's quantifier row retired.
  - kg2_logic gains the `Scope_Identity` sheet: A3 name-key model
    (`file::name` / `file::name#i`, counted retirement branch),
    A11 `::delivery` emitters, A4 attachment domain — transcribed
    from the doc's Disambiguation models + register A11.
  - lenses Catalog_v1 gains the `v1` flag column — the registry's
    flag is the authority; the doc's prose lens-count retired
    (doc sentence amended same ruling).
  - flows gains `Rules_to_Checks`: row per check, all 24 flow
    checks (PROD/APPR/LAND/MATCH/GRND/GEN) with doc-transcribed
    rules; inward rows carry their deferral inline.
  Every registry's `_open` is now empty; PM-1..PM-4 are ruled in
  the Port Manifest the same day.

## Validation

`validate_registries.py` — the embryo of binding mechanisms (a) and
(b): stamp discipline, rule-to-check closure, check-name uniqueness,
closed vocabularies, cross-registry kind agreement. Currently 6 rules
green; the doc-stamp compare is NOT-RUNNABLE until the design doc's
sections carry version stamps (Sunny action).

## Law

The xlsx workbooks remain the drafting record; on ratification these
JSON files become the single source and the workbooks retire. Until
then, any xlsx edit requires rerunning the converter — divergence
between the two is a defect, and the converter is the arbiter.
