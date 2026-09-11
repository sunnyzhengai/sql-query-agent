# Fabric Graph load — the verification surface (M1: technical layer)

*(Manifest_Build §E5, ruled 2026-09-09. You load the export into
Fabric Graph in your own workspace and run the gate queries
yourself — the store's shape verified by your GQL, never by a
rendering. Repeat per batch: each batch re-exports; you refresh
the tables and re-run that batch's gate.)*

## Prerequisites (check once)

- [ ] Workspace **AIVIA-DEV-2** on your Fabric capacity (you have it).
- [ ] **Graph (preview)** enabled: Settings → Admin portal / workspace
      settings → look for Graph under preview features. If the
      "Graph model" item type doesn't appear in + New item, it's off.

## Steps

1. In **AIVIA-DEV-2**: **+ New item → Lakehouse**, name it
   **`AIVIA_GRAPH`**. (Dedicated — batch refreshes are
   drop-and-reload; nothing else lives here.)
2. On your machine the export files are in
   `AIVIA_Product/estates/sepsis/graph_export/` — 7 Parquet files.
   (Regenerate any time:
   `python3.11 -m aivia.flows.export_graph sepsis`)
3. Open `AIVIA_GRAPH` → **Files** → **Upload files** → select all
   7 Parquet files.
4. For each of the 7 files: right-click → **Load to Tables** →
   **New table** → keep the file's name (`graph_db`,
   `graph_db_schema`, `graph_table`, `graph_column`,
   `graph_has_part_dbSchema`, `graph_has_part_schemaTable`,
   `graph_has_part_tableColumn`). Result: 7 Delta tables.
5. In the workspace: **+ New item → Graph model (preview)**, name
   **`AIVIA_GRAPH_MODEL`**, choose the `AIVIA_GRAPH` lakehouse and
   add the 7 tables.
6. Map **node types** — name them exactly like the store labels
   (lowercase), key column `nodeId` in each:
   - `db` ← graph_db · `db_schema` ← graph_db_schema ·
     `table` ← graph_table · `column` ← graph_column
   - properties (name, description, grain, pkColumns, …) map
     automatically from the remaining columns.
7. Map **edge type `has_part`** three times, `sourceId → targetId`:
   - db → db_schema via graph_has_part_dbSchema
   - db_schema → table via graph_has_part_schemaTable
   - table → column via graph_has_part_tableColumn
8. Save / build the model, open the **query** experience.

## Why Parquet, never CSV (the missing-86 corpse, 2026-09-09)

Fabric's Load-to-Tables mis-parsed standard CSV quote-escaping:
every column whose steward description contained double-quotes
("Y"/"N", "NDC Expired", ...) loaded as NULL — 3 nodes and ~86
edges silently vanished at graph refresh. Sunny's per-table GQL
diff against the export truth found them. Parquet has no parsing
layer; the corpse row (WRONG_MED_ALT_CNT) is pinned round-trip
byte-perfect in test_graph_export.

## Dialect rules (learned live 2026-09-09, Sunny's first run)

- ONE statement per run — clear the editor between queries.
- Every RETURN expression needs an `AS` alias; `label` is a
  reserved alias — use `nodeType` etc.
- Aggregation needs an explicit `GROUP BY` (no Cypher-style
  implicit grouping).
