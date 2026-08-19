# Tree phase 1 — ED sepsis acceptance output (for Sunny's gap review)

Per the standing protocol (2026-08-19): every tree-contract phase
ships real test output against `[reporting].[USP_ED_Sepsis]` for
Sunny's domain review before the phase is called done.

**Method:** the 33 `SELECT ... INTO #step` statements were carved as
FULL statements from the raw proc (70,703 chars, session scratchpad —
the same source the deep trace used) and run through
`src.tree.extract.build_decision_tree` (1.26.0). Carving was manual
demo surgery; phase 1b replaces it with ScriptDom-extracted fragments
in the pipeline itself. Conservation was asserted per step: zero
violations.

## Summary

| | |
|---|---|
| Steps run | 33 (all `SELECT INTO` steps of the proc) |
| Decision sites (predicate grain) | **400** |
| Extracted | **397 (99.2%)** |
| Counted gaps | **3** (named below — no third bucket) |

Largest step: `Final` — 255 sites, almost all `case_when` (the giant
final-select CASE machinery). Sanity question for the reviewer: does
~400 decisions across this proc match your read of it?

## Base_Pop — the step whose description was once fabricated

The extractor's complete decision inventory for Base_Pop:

```
[where]   BETWEEN: EEF.ADT_ARRIVAL_DATE BETWEEN @dStartDate AND @dEndDate
[join_on] EQ: EEF.ENCOUNTER_ID = HE.ENCOUNTER_ID
[join_on] EQ: EED.ENCOUNTER_ID = EEF.ENCOUNTER_ID
[join_on] EQ: PAT.PATIENT_ID = HE.PATIENT_ID
[join_on] EQ: REDI.ED_DISPOSITION_CODE = HE.ED_DISPOSITION_CODE
[join_on] EQ: REG.ETHNIC_GROUP_CODE = PAT.ETHNIC_GROUP_CODE
[join_on] AND
          EQ: RACE.PATIENT_ID = PAT.PATIENT_ID
          EQ: RACE.LINE = 1
[join_on] EQ: RPR.PATIENT_RACE_CODE = RACE.PATIENT_RACE_CODE
[join_on] EQ: DEP.DEPARTMENT_ID = HE.DEPARTMENT_ID
[join_on] EQ: LOC.LOC_ID = DEP.REV_LOC_ID
```

Two things this proves mechanically:

1. **Exactly ONE population filter exists** — the arrival-date window.
   The triage/admission/cancelled filters the old LLM description
   invented have no node to attach to. Under the tree architecture the
   translator cannot voice a decision that has no node (clause 2 +
   clause 5 ledger).
2. **`RACE.LINE = 1` is captured in place** — the line-table
   fan-out qualifier riding the join (the "qualifying predicates"
   discussed 2026-08-19). Raw schema-map synthesis would not know it;
   shape reuse carries it.

## The 3 counted gaps (all parse_failed, sqlglot)

| Step | Construct | Note |
|---|---|---|
| Base_Pop_ENC_Reason | `STUFF((SELECT ';' + ... FOR XML PATH('')))` | the T-SQL string-aggregation idiom |
| Base_Pop_SepsisScores_ConCat | same `STUFF/FOR XML PATH` idiom | |
| Cultures | `SELECT * INTO ... FROM x UNION ...` | SELECT INTO + UNION |

Both constructs are ordinary T-SQL that ScriptDom parses natively —
**they are expected to go to zero in phase 1b** (the ScriptDom-visitor
port). Until then, on a tenant run they surface as `ops_fallout`
stage `300_tree_unextracted` — visible, escalated, never silent.

## Reviewer checklist (Sunny)

1. Does ~400 decision sites match your read of the proc? Any step's
   count look wrong (too high = double-counting, too low = misses)?
2. In Base_Pop's inventory: any decision you know is in the SQL that
   is absent above?
3. After your 300 run on 1.26+, the same view comes from the tenant:

```sql
SELECT step_name, context, status, predicate_count,
       expression_sql, reason_code
FROM graph_decision_sites
WHERE metric_id LIKE '%ED_Sepsis%'
ORDER BY step_name, site_id
```

Compare its totals to this document; deltas are gaps in either the
carving (this doc) or the pipeline (worse — report them).
