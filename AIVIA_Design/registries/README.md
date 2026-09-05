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
- **Open flags** (undecided, filed in each file's `_open`):
  - kg2_kind_library RG-1: QUANTIFIED_COMPARE's `comparison-op` role
    is undefined in the Roles sheet — role vs property, Sunny rules.
    (Caught by the validator; declared exception until ruled.)
  - kg2_logic: A3/A4/A11 scope-identity rulings not yet restated as
    registry rows.
  - lenses: the v1 "eleven lenses" count vs catalog granularity.
  - flows: whether flow rules get row-per-rule treatment at
    ratification.

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
