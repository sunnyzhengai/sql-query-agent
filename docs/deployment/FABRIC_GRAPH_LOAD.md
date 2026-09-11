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
   **`AIVIA_Product/estates/ed_sepsis_dev/graph_export/`** — the
   dev estate is the RULED gate surface (25 Parquet files).
   (Regenerate any time:
   `python3.11 -m aivia.flows.export_graph ed_sepsis_dev`.
   The old sepsis graph_export was DELETED 2026-09-11 — Sunny
   pulled stale superseded files from it; the sepsis export
   regenerates at phase boundaries only.)
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

## The gates moved (2026-09-10, Sunny's ruling)

Every gate — M1's verified record and the one-proc ladder gates
M2–M7 with their exact GQL and expected answers — now lives in
**`AIVIA_Test/GQL_Gates.md`**, beside the tests that mirror the
same numbers. This runbook keeps setup, load mechanics, and the
dialect rules only.

## One namespace: dbo (the dual-set corpse, 2026-09-10)

The lakehouse is schema-enabled: UI loads land in `dbo`, while the
API loader originally wrote to the Tables ROOT — two same-named
sets, and the graph model could only bind one of them (empty
Source dropdowns, dead bindings, M1 lost a day to it). RULED: one
namespace — everything targets `Tables/dbo/`; the loader now does.
Root-level graph_* tables must never exist; delete on sight.

## M2 — the scope layer [SUPERSEDED 2026-09-10 by the M2
REDESIGN before its gate ever ran — kept as record; the ruled
gates are THE ONE-PROC LADDER GATES below. Do NOT load these
tables: scope→table travels through JOIN NODES now (the
remainder rule); joins_to re-homed to M1's content]

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

