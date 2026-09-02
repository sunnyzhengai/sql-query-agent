# ADR 0068 — The landing matrix as data (ratchet turn 2)

**Status:** ACCEPTED 2026-09-02 — Sunny's order ("do the next ratchet
turn on DECISION_LANDING_MATRIX"), executing ADR 0067.

## Decision

`src/landing_registry.py` (ninth peer registry) holds the decision
landing matrix as records: the four workflow rules, the zero-schema-
footprint principles, the OUTBOX schema and outcome vocabulary, and
one record per governance action with its per-tool landings, grade,
and what stays home. `DECISION_LANDING_MATRIX.md` is now the
**generated projection** — the registry is the truth.

ADR 0063 §3's two invariants, prose until now, are mechanized
(`tests/test_landing_registry.py`): **no action without a landing**
(every record lands in each tool or is explicitly own-only) and
**no landing without a grade**. Plus: closed support vocabulary
(`[native]/[config]/[absent]` — no third state left implicit), closed
outcome vocabulary, and the four rules pinned at four (changing their
number is an ADR, not an edit).

## Two constraints the turn surfaced

1. **Brand neutrality.** The matrix's attribution prefix contains the
   product name, and the core bans brand strings — so the registry
   stores the `{product}` template, deployment-rendered via
   `src/branding.py`.
2. **Determinism.** `product_name()` reads an env var; a committed
   generated artifact must be replay-identical everywhere, so the
   generator uses `DEFAULT_PRODUCT_NAME` and shows the attribution
   template raw. Proven: generation is byte-identical under a
   `SQA_PRODUCT_NAME` override.

## Content status — carried, not changed

The source document was DRAFT v3: Sunny's four rulings (2026-08-31 —
hierarchy over official/sibling; approval in the customer's DG
workflow; no sync, the OUTBOX; zero schema footprint) are RULED; the
matrix as a whole awaits Bridge-build ratification. Conversion to data
changes the FORM, not the status; the generated doc says so. The
rulings' rationale lives here and in the git history of the prose
version, per the 0067 invariant.

## Relations

0067 (the ratchet), 0063 §3 (the invariants now mechanized), 0057/
0066 (the landing component's blueprint lineage).
