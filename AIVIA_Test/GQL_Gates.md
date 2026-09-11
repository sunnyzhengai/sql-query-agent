# GQL Gates — the M-ladder verification queries (Sunny's surface)

*(Moved from docs/deployment/FABRIC_GRAPH_LOAD.md 2026-09-10 at
Sunny's request: the gates live beside the tests they mirror.
The runbook keeps setup/load/dialect; THIS file is what you run.
Every gate: copy one query, run it, compare the stated answer.
Machine twin of every number:
AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json.)*

## The original M1 gate (VERIFIED by your GQL 2026-09-10, sepsis
estate — kept as record)


```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
Expected exactly: `db 1 · db_schema 3 · table 90 · column 4554` —
and NOTHING else (no statement, no scope: the Shape_Ledger's
TARGET rows are honestly absent until their batches land).

```gql
MATCH ()-[c:has_part]->() RETURN count(c) AS cnt
```
Expected: **4647** (3 + 90 + 4554).

```gql
MATCH (t:table) WHERE t.name = 'SEVERE_SEPSIS_STAGING'
RETURN t.description AS tableDescription
```
Expected: "ETL staging table for identifying severe sepsis cases.
Contains records of patients who meet the criteria for severe
sepsis along with tracking for compliance with bundle elements."

```gql
MATCH (s:db_schema)-[:has_part]->(t:table)
RETURN s.name AS schemaName, count(t) AS tables GROUP BY schemaName
```
Expected: the three schemas with their table counts summing to 90.


## THE ONE-PROC LADDER GATES (ruled 2026-09-10): M2–M7 on
ed_sepsis_dev

From M3 on, batches build/test/GATE on the one-proc estate
(`AIVIA_Product/estates/ed_sepsis_dev` — USP_ED_SEPSIS alone,
full dictionary). Answer key with every expected number:
`expected_m_gates.json` in that estate dir — numbers derived from
the parse, pinned by test_ed_sepsis_dev_estate.py BEFORE each
batch builds. Export: `python3.11 -m aivia.flows.export_graph
ed_sepsis_dev`.

**RULED (Sunny 2026-09-10): the gate runs on the DEV ESTATE.**
Load ed_sepsis_dev's exports; the full sepsis estate re-loads at
phase boundaries (M7, M12). The technical layer is identical in
both estates, so nothing M1 verified is invalidated.

Every gate below follows the census shape: label counts == the
key's node rows, edge-type counts == the key's edge rows, plus
the batch's special checks. Node/edge count queries are always:

```gql
MATCH (n) RETURN labels(n) AS lbl, count(*) AS cnt ORDER BY lbl
```
```gql
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt ORDER BY rel
```

### M1 gate — technical layer + joins_to (re-homed here, Sunny's
redesign ruling)

| expect | value |
|---|---|
| nodes | db 1 · db_schema 3 · table 90 · column 4554 |
| edges | has_part 4647 (3+90+4554) · joins_to 65 (dictionary-declared, onColumns) |
| spot | ADT_EVENTS joins_to neighbors carry onColumns |

THE FULL-CENSUS TABLES (hardened 2026-09-10, Sunny's directive —
the blob-corpse lesson: a spot check passes while the graph
doesn't exist; the gate is EVERY label and EVERY edge type,
totals exact, both directions). Q1/Q3 expected results after each
batch, cumulative:

| after | Q1 nodes by label | total |
|---|---|---|
| M1 | db 1 · db_schema 3 · table 90 · column 4554 | **4648** |
| M2 | + scope 44 · join 93 | **4785** |
| M3 | + condition 748 · param 2 | **5535** |
| M4 | + derived_column 156 | **5691** |
| M5 | + statement 67 · condition→754 · param→4 | **5766** |
| M6 | + file 1 | **5767** |
| M7 | + pbi_report 1 · description 1 · agent 1 · role 1 · responsibility 1 | **5772** |

| after | Q3 edges by type | total |
|---|---|---|
| M1 | has_part 4647 · joins_to 65 | **4712** |
| M2 | + left_side 93 · right_side 93 · has_part→4740 · reads ~6 (the REMAINDER — exact value pinned at build) | **4997** |
| M3 | has_part 5488 · resolves_to 152 · uses_param 2 · rest same | **5899** |
| M4 | has_part 5644 · + cites 100 | **6155** |
| M5 | has_part 5694 · resolves_to 156 · uses_param 4 | **6211** |
| M6 | has_part 5765 | **6282** |
| M7 | + executes 1 · describes 1 | **6284** |

Any label or edge type not in the row = a gate failure; any
declared count off by one = a gate failure. The machine copy of
these tables (with every per-batch delta and its breakdown) is
`expected_m_gates.json`.

### M2 gate — THE JOIN LAYER [BUILT 2026-09-10, store-verified;
every number below MEASURED from the built store; YOUR GQL on
the dev estate closes the batch]

Load first (once): upload ALL parquets from
`AIVIA_Product/estates/ed_sepsis_dev/graph_export/` → Load to
Tables (dbo) → in the graph model add node `scope` (key nodeId;
name, description, structures) and node `join` (key nodeId;
name, description, onPredicate) → add edges: `has_part`
scope→join via graph_has_part_scopeJoin · `left_side` join→table
AND join→scope (two mappings) · `right_side` likewise · `reads`
scope→table via graph_reads_scopeTable → Save → ONE refresh.

The full census (any extra label/type or off-by-one = failure):

```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
Expected exactly: db 1 · db_schema 3 · table 90 · column 4554 ·
scope 44 · join **95** — total 4787, nothing else.

