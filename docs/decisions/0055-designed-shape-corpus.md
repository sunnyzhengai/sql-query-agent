# ADR 0055 — The designed shape corpus: spec-derived test data

**Status:** ACCEPTED 2026-08-24 — dimensions RATIFIED by Sunny as
proposed; BOTH phases authorized for immediate build; the shape
cohort IS demo-eligible (Sunny's ruling, reversing the skeleton's
recommendation): designed shapes give clean, falsifiable demo
results ("we planted these sins; it found exactly these") that the
messy realism corpus cannot. Demo-eligibility adds a generator
requirement: a coherent, readable business domain rendered via a
SWAPPABLE NAME PALETTE (cell logic is domain-independent; the domain
is a skin). Palette RULED by Sunny 2026-08-24: DIABETIC DIAGNOSIS
cohort analytics (retail vetoed; SaaS superseded). Never abstract
TBL_A/TBL_B names.

## Context

The behavior suite is corpse-driven and the 28-file demo cohort is a
FOUND corpus — superb realism, unaudited coverage. Every recent
field find maps to a cell of an enumerable relationship space the
corpus was never checked against: Base_Pop (same name × different
logic × proc-local), the blend misname (cousin tokens across two
families), the W13 resolver holes (aliased reference,
temp-projection reference). The ADR 0054 taxonomy already
partitions (name × logic × scope) — this ADR generates test data
from that model. Method: category-partition / model-based test
design, run under the project's own conservation discipline.

## Principles

1. **Two cohorts, two jobs.** The 28 real files stay untouched — the
   REALISM cohort (parser depth, scale, mess). The new SHAPE corpus
   is synthetic, minimal, one-cell-per-file(-pair) — the COVERAGE
   cohort. Neither substitutes for the other.
2. **Generated with its oracle.** One shape definition emits BOTH
   the SQL and the expected outcomes (flags, edges, compare
   verdicts, lineage rows). Oracles true by construction —
   store-derivation and manual verification not needed.
3. **Total or lying, applied to test data.** Every matrix cell is
   instantiated ⊎ excluded-with-reason; CI asserts totality (the
   reachability-contract pattern). A cell cannot be silently
   uncovered.
4. **Echo Law endgame.** Every future field find names its cell:
   covered cell → coverage bug; missing cell → the matrix grows and
   that growth IS the recorded mechanism. Walks become audit of
   last resort, not discovery of first resort.
5. **Disclosed boundary cells.** Where detection is provably beyond
   the machinery, the cell's expectation is honest disclosure, not
   detection (see D2 below). Proof where proof exists; disclosure
   where it doesn't (METHODOLOGY's asymmetry).

## Dimensions (RATIFIED; D7 added and ratified 2026-08-25)

- **D1 name relation** (pairwise): identical · cousin
  (token-overlap) · disjoint.
- **D2 logic relation**: hash-identical · whitespace/case-only
  (must normalize to IDENTICAL) · semantically-same-syntactically-
  different (**disclosed boundary cell**: verdict must say "differs
  by normalized hash," never claim semantic difference — semantic
  equivalence is undecidable) · genuinely different.
- **D3 scope**: CTE · temp table · schema table/view · proc ·
  business name (metric).
- **D4 reference form** (column/table refs): direct-qualified ·
  aliased · through temp-table projection · unqualified-unique ·
  unqualified-ambiguous (drop-bucket cell) · wrong-kind (metric/
  report id where a table is expected).
- **D5 chain shape**: linear A→B→C · diamond · self-reference ·
  cross-schema twin pair (reporting./reports.).
- **D7 grain** (RATIFIED 2026-08-25): patient-distinct ·
  encounter-grain · event-grain — what one output row represents;
  machine-detectable (DISTINCT on patient key). The
  same-name-different-grain fight (890 patients vs 1,200
  encounters).
- **D6 hygiene/edge** (excluded-or-instantiated per reason): dynamic
  SQL · multi-statement · \r\n forms · PHI-shaped literals (gate
  must redact).

## Deliverables

1. `data/shapes/` generator (deterministic, spec:E2) → SQL files +
   `shape_manifest.json` (cell id, files, expected flags/edges/
   verdicts).
2. Matrix registry (the 0052 pattern): every cell instantiated or
   excluded-with-reason; CI totality test.
3. Suite family `shapes`: pipeline over the shape corpus → assert
   manifest expectations end-to-end (parse → graph → sweep → ask).
4. Walk addendum: field finds cite their cell id.

## Phasing [RATIFY]

- BOTH phases authorized 2026-08-24 (Sunny): Phase 1 = D1×D2×D3
  pair shapes + D4; Phase 2 = D5, D6, property-based generator.
  Built in that order, one overnight run.

## Rulings (Sunny, 2026-08-24)

1. Dimension set RATIFIED as proposed (D1–D6).
2. Both phases authorized, built overnight.
3. Shape cohort IS demo-eligible — with the isolation constraint:
   the 28-file realism store and every existing oracle remain
   UNTOUCHED; shapes load as an isolated source/catalog the demo
   can switch to.
4. Domain RULED (Sunny): DIABETIC DIAGNOSIS. Rationale: diabetes
   is identified via MULTIPLE legitimate paths (ICD codes, HbA1c
   lab thresholds, medication lists, problem-list entries) — so
   same-concept-different-logic instances are clinically REAL, not
   contrived; the shape matrix doubles as the governed-plurality
   story (variants per path, steward certifies the official).
   Fully synthetic data; palette swappable by construction.
