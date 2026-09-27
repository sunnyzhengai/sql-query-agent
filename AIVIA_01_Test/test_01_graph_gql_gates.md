# F14 GQL Gates — did the table load into the graph correctly?

Node label under test: SQL_FILE (Sunny's mapping, 2026-09-27)
Graph model: AIVIA_01_GRAPH · source table: f01_subject_sql_files_graph
(the embedding-free graph export table — ruled 2026-09-27: the graph
cannot hold the 3072-number array as a property; embeddings stay in
f01_subject_sql_files_lh_table and are validated by the local suite)
Mirror pytest: test_01_graph_gql_gates.py re-derives every expected value
below from the data sheet — if the sheet changes, the mirror goes red until
this doc is regenerated to match.

How to run (the FABRIC_GRAPH_LOAD.md dialect rules, learned live 2026-09-09):
- Open AIVIA_01_GRAPH's query experience.
- ONE statement per run — clear the editor between gates.
- Comments are `//`, never `--`.
- Run each gate, eyeball the answer against "Expected". All gates green =
  F14 passed. Any mismatch: copy the actual output verbatim back to the chat.

---

## Gate G1 — 8 nodes, one per report

```gql
MATCH (f:SQL_FILE) RETURN count(f) AS fileCount
```

Expected:
```
fileCount = 8
```

## Gate G2 — every file name arrived, none invented

```gql
MATCH (f:SQL_FILE) RETURN f.fileName AS fileName ORDER BY fileName
```

Expected (8 rows, this exact order):
```
COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS
COOK_RPT_usp_PTA_CensusDashboard_PBI
COOK_RPT_usp_SF_CensusDashboard
Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_SSRS
Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Totals_SSRS
Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_Detail_PBI
Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_Summary_PBI
Reporting_USP_Hospitalist_Daily_Census_Report_92a_PBI
```

## Gate G3 — no duplicate nodes

```gql
MATCH (f:SQL_FILE) RETURN count(DISTINCT f.fileName) AS distinctNames
```

Expected:
```
distinctNames = 8
```

## Gate G4 — database property, grouped

```gql
MATCH (f:SQL_FILE)
RETURN f.databaseName AS databaseName, count(f) AS files
GROUP BY f.databaseName
```

Expected (databaseName | files):
```
CookClarity | 8
```

## Gate G5 — schema property, grouped

```gql
MATCH (f:SQL_FILE)
RETURN f.schemaName AS schemaName, count(f) AS files
GROUP BY f.schemaName
ORDER BY schemaName
```

Expected (schemaName | files):
```
COOK_RPT | 3
Reporting | 5
```

## Gate G6 — no blank or missing database/schema values

```gql
MATCH (f:SQL_FILE)
WHERE f.databaseName IS NULL OR f.databaseName = ''
   OR f.schemaName IS NULL OR f.schemaName = ''
RETURN count(f) AS badRows
```

Expected:
```
badRows = 0
```

## Gate G7 — the graph export table is whole (SQL, not GQL)

The graph loads from f01_subject_sql_files_graph, so that table gets its
own gate. Run in the LAKEHOUSE SQL ENDPOINT, not the graph query page:

```sql
select count(*) as graphTableRows from f01_subject_sql_files_graph
```

Expected:
```
graphTableRows = 8
```

## Retired gates G7/G8 (embeddings in the graph) — ruled 2026-09-27

The original G7/G8 checked the fileNameEmbedding node property. RULED
OUT: the graph model cannot hold the 3072-number array (the mapping UI
types the column "?", full-table loads died with SystemError1009).
Embeddings live in f01_subject_sql_files_lh_table only; their
completeness (every row, exactly 3072 numbers) is enforced by the local
suite — test_01_subject_sql_files_data_contract.py on the sheet and
test_01_load_lh_table.py at the table loader's door.