```gql
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt GROUP BY rel
```
Expected exactly: has_part **4742** · joins_to 65 · left_side
**95** · right_side **87** · reads **6** — total 4995.

| expect | value |
|---|---|
| descriptions | scope 44/44 · join 95/95 non-empty (verbatim-law checked in AIVIA_Test) |
| join conservation | 95 = 87 two-sided + 8 one-sided (ON vs param/literal — left only, counted) + 0 no-sided |
| side targets | →table 88 · →scope 94 |
| reads coverage | remainder 6 + covered-by-sides 53 == read-set 59 |
| deferred, counted | joinType (inner/left_outer/…) — the parse tree lacks the operator type |
| spot | `#Base_Pop`'s join#4 description: "Joins REF_ED_DISPOSITION with HOSPITAL_ENCOUNTERS on REDI.ED_DISPOSITION_CODE = HE.ED_DISPOSITION_CODE." |

THE DRIFT QUERY runs AT THIS GATE — it needs joins + joins_to
only, no condition nodes (why joins are testable alone). Must
return EXACTLY two rows:

```gql
MATCH (j:join)-[:left_side]->(a:table),
      (j)-[:right_side]->(b:table)
WHERE NOT (a)-[:joins_to]-(b)
RETURN DISTINCT a.name, b.name
```
Expected: ENCOUNTER_VISIT_REASONS↔VISIT_REASONS and
MEDICATIONS↔REF_GENERIC_MED — practiced in USP_ED_SEPSIS, never
declared by the dictionary (verified against the parse
2026-09-10, before any build).

THE COVERAGE INVARIANTS (superseding the side-reads invariant —
reads is the remainder, never the union). Disjointness must
return zero:

```gql
MATCH (s:scope)-[:reads]->(t:table),
      (s)-[:has_part]->(:join)-[:left_side|:right_side]->(t)
RETURN count(*) AS doubleConnected
```
Expected: 0. Coverage (reads ∪ join-sides == the parse read-set,
per scope) runs store-side in the census — the parse read-set is
not itself in the graph.

### M3 gate — THE CONDITION LAYER (condition + param; testable
ALONE)

| expect | value |
|---|---|
| new nodes | condition 748 · param 2 (@dStartDate @dEndDate) |
| new edges | has_part +748 (join→condition ON-roots 90 [3 pinned at build] · scope→condition 132 · condition→condition 526) · resolves_to 152 (→column 150 · →param 2, role-tagged) · uses_param 2 |
| condition split | join_on 194 · where 167 · case_when 387; degenerate subkind 25 |
| held for M5 | 6 statement-rooted conditions (IF predicates) + @StartDate/@EndDate — their parents are STATEMENTS, which don't exist until M5; shipping them now would float them (the birth-edge law) |

