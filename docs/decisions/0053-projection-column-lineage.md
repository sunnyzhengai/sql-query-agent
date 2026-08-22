# 0053 — Projection-grain column lineage (the columns pass, v1)

Date: 2026-08-22
Status: accepted
Category: architecture
Axioms: spec:C1, spec:C2 (frontier + conservation); AIVIA-framework
typing D1/D4/J2 in prose below. §3b design review — this ADR is the
review record.

## Context

Ordered by Sunny (2026-08-22): the filter blast radius (decision
sites) landed with the columns work, but the differentiating
governance answer is the PAIR — "PATIENTMRN is selected by these 9
metrics and filtered by none" — and selection had no column-grain
relation: transform_to_technical reads are table-grain (all 681
edges, verified live). The parse data already existed: every step
carries ScriptDom-extracted `column_refs`.

## The §3b answers (design before code)

1. **Inventory.** Contexts that mint `transform_to_column` edges (v1):
   the parser's per-step `column_refs` (SELECT list + fragment
   expressions) and `final_select_columns` for the `__final_select__`
   step. Not minted, on record: GROUP BY / ORDER BY as distinct
   contexts (subsumed in fragment refs where the parser captured
   them); DAX measure refs (measure_to_column — separate ingestion
   gap, its registry row); dep-grain step chains (parked behind
   Round 4 by Sunny).
2. **Conservation.** `refs = minted ⊎ dropped(reason)` — the ADR 0029
   honesty pattern. Edges are RESOLVED-ONLY: a ref mints exactly when
   it resolves to one dictionary column node (qualified: the
   qualifier must name a step table; unqualified: unique across the
   step's tables). Drop reasons counted: unresolved_qualifier,
   no_dictionary_column, ambiguous, duplicate, no_column_name. The
   build step asserts the equation; BuildGraphOutput carries the
   counts.
3. **Drift.** The EdgeType addition forced a reachability row before
   CI could pass (ADR 0052 totality — the mechanism firing as
   designed). The Fabric-Graph export excludes the type explicitly
   (counted exclusion, same class as decision edges); an edge type in
   neither map fails loudly. The ask-surface op probes edge presence:
   a pre-0053 export answers "projection coverage absent — rerun
   mints it," never "selected by none."
4. **Type.** Deterministic (parser + dictionary resolution) ×
   end-user → L1 (builder conservation tests, ops union tests) +
   L3-once (walk probe D5 re-graded after the pipeline run mints the
   edges).

## Decision

- `EdgeType.TRANSFORM_TO_COLUMN`, minted in
  `GraphBuilder.mint_projection_edges` during `build_from_parsed_sql`.
- `lineage(column=)` answers with BOTH relations — rows carry
  `relation: filters|selects` — universe naming both edge sources;
  counts exact over recorded edges.
- Edges flow to `graph_edges` with the next pipeline run (Sunny's
  single run: descriptions v6 regeneration + decision redaction +
  these edges, one pass).

## Consequences

- Walk D5 upgrades from honest-empty to the full governance pair
  after the rerun; graded L3-once then.
- The 0046 engine gains a ready column-grain substrate; the
  Fabric-Graph export exclusion lifts with it.
