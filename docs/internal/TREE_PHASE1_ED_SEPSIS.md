# Tree phase 1 — ED sepsis acceptance output (traced, reconciled)

Per the standing protocol (2026-08-19): every tree-contract phase
ships real test output against `[reporting].[USP_ED_Sepsis]`, and the
dev session traces the SQL itself — the reviewer checks domain
judgment, not arithmetic.

**Correction note (same day):** the first version of this artifact
reported 33 steps / 99.2% by carving only the `SELECT INTO` blocks —
it missed the 6 CTE statements, the final SELECT, and 2 IF blocks, and
its splitter also cut two statements mid-parenthesis. The full trace
below supersedes it. Overstated coverage is exactly the failure class
this protocol exists to catch; it caught its own author first.

## Method

All 43 statements of the raw proc (70,703 chars) were bounded with a
paren-depth-aware splitter (demo surgery — phase 1b replaces this with
ScriptDom's own statement list) and run through
`src.tree.extract.build_decision_tree` (1.26.0). Verification was
INDEPENDENT: per statement, textual counts of `JOIN` / `WHERE` /
`WHEN` (comments and strings stripped) were compared against the
extractor's per-context site counts.

## Results

| | |
|---|---|
| Statements analyzed | **43** (matches the deep trace's 43-step inventory) |
| Decision sites (predicate grain) | **442** |
| Extracted | **431 (97.5%)** |
| Counted gaps | **11** — every one named below |
| Extractor-vs-textual mismatches on clean statements | **0 of 32** |

Zero mismatches means: on every statement the extractor fully parsed,
its join/where/case site counts equal the independently counted
occurrences in the SQL text — including `Final` (38 joins / 2 wheres /
66 case-whens) and `Base_Pop` (9/1/0).

## Base_Pop — the step whose description was once fabricated

```
[where]   BETWEEN: EEF.ADT_ARRIVAL_DATE BETWEEN @dStartDate AND @dEndDate
[join_on] EQ: EEF.ENCOUNTER_ID = HE.ENCOUNTER_ID
[join_on] EQ: EED.ENCOUNTER_ID = EEF.ENCOUNTER_ID
[join_on] EQ: PAT.PATIENT_ID = HE.PATIENT_ID
[join_on] EQ: REDI.ED_DISPOSITION_CODE = HE.ED_DISPOSITION_CODE
[join_on] EQ: REG.ETHNIC_GROUP_CODE = PAT.ETHNIC_GROUP_CODE
[join_on] AND
          EQ: RACE.PATIENT_ID = PAT.PATIENT_ID
          EQ: RACE.LINE = 1        <- line-table fan-out qualifier, captured in place
[join_on] EQ: RPR.PATIENT_RACE_CODE = RACE.PATIENT_RACE_CODE
[join_on] EQ: DEP.DEPARTMENT_ID = HE.DEPARTMENT_ID
[join_on] EQ: LOC.LOC_ID = DEP.REV_LOC_ID
```

Exactly ONE population filter exists — the arrival-date window. The
triage/admission/cancelled filters the old LLM description invented
have no node here; under the tree architecture (clauses 2+5) a
description of a nonexistent decision has no input to arise from and
no ledger entry to survive on.

## The 11 gaps, classified (all sqlglot 19.7 limits; ScriptDom parses
## every one of these classes — the 200 trace was 43/43)

| Class | Count | Statements | Note |
|---|---|---|---|
| `WITH cte AS (...) SELECT ... INTO` | 6 | lines 285, 787, 1089, 1439, 1481, 2199 | "Failed to parse any statement following CTE" — CTE+SELECT INTO unsupported |
| `STUFF(... FOR XML PATH(''))` | 2 | Base_Pop_ENC_Reason, ..._ConCat | T-SQL string aggregation idiom |
| `SELECT * INTO ... UNION` | 1 | Cultures | |
| `IF @param IS NULL ... SET @d = fn_parse_date('MB-12')` | 2 | lines 29, 39 | the DEFAULT REPORTING WINDOW logic — see design note |
| Expected after phase 1b (ScriptDom port) | **~0** | | |

**Design note for phase 1b (flagged for Sunny):** the two IF blocks
are the parameter-defaulting logic — the 12-month default window
(MB-12 → T-1) that the original deep trace called out as a major
description omission. It is a real business decision but control-flow
grain, not predicate grain. Phase 1b must decide how the tree models
it (e.g., a `parameter_default` site kind) rather than leaving it a
permanent counted gap.

## Remaining reviewer questions (domain judgment only)

1. 442 decision sites across the proc, 255 of them in `Final`'s CASE
   machinery — does that match your read?
2. Is any decision you know is in Base_Pop's SQL absent from the
   inventory above?
3. Do you agree the IF/default-window logic must become a modeled
   site kind in 1b (vs staying a counted gap)?

After the 300-on-1.26 tenant run, the same view comes from:

```sql
SELECT step_name, context, status, predicate_count,
       expression_sql, reason_code
FROM graph_decision_sites
WHERE metric_id LIKE '%ED_Sepsis%'
ORDER BY step_name, site_id
```

Deltas against this document are gaps in the pipeline — report them.

## Native re-run (1.28.0, same day — sqlglot abolished)

The extractor now runs on ScriptDom everywhere (ADR 0001 total law).
Re-run against the same raw proc:

| | sqlglot bootstrap | native (1.28.0) |
|---|---|---|
| Decision sites | 442 | **488** |
| Extracted | 431 (97.5%) | **486 (99.6%)** |
| Gaps | 11 | **2** (both `control_flow_if` — reviewer question 3) |

The review of the previous render caught two extractor bugs the unit
tests had missed — the acceptance protocol working exactly as designed:

1. **BETWEEN was a counted gap** (ScriptDom models it as
   `BooleanTernaryExpression`) — 22 window filters, INCLUDING
   Base_Pop's one true filter, were unextracted until modeled. Now a
   `BETWEEN`/`NOT_BETWEEN` leaf; pinned by regression test.
2. **Double negation**: `x IS NOT NULL` was wrapped in an extra NOT
   node, claiming the OPPOSITE of the SQL. Text-intrinsic negation now
   lives in the op (`IS_NOT`, `NOT_IN`, `NOT_BETWEEN`, `NOT_LIKE`);
   only standalone `NOT` (e.g. NOT EXISTS) is a NOT node. Pinned.

Reviewer question 3 ANSWERED (Sunny, 2026-08-19): **model it** — the
IF default-window blocks become a `parameter_default` site kind in 1b;
expected end state 488/488. (Questions 1–2 stand answered by the
reconciliation and the dictionary remediation: 28/28 leaf-grounded.)

## Phase 1b complete (1.30.0, overnight run)

| | native 1.28.0 | **1b (1.30.0)** |
|---|---|---|
| Decision sites | 488 | 488 |
| Extracted | 486 (99.6%) | **488 (100.0%)** |
| Gaps | 2 (control_flow_if) | **0** |

- `parameter_default` sites (your ruling) carry the default window
  verbatim: operands include `'MB-12'` and `'T-1'` — the description
  layer can now voice "defaults to the last 12 months through
  yesterday."
- Decision nodes are IN THE GRAPH: `step→decision`,
  `decision→column` (column-grain when the dictionary has the column,
  table-grain otherwise), `decision→step` for temp-side references —
  and every extracted site carries a `reachability` verdict
  (connected | literal_only | parameter_only | unresolved_alias |
  unqualified): connected or counted, no dangling decisions.
- The depth-cap fix recovered the trace's 3 missing reads — this
  proc's read set now matches your hand-derived 48 exactly
  (RECERT_ANSWER_KEY_1_30.md).

Remaining known gap classes in the WHOLE corpus: dynamic SQL only.