ONE LABEL, KIND AS PROPERTY (the kind-vs-label standard; ruled at
the design level by the Shape Contract + the closed kind
library): every predicate is a `condition` node whose `predicate`
property comes from kg2_kind_library's closed set; composite
AND/OR/NOT are condition nodes too (nested has_part). The
per-predicate structure lives in ROLE-tagged resolves_to edges
(Sunny's numbered-edge drawing: BETWEEN = subject + bounds).
THE PER-KIND CENSUS is a gate query:

```gql
MATCH (c:condition)
RETURN coalesce(c.predicate, c.shape) AS kind, count(*) AS cnt
ORDER BY cnt DESC
```
Expected at M3 (sums to 748): COMPARE_EQ 210 · NULL_CHECK 170 ·
AND 132 · NOT 123 · IN_LIST 33 · RANGE 22 · COMPARE_LTE 18 ·
COMPARE_LT 15 · OR 9 · COMPARE_GT 6 · EXISTS_SELECTION 5 ·
COMPARE_NEQ 2 · COMPARE_GTE 2 · IN_SELECTION 1. (M5 adds
NULL_CHECK +2, COMPARE_EQ +2, OR +2 → 754.) An unlisted kind or a
moved count = gate failure. Role property on resolves_to,
expected: subject 104 · comparand 43 · selection 3 (this proc's
RANGE bounds resolve to params/literals, so no bound-role column
edges here — the roles vocabulary stays the ratified closed set).

### M4 gate — derived_column

| expect | value |
|---|---|
| new nodes | derived_column 156 (154 expression + 2 named literal; 312 passthrough projections and 5 anonymous EXISTS-SELECTs are NOT nodes) |
| new edges | has_part +156 · cites 100 (scope→column outputs) |

### M5 gate — statement (+ the M3 holdovers)

| expect | value |
|---|---|
| new nodes | statement 67 (operational subkind 31, voiced never) · condition +6 (the IF predicates: total→754) · param +2 (@StartDate @EndDate: total→4) |
| new edges | has_part +50 (statement→scope 44 · statement→condition 2 · condition→condition 4) · resolves_to +4 (→param: total 156) · uses_param +2 (total 4) |
| descriptions | 67/67 R11-rendered non-empty |
| counted debt | 31 operational statements have NO downward edge — DECLARED Connection_Ledger counted-missing, landing step named M6 (file→statement). Not silent, not a failure: a counted row |

### M6 gate — file

| expect | value |
|---|---|
| new nodes | file 1, aboutness STORED + meaning-key anchored |
| new edges | has_part +71 (file→statement 67 · file→param 4); NO file—reads→table rollup (0) |
| debt closed | the 31 counted-missing statements birth-edge via file→statement; the Connection_Ledger row retires |
| composition | the file description contains its children's words (the summing law) |
| walk | file-[:has_part*]->scope-[:reads]->table is complete: every one of the 90-table dictionary's tables the proc touches is reachable |

### M7 gate — governance + consumption

| expect | value |
|---|---|
| new nodes | pbi_report 1 · description 1 · agent 1 · role 1 · responsibility 1 (person/term/usage 0 until acts) |
| new edges | executes 1 (dashboard→USP_ED_SEPSIS) · describes 1 |
| counted gap | executes names reports/USP_RPTS_ED_Sepsis.sql — absent from this estate BY DESIGN, must appear as a counted gap, never silently dropped |
| ledger | Shape_Ledger TARGET rows == 0; shape census Q1/Q2/Q3 green both directions |
| phase boundary | full sepsis estate re-run against its own key |

## Per-batch refresh (M2 and on)

1. Pull the branch; re-run the export command (step 2) with
   estate `ed_sepsis_dev`.
2. Upload the new/changed parquet over the old ones (Files →
   overwrite), **Load to Tables** again for changed tables.
3. New tables (new node kinds) → extend the graph model: new node
   type + its contains mapping, per that batch's runbook note.
4. Run that batch's gate queries above (answer key:
   expected_m_gates.json).
