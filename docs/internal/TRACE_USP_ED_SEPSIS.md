# Deep trace — reporting.USP_ED_Sepsis through every pipeline stage

**Requested by Sunny 2026-08-18 ("focus on one proc, one of the more
complex ones... write expected output for each step, compare actual to
expected... write a description yourself following our guidelines and
find false statements/missing logic. don't fake it").**

Method: the proc chosen is the estate's most complex (43 steps, 3,396
lines). Expected values below were derived independently from the RAW
SQL (`data/demo/seed_demo_source.sql`, the `[reporting].[USP_ED_Sepsis]`
block) — step inventory from `SELECT INTO #x` + CTE declarations, table
set from FROM/JOIN scanning with comments and literals stripped. Actual
values were pulled live from the tenant (Eventhouse, 2026-08-18 ~23:00)
after the full 060→800 run. Nothing hand-adjusted; the harvest is in
the session scratchpad (`trace_harvest.json`).

## Stage-by-stage: expected vs actual

| Stage | Expected (from my SQL reading) | Actual (live tenant) | Verdict |
|---|---|---|---|
| 200 parse | proc parses; 43 steps (temp tables + CTEs) | parsed; 43 transformation nodes | **EXACT — 43/43, zero diff either direction** |
| 300 graph | canonical node + 43 steps + edges to 48 base tables | canonical + 43 steps + edges to 45 tables | **45/48 tables (94%) — 3 real misses, see below** |
| 400 card | business_name "ED Sepsis Screening", report link, non-null calculation_logic | all three present; link resolves to the new dashboard | **PASS** |
| 600 descriptions | business-language, grounded, literal values kept | 966-char metric description + 43 step descriptions | **PARTIALLY FALSE — see audit** |
| 700 index | metric findable by business phrasing | search('ED sepsis screening rate') → top candidate | **PASS** (gate evidence) |
| 800 export | canonical/edges exported; uses_table closure | closure rows present; blast-radius answer works | **PASS** (gate evidence) |

### The 3 missing table edges (300) — honest accounting

- `dbo.MED_MIX_COMPONENTS` — read inside a deeply nested subquery;
  matches the documented AST-suppression class (the 13k-suppression
  counter finding). Known gap, already on the follow-up list.
- `reports.SEVERE_SEPSIS_STAGING`, `reports.NON_SEVERE_SEPSIS_STAGING`
  — LEFT OUTER JOINs near the final select (line ~2957). Real reads
  the extractor missed; likely the same suppression class. Filed with
  the suppression refinement.

None of the 45 captured edges is false — the misses are omissions, not
inventions. Deterministic-stage summary: **everything the graph claims
is true; 3 of 48 reads are missing and the gap class was already known
and counted.**

## The description audit (stage 600) — where the real problem is

### Generated metric description, claim by claim

| Claim | Verdict | Evidence |
|---|---|---|
| "encounters for patients with sepsis" | **MISFRAMED** | population is ALL ED encounters in the window (screening context); no sepsis filter on the population |
| "valid patient identifier" | **WEAK** | defensible only as the INNER JOIN to the patient table; no explicit filter |
| "admitted to the hospital, non-null admission time" | **FABRICATED** | zero occurrences of any admission-time filter in 3,396 lines |
| "excludes pending or cancelled" | **FABRICATED** | the only "cancelled" in the proc is the *Sepsis Alert Cancelled* flowsheet code (9001125002) — an outcome tracked, not an encounter exclusion |
| "only those with both a triage start and end time" | **FABRICATED** | triage columns are SELECTed, never filtered |
| score 9000002613 between arrival and departure | TRUE | verified; but omits co-listed retired score 9000161709 |
| BP percentiles for girls and boys | TRUE | codes 95, 9001140203, 9001140205 verified |
| age ≤ 21 days flag | TRUE | verified in the final select |

**Major omissions:** the reporting window (default: last 12 months
through yesterday, via date tokens MB-12/T-1); the positive-score
threshold (> 4); and the entire treatment/culture machinery
(antibiotics, boluses, pressors, cultures, alerts, 24-hour returns) —
partly explained by the roots-only composition design, but the > 4
threshold is core logic and absent.

### The fabrication mechanism (found, not guessed)

The false claims did NOT originate in the metric summary — the
composition faithfully rolled up its root steps. They originate in the
**step descriptions**, with two distinct failure modes:

1. **Selected columns hallucinated into filters.** The Base_Pop step
   SELECTs triage times and admission time as output columns; its only
   real filter is the arrival-date window. The LLM described the
   selected columns as if they were WHERE clauses ("filters for
   encounters with a triage start and end time"). The same boilerplate
   (valid identifier / non-null admission) repeats across ~12 step
   descriptions — a template hallucination.
2. **Invented literal values.** The LDA steps' descriptions cite
   "flowsheet IDs **123 and 456** ('ETT'), **789 and 101** ('IV')" —
   the real codes are **900112** and **900111**. Placeholder numbers,
   fabricated outright. (A sibling step said "specific flowsheet IDs" —
   the vague-filler class our observer already flags.)

The "Ground every line in the SQL above" prompt instruction did not
prevent either mode. **Prompt instructions are intent; only mechanical
verification survives** — the same lesson as the notebook contract,
now applied to stage 600. Fix filed: HANDOFF_DESCRIPTION_GROUNDING_GATE
(deterministic post-generation checks: every literal value quoted in a
description must appear in the step's fragment; every filter-claim term
must have support in the SQL text; failures land as rejected rows, not
published descriptions).

## My independent description (per the v3 guidelines, from the SQL)

This metric reports every emergency department encounter in the
reporting window together with the patient's sepsis screening scores,
vital signs, sepsis-related treatments, and culture results, to show
how consistently ED sepsis screening is performed and acted on.

Business logic:
- Includes all ED encounters with an arrival date in the reporting
  window (default: from the start of the month 12 months ago through
  yesterday), with demographics, disposition, and location attached.
- Collects sepsis screening scores (codes 9000161709 — retired — and
  9000002613, the 2019 sepsis score) recorded between ED arrival and
  ED departure; a score above 4 counts as positive.
- Collects blood pressure readings (code 95) and boys'/girls' systolic
  percentile values (9001140203, 9001140205) taken during the ED stay;
  systolic below 100 flags hypotension for patients over 13 years,
  with percentile-based evaluation for younger patients.
- Tracks intravenous antibiotics (therapeutic class 11), fluid boluses
  (frequency code 300902), and vasopressors given before ED departure,
  plus blood, urine, and CSF culture orders and results, line and
  airway placements (ETT 900112, peripheral IV 900111, central line
  value set 3022), and sepsis alerts including cancelled alerts
  (code 9001125002).
- Flags patients aged 21 days or younger and identifies return ED
  visits within 24 hours of departure.

## Bottom line

- **The deterministic pipeline earned trust in this trace**: 43/43
  steps, 45/48 reads with the 3 misses belonging to a known, counted
  gap class, a correct card, working search and lineage. Nothing it
  asserts about this proc is false.
- **The LLM description stage did not**: three fabricated filters, one
  set of invented codes, and a misframed population — all now
  localized to a specific mechanism with a mechanical fix designed.
  Until the grounding gate ships, treat 600's step bullets as drafts
  for steward review, not certified facts — and the metric summary
  inherits whatever the steps got wrong.
- The freshness columns did not surface through the orchestrator's
  card facts (both None) — the assemble-layer query predates 1.19's
  columns; verify against the lakehouse and extend the card query
  (filed alongside the grounding gate).
