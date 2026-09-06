# Phase A projection census — the ED-sepsis corpus (Sunny's gap-check)

**Phase A of the twin-graph ruling (ADR 0077), built 2026-09-06.**
Metamodel v1.2.0 (PROJECTION joins Structure_Kinds); the 28-proc
corpus re-parsed under the bump. This report is the phase gate per
the ED-sepsis acceptance law: real output, for your gap-check.
Nothing below is voiced prose — Phase A captures structure only; the
meaning twin (Phase B) and voicing (Phase C) come next.

## What Phase A claims

Every SELECT-list element in the corpus is now a **projection
member** (name + expression subtree, position-ordered) **or a
counted remainder row** — never silently skipped. The conservation
consequence is the headline finding below.

## Totals

| Measure | Count |
|---|---|
| Files parsed | 28 |
| Projection members captured | 3,397 |
| — named | 3,397 (100%) |
| — anonymous (no name derivable) | 0 |
| Window-function members (`... OVER(...)`) | 131 |
| `SELECT *` counted as `star_projection` | 49 |

## Finding P-1 — the silent-skip hole (closed, counted)

The pre-Phase-A select walk handled only scalar expressions;
**49 `SELECT *` elements were skipped with no trace** — not
captured, not counted, invisible to conservation. They now land as
`star_projection` remainder rows (remainder_total 949 → 998; the
shapes corpus moved 6 → 43 the same way, 37 stars). Star
*expansion* (resolving `*` through KG1 into members) is deliberately
NOT built — it needs a ruling on how expanded members interact with
drift when the table gains a column. Counted until ruled.

## Finding P-2 — the Gap B material is now in the graph

The derived-column meanings that finding 4 could not reach are
captured with their defining expressions. Samples (verbatim
fragments, evidence-grade):

| Scope | Member | Defining expression |
|---|---|---|
| `#BasePopABX` | TIME_LINE | `ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY ABX_ADMIN_TIME)` |
| `#BasePopBolus` | TIME_LINE | `ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY TAKEN_TIME ASC)` |
| `#Pressors` | TIME_LINE | `ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY TAKEN_TIME)` |
| `#EncounterWeights` | TIME_LINE | `ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME ASC)` |

In Phase B these become projection *meaning* nodes, and a filter
like `FIRST_TIME_LINE = 1` resolves through the defining scope's
member — "the first antibiotic administration per encounter" instead
of "the first time line is 1."

## Finding P-3 — two files with zero members (correct, not a miss)

`reports/USP_RPTS_NonSevere_Sepsis.sql` and
`reports/USP_RPTS_Severe_Sepsis.sql` yield no projection members.
Diagnosis: both are control-flow shells (DECLARE + IF + WHILE) whose
work happens inside statement kinds the mapper counts as unmapped
remainder (5 and 6 rows respectively — the standing
dynamic-SQL-shaped gap class, present since round 2). Zero members
with the gaps counted is the honest census; when those statement
kinds get mapped, their SELECTs enter projection automatically.

## Per-file census

| File | Members | Stars counted |
|---|---|---|
| reporting/USP_ED_SEPSIS.sql | 423 | 6 |
| reporting/USP_IP_SEPSIS.sql | 454 | 14 |
| reporting/USP_IP_SepsisDates.sql | 7 | 0 |
| reporting/USP_IP_SepsisDetails.sql | 224 | 1 |
| reporting/USP_IP_SepsisDetails_v1.sql | 42 | 0 |
| reporting/USP_IP_SepsisEncounters.sql | 22 | 0 |
| reporting/USP_IP_SepsisEncountersDetails.sql | 17 | 0 |
| reporting/USP_IP_SepsisEncountersWLocations.sql | 32 | 0 |
| reporting/USP_IP_SepsisEncountersWLocations_v1.sql | 17 | 0 |
| reporting/USP_IP_SepsisPatientDates.sql | 48 | 1 |
| reporting/USP_IP_SepsisPatientDates_v1.sql | 12 | 0 |
| reporting/USP_IP_SepsisScreeningAudit.sql | 142 | 0 |
| reporting/USP_IP_SepsisScreeningAudit_v1.sql | 52 | 0 |
| reporting/USP_IP_SepsisShiftCompliance.sql | 130 | 1 |
| reporting/USP_IP_SepsisShiftComplianceByShift.sql | 31 | 0 |
| reporting/USP_IP_SepsisShiftComplianceMetrics.sql | 27 | 0 |
| reporting/USP_IP_Sepsis_ComplianceByShift.sql | 44 | 0 |
| reporting/USP_IP_Sepsis_ComplianceMetrics.sql | 40 | 0 |
| reporting/USP_IP_Sepsis_Details.sql | 157 | 0 |
| reporting/USP_IP_Sepsis_Encounters.sql | 16 | 0 |
| reporting/USP_IP_Sepsis_ScreeningTool.sql | 68 | 0 |
| reports/USP_RPTS_ED_Sepsis.sql | 420 | 0 |
| reports/USP_RPTS_IP_SEPSIS.sql | 393 | 13 |
| reports/USP_RPTS_IP_SEPSIS_COMPLIANCE.sql | 101 | 1 |
| reports/USP_RPTS_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES.sql | 70 | 0 |
| reports/USP_RPTS_IP_SEPSIS_REPORT.sql | 408 | 12 |
| reports/USP_RPTS_NonSevere_Sepsis.sql | 0 (finding P-3) | 0 |
| reports/USP_RPTS_Severe_Sepsis.sql | 0 (finding P-3) | 0 |

## Acceptance state

- F8 phase-A cases: RUNNABLE and green
  (`tests/aivia/test_phase_a_projection.py`, 6 tests)
- Full suite: green; both shakedowns' conservation counters
  re-pinned with the Phase A deltas justified in their notes
- Open for your ruling at gap-check: (1) is the star posture right
  (counted, unexpanded)? (2) does the P-3 zero-member diagnosis
  match your read of those two procs?
