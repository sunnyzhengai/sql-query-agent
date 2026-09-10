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
   `AIVIA_Product/estates/sepsis/graph_export/` — 7 CSVs.
   (Regenerate any time:
   `python3.11 -m aivia.flows.export_graph sepsis`)
3. Open `AIVIA_GRAPH` → **Files** → **Upload files** → select all
   7 CSVs.
4. For each of the 7 files: right-click → **Load to Tables** →
   **New table** → keep the file's name (`graph_db`,
   `graph_schema`, `graph_table`, `graph_column`,
   `graph_has_part_dbSchema`, `graph_has_part_schemaTable`,
   `graph_has_part_tableColumn`). Result: 7 Delta tables.
5. In the workspace: **+ New item → Graph model (preview)**, name
   **`AIVIA_GRAPH_MODEL`**, choose the `AIVIA_GRAPH` lakehouse and
   add the 7 tables.
6. Map **node types** — name them exactly like the store labels
   (lowercase), key column `nodeId` in each:
   - `db` ← graph_db · `schema` ← graph_schema ·
     `table` ← graph_table · `column` ← graph_column
   - properties (name, description, grain, pkColumns, …) map
     automatically from the remaining columns.
7. Map **edge type `has_part`** three times, `sourceId → targetId`:
   - db → schema via graph_has_part_dbSchema
   - schema → table via graph_has_part_schemaTable
   - table → column via graph_has_part_tableColumn
8. Save / build the model, open the **query** experience.

## Dialect rules (learned live 2026-09-09, Sunny's first run)

- ONE statement per run — clear the editor between queries.
- Every RETURN expression needs an `AS` alias; `label` is a
  reserved alias — use `nodeType` etc.
- Aggregation needs an explicit `GROUP BY` (no Cypher-style
  implicit grouping).
- Comments are `//` (never SQL's `--`).
- Reserved words in names force backticks — which is why the edge
  is `has_part`, not `contains` (Sunny's rename ruling).

## The M1 gate (run these; expected answers stated)

```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
Expected exactly: `db 1 · schema 3 · table 90 · column 4554` —
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
MATCH (s:schema)-[:has_part]->(t:table)
RETURN s.name AS schemaName, count(t) AS tables GROUP BY schemaName
```
Expected: the three schemas with their table counts summing to 90.

## Per-batch refresh (M2 and on)

1. Pull the branch; re-run the export command (step 2).
2. Upload the new/changed CSVs over the old ones (Files →
   overwrite), **Load to Tables** again for changed tables.
3. New tables (new node kinds) → extend the graph model: new node
   type + its contains mapping, per that batch's runbook note.
4. Run that batch's gate queries from Manifest_Build §E5.