- Comments are `//` (never SQL's `--`).
- Reserved words in names force backticks — so NO graph name is
  ever one: the vendored official list
  (AIVIA_Design/Registry_GQL_Reserved_Words.json) gates every label, edge,
  table, and column at test time (Sunny's rename rulings:
  has_part, performed_by, db_schema, param, derived_column,
  pbi_report; kg3 text -> description).

## The M1 gate (run these; expected answers stated)

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

## One namespace: dbo (the dual-set corpse, 2026-09-10)

The lakehouse is schema-enabled: UI loads land in `dbo`, while the
API loader originally wrote to the Tables ROOT — two same-named
sets, and the graph model could only bind one of them (empty
Source dropdowns, dead bindings, M1 lost a day to it). RULED: one
namespace — everything targets `Tables/dbo/`; the loader now does.
Root-level graph_* tables must never exist; delete on sight.

## M2 — the scope layer (bottom-up re-ruling, 2026-09-10)

Ships the layer that touches the technical foundation directly:
`graph_scope` (312 rows — name, description STORED on the store
node and exported verbatim, structures) and
`graph_reads_scopeTable` (451 edges, scope→table at TRUE grain).
The earlier file-layer tables (graph_file / graph_reads_fileTable)
are WITHDRAWN — files ship at M6, tied to statements; never load
them.

Load: upload both parquet → Load to Tables (New table, dbo) → in
the graph model: Get data — keep ALL existing boxes checked, add
the two new → Load → Add node `scope` ← graph_scope, key `nodeId`,
properties name/description/structures → Add edge `reads`,
scope → table, via graph_reads_scopeTable (sourceId → targetId) →
Save → ONE refresh.

M2 also ships `graph_joins_to_tableTable` (65 rows) — the DECLARED
dictionary joins (Epic Clarity joins.csv, loaded at KG1 intake;
they were in the store all along but M1's export missed them).
Add edge `joins_to`, table → table, sourceId → targetId, property
onColumns. Observed joins arrive as condition nodes at M3; their
GQL diff against these = documentation drift.

THE M2 GATE:
```gql
MATCH (s:scope) RETURN count(s) AS cnt
```
Expected: 312.
```gql
MATCH (s:scope)-[:reads]->(t:table) RETURN count(*) AS cnt
```
Expected: 451.
```gql
MATCH (s:scope WHERE s.name = '#Base_Pop')-[:reads]->(t:table)
RETURN s.nodeId AS scopeId, t.name AS tableName ORDER BY scopeId, tableName
```
Expected: each file's #Base_Pop with its read tables —
ED_ENCOUNTERS_FACT among the ED proc's.
```gql
MATCH (t:table WHERE t.name = 'ED_ENCOUNTERS_DM')<-[:reads]-(s:scope)
RETURN count(s) AS cnt
```
The reverse walk: which selections read the ED data mart.
```gql
MATCH (s:scope) RETURN s.name AS selection, s.description AS descr LIMIT 10
```
Stored descriptions, composed bottom-up from the dictionary words.
```gql
MATCH ()-[j:joins_to]->() RETURN count(j) AS cnt
```
Expected: 65 — the dictionary's declared joins.
```gql
MATCH (a:table WHERE a.name = 'ADT_EVENTS')-[j:joins_to]->(b:table)
RETURN b.name AS joinsTo, j.onColumns AS onCols
```
The declared neighbors of ADT_EVENTS with their keys.

## THE ONE-PROC LADDER GATES (ruled 2026-09-10): M2–M7 on
ed_sepsis_dev

From M3 on, batches build/test/GATE on the one-proc estate
(`AIVIA_Product/estates/ed_sepsis_dev` — USP_ED_SEPSIS alone,
full dictionary). Answer key with every expected number:
`expected_m_gates.json` in that estate dir — numbers derived from
the parse, pinned by test_ed_sepsis_dev_estate.py BEFORE each
batch builds. Export: `python3.11 -m aivia.flows.export_graph
ed_sepsis_dev`.

**Sunny's surface choice on the still-open M2 gate:** the staged
M2 numbers above are the SEPSIS estate's (312 / 451). The
technical layer is IDENTICAL in both estates (dictionary truth
never narrows), so switching the Fabric tables to the dev
estate's exports invalidates nothing M1 verified. Recommended:
load ed_sepsis_dev from here on and gate M2 with the dev numbers
below; the full sepsis estate re-loads at phase boundaries (M7,
M12).

Every gate below follows the census shape: label counts == the
key's node rows, edge-type counts == the key's edge rows, plus
the batch's special checks. Node/edge count queries are always:

```gql
MATCH (n) RETURN labels(n) AS lbl, count(*) AS cnt ORDER BY lbl
```
```gql
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt ORDER BY rel
```

### M2 gate (dev estate)

| expect | value |
|---|---|
| nodes | db 1 · db_schema 3 · table 90 · column 4554 · scope 44 |
| edges | has_part 4647 (3+90+4554) · joins_to 65 · reads 45 |
| descriptions | 44/44 scopes non-empty (`WHERE s.description IS NOT NULL`) |
| spot | #Base_Pop reads ED_ENCOUNTERS_FACT; ADT_EVENTS joins_to neighbors carry onColumns |

THE FULL-CENSUS TABLES (hardened 2026-09-10, Sunny's directive —
the blob-corpse lesson: a spot check passes while the graph
doesn't exist; the gate is EVERY label and EVERY edge type,
totals exact, both directions). Q1/Q3 expected results after each
batch, cumulative:

| after | Q1 nodes by label | total |
|---|---|---|
| M2 | db 1 · db_schema 3 · table 90 · column 4554 · scope 44 | **4692** |
| M3 | + condition 748 · join 93 · param 2 | **5535** |
| M4 | + derived_column 156 | **5691** |
| M5 | + statement 67 · condition→754 · param→4 | **5766** |
| M6 | + file 1 | **5767** |
| M7 | + pbi_report 1 · description 1 · agent 1 · role 1 · responsibility 1 | **5772** |

| after | Q3 edges by type | total |
|---|---|---|
| M2 | has_part 4647 · joins_to 65 · reads 45 | **4757** |
| M3 | has_part 5488 · joins_to 65 · reads 45 · left_side 93 · right_side 93 · resolves_to 152 · uses_param 2 | **5938** |
| M4 | has_part 5644 · … · cites 100 | **6194** |
| M5 | has_part 5694 · resolves_to 156 · uses_param 4 · rest same | **6250** |
| M6 | has_part 5765 · rest same | **6321** |
| M7 | + executes 1 · describes 1 | **6323** |

Any label or edge type not in the row = a gate failure; any
declared count off by one = a gate failure. The machine copy of
these tables (with every per-batch delta and its breakdown) is
`expected_m_gates.json`.

### M3 gate — condition + param + join

| expect | value |
|---|---|
| new nodes | condition 748 · join 93 · param 2 (@dStartDate @dEndDate) |
| new edges | has_part +841 (scope→condition 222 · condition→condition 526 · scope→join 93) · resolves_to 152 (→column 150 · →param 2) · left_side 93 · right_side 93 (→table 85, →scope 101) · uses_param 2 |
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

THE DRIFT QUERY (the product story, live at this batch) must
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

THE SIDE-READS INVARIANT must return zero:

```gql
MATCH (s:scope)-[:has_part]->(j:join)-[:left_side|right_side]->(t:table)
WHERE NOT (s)-[:reads]->(t)
RETURN count(*) AS violations
```
Expected: 0.

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
