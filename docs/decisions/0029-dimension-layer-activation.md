# 0029 — Dimension layer activation: filter-usage qualifies, scope-local aliases resolve

**Status:** Accepted (design pass — implementation to follow)
**Date:** 2026-08-06

## Context

The dimension layer exists in the model (`NodeLayer.DIMENSION`,
`add_dimension_node`, `TECHNICAL_TO_DIMENSION` edges, an LPG export table)
but is empty in practice. `column_refs` now survive the 02→03 boundary, and
the ROADMAP backlog names the two blocking decisions: **which columns
qualify** as dimensions, and **alias resolution** (refs carry FROM-clause
aliases — `peh`, `cat` — not table names; verified in the recorded
fixtures). Downstream, parameter/filter questions ("what date ranges can I
filter this metric by?") are explicitly out of scope for the agent until
this layer ships, and the rematch protocol excludes them.

## Decision

1. **Filter usage qualifies a column; projection does not.** A dimension is
   a column the SQL *slices or filters by*: it appears in a `WHERE`
   predicate, `GROUP BY`, `HAVING`, or as a join key that carries a
   business filter (date/flag/category columns in `ON` clauses). Columns
   that are merely selected are outputs, not dimensions — promoting every
   projection would make the layer a column dump and drown the filter
   signal. Extraction is positional: `_extract_column_refs` grows a
   `context` tag (`where | group_by | having | join_on | select`) taken
   from the AST clause the reference sits in; only filter contexts mint
   dimension nodes. A column used in both stays one node with its contexts
   recorded — frequency across metrics is the dimension's usage weight
   (same flywheel shape as ADR 0023).
2. **Aliases resolve within statement scope, at parse time.** Each
   CTE/select scope already names its sources (`FROM x AS peh JOIN y AS
   cat` — sqlglot exposes the alias→table map per scope). Resolution
   happens where the scope is still in hand (02_parse), never downstream
   where it is lost: `ColumnRef.table` gains the *resolved* physical table,
   keeping the raw alias in a companion field for debugging. Refs that
   cannot be resolved deterministically — ambiguous unqualified columns
   against multi-table scopes, refs into subqueries — are **dropped and
   counted** (a `dimension_refs_dropped` stat on the parse result), never
   guessed into the graph (ADR 0005's principle applied to lineage:
   refuse over guess).
3. **Dimensions attach to Technical tables only** (`dim:{table}.{column}`
   under `TECHNICAL_TO_DIMENSION`, as modeled). CTE-local computed columns
   don't qualify — a dimension the user can filter by must exist
   physically. Dictionary descriptions attach where the data dictionary
   has the column (the mandatory-dictionary rule, ADR 0014, gives most
   dimensions descriptions for free).
4. **Case folding follows ADR 0016** (uppercase-folded matching) for both
   alias→table and column→dictionary joins.

## Consequences

- The agent gains the filter vocabulary: "you can filter
  reporting.USP_ED_Sepsis by HOSP_ADMSN_TIME (admission time), DEPARTMENT_NAME,
  …" — the rematch question set can add its parameter/filter section, and
  the LPG dimension export stops being an empty table.
- Parser work is additive: context tagging + scope-local alias maps in
  `_extract_column_refs` / CTE walk; recorded fixtures make the change
  regression-testable offline (count-oracle style: expected dimension
  counts per metric pinned from the answer key).
- Dropped-ref counting makes resolution honesty measurable — if the drop
  rate is high on real corpora, that is a parser gap surfaced as a number,
  not silently missing filters.
- Same-column-different-tables (PAT_ENC_CSN_ID on many tables) yields one
  dimension node per (table, column) — join-key noise in `where`/`join_on`
  contexts is expected; the usage-weight ordering pushes real business
  filters above plumbing keys in agent answers.
