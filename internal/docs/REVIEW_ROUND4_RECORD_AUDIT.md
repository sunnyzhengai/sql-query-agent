# Review verdict — Round 4 record audit (2026-08-22)

**Verdict: the WIN stands; the RECORD needs three corrections before
anyone quotes it.** Machine table re-checked against the runner's own
oracle code and the certified catalog. The 13/13 vs 8/13 headline,
homegrown ≥ Fabric on every family, and the p50 comparison are all
confirmed by the scorecard table. The prose characterization around
it is wrong in ways a skeptical customer would catch in five minutes.

## Correction 1 — the miss list is wrong (record vs machine)

The goal-file entry (and the relay) characterizes Fabric's five
misses as: lineage(IP_SEPSIS), lineage(COMPILED_CONTEXT),
topical×2, anaphora. The machine table says otherwise:

- Row 14, lineage(IP_SEPSIS): Fabric **PASS** (22.03s).
- Row 11, bridge("how is Sepsis Case defined"): Fabric **miss** —
  it answered about Inpatient Sepsis Overview and named neither
  sibling. This miss is absent from the prose.

Actual five misses: bridge(Sepsis Case) · lineage(COMPILED_CONTEXT)
· topical(sepsis count) · topical(ED) · anaphora#1(protocol). The
8/13 total is unchanged; the characterization must match the table.

## Correction 2 — "names that don't exist in the catalog" is FALSE

Every name Fabric listed for IP_SEPSIS readers is a real certified
metric (data/demo/input_metric_names.csv): Sepsis Shift Compliance,
Sepsis Shift Compliance Metrics, Sepsis Case Encounters, Sepsis
Patient Timeline (Legacy v1), Sepsis Encounters by Location (Legacy
v1). Nothing was invented. The actual defect: **4 of the 5 are not
readers of IP_SEPSIS** — the store's parsed-lineage reader set is
Bundle Compliance Metrics / Bundle Compliance by Shift / Case
Details / Case Encounters / Screening Tool Results. Fabric answered
lineage by NAME ASSOCIATION across the corpus's deliberate
name-cousins — the same substring/cousin disease the homegrown
lineage op was cured of in 1.56.1 (exact-table scoping; the corpus
has 4 IP_SEPSIS name-cousin tables precisely to expose this).

This is a STRONGER product claim than invention, and it is
defensible: "Fabric associates names; AIVIA reads parsed edges."
The invention claim would detonate on first customer inspection —
the names are in the catalog they'd check.

## Correction 3 — the PASS on row 14 needs a footnote

The table_readers oracle passes on 2-of-5 name overlap
(required_overlap = min(2, len)). Fabric's list is 1-correct in the
truncated view, so the ≥2 hits that produced PASS must sit in the
untruncated tail — either way, a mostly-wrong reader list cleared
the facts bar. Acceptable for a coarse cross-surface ruler, but the
scorecard should say so where the row is quoted; otherwise 8/13
silently credits an answer whose list is 4/5 wrong. (Same class as
the already-recorded honesty-ruler asymmetry: the coarse rulers cut
Fabric slack in BOTH columns, which strengthens, not weakens, the
homegrown result — say that explicitly.)

## Goal-criteria honesty (record; amendments are Sunny's)

- **Criterion 4 NOT MET as written**: "homegrown p50 under 3s" —
  Round 4 p50 is 15.6s. The advantage was consciously spent by the
  one-mind engine (LLM rounds bought reach + typed honesty), and
  homegrown still beats Fabric's 21.1s — but the goal file must
  record the criterion as unmet-and-why or amended, not stay silent.
- **Criterion 1 partially unmet**: drilldown sits at 0.33 (1.56.1)
  under the find-1 grain gate, which post-dates the criterion.
  Record as superseded-by-tightening or unmet; don't leave the
  "closed" entry implying all four criteria cleared.

## Confirmed sound

- Anaphora protocol caveat properly on the record (adapter has no
  session; clarification scored miss, stated).
- Routing inconsistency claim survives correction 2: the scripted
  run's reader list ≠ the UI run's correct 5 for the same question.
- Oracle derivation store-side, no hardcoded answers; grade_fabric
  and grade share required-facts logic.

PARKED (Sunny): any Marketplace-facing phrasing of the Round-4
result — with the note that "honest but shallower" over-reads the
coarse ruler and "invents names" is now known-false; the safe
defensible line is reach (column lineage, ED tokens) + consistency
(routing) + lineage-by-parse vs lineage-by-name.
