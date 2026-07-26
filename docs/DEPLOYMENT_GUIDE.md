# AIVIA Deployment Guide

**Version:** 1.0.0
**For:** System Administrators deploying AIVIA in a Microsoft Fabric tenant

---

## Overview

AIVIA runs entirely within your Microsoft Fabric tenant. This guide walks you through deploying the product, loading your SQL files, running the parsing pipeline, and configuring the Data Agent.

**Estimated time:** 1-2 hours for initial deployment

---

## Prerequisites

Before starting, ensure you have:

| Requirement | Details |
|---|---|
| **Microsoft Fabric workspace** | With Lakehouse access. F2 capacity or higher. |
| **Workspace role** | Contributor or higher on the target workspace |
| **SQL files** | Your stored procedures and/or views exported as .sql files |
| **Data dictionary** (optional) | Table and column descriptions from your data warehouse |
| **ScriptDom DLL** | Microsoft.SqlServer.TransactSql.ScriptDom.dll (see Step 2) |

---

## Step 1: Create Workspace and Lakehouse

1. Open [Microsoft Fabric](https://app.fabric.microsoft.com)
2. Create a new workspace (e.g., "AIVIA-Production")
3. Inside the workspace, create a new **Lakehouse** (e.g., "AIVIA_Lakehouse")
4. Open the Lakehouse and note the Files section — this is where you'll upload code

---

## Step 2: Upload AIVIA Files

Upload the following to your Lakehouse **Files** section:

```
Files/
└── sql-query-agent/
    ├── src/                          ← Core library (all .py files)
    │   ├── config.py
    │   ├── models.py
    │   ├── schemas.py
    │   ├── dictionary.py
    │   ├── parser/
    │   │   ├── sql_parser.py
    │   │   ├── sql_extractor.py
    │   │   ├── scriptdom_fabric.py
    │   │   ├── scriptdom_extractor.py
    │   │   └── error_classifier.py
    │   ├── graph/
    │   │   ├── builder.py
    │   │   └── traversal.py
    │   ├── adapters/
    │   └── ...
    ├── notebooks/
    │   └── pipeline/
    │       ├── 02_parse.py
    │       ├── 03_build_graph.py
    │       ├── 04_build_metric_logic.py
    │       └── 05_validate.py
    ├── libs/
    │   └── Microsoft.SqlServer.TransactSql.ScriptDom.dll
    ├── org_config.yaml               ← Your configuration (see Step 3)
    └── notebooks/
        └── data_agent_instructions.md ← Agent instructions (see Step 7)
```

### Getting the ScriptDom DLL

1. Download from NuGet: https://www.nuget.org/packages/Microsoft.SqlServer.TransactSql.ScriptDom
2. Rename the `.nupkg` file to `.zip`
3. Extract and find `lib/netstandard2.0/Microsoft.SqlServer.TransactSql.ScriptDom.dll`
4. Upload to `Files/sql-query-agent/libs/`

---

## Step 3: Configure AIVIA

Create `org_config.yaml` in `Files/sql-query-agent/`:

```yaml
org:
  name: "Your Organization Name"

lakehouse:
  dict_tables: "dict_tables"
  dict_columns: "dict_columns"
  sql_sources: "sql_sources"
  graph_nodes: "graph_nodes"
  graph_edges: "graph_edges"

dictionary:
  table_name_col: "TABLE_NAME"
  column_name_col: "COLUMN_NAME"
  description_col: "DESCRIPTION"
  table_description_col: "DESCRIPTION"
  table_id_col: null                    # Set if your dictionary uses TABLE_ID instead of TABLE_NAME
```

Adjust column names to match your data dictionary schema.

---

## Step 4: Load Your Data

### 4a: Load SQL Files

Upload your .sql files to the Lakehouse Files section, organized by folder:

```
Files/data/
├── procs/          ← Stored procedures
└── views/          ← Views
```

Then create a notebook and run the SQL file loader to populate the `sql_sources` Delta table. See `notebooks/load_sql_files.py` for the template.

### 4b: Load Data Dictionary (optional but recommended)

If you have a data dictionary (table/column descriptions), load it into two Delta tables:

- `dict_tables` — one row per table with at minimum: `TABLE_NAME`, `DESCRIPTION`
- `dict_columns` — one row per column with at minimum: `TABLE_NAME`, `COLUMN_NAME`, `DESCRIPTION`

The data dictionary enriches the knowledge graph with human-readable descriptions for source tables.

---

## Step 5: Run the Pipeline

Create four notebooks in your workspace. Copy the contents of each pipeline file into a Fabric notebook. Run them in order:

### 5a: Parse SQL (02_parse.py)

**Reads:** `sql_sources`
**Writes:** `parse_results`, `parse_errors`, `parse_successes`

This parses all your SQL files using Microsoft's ScriptDom parser and extracts:
- CTE definitions and their dependencies
- Table references
- Temp table chains
- SQL fragments for each transformation step

Expected result: 99%+ of SQL files parse successfully. Any failures are logged to `parse_errors` with user-friendly explanations.

### 5b: Build Knowledge Graph (03_build_graph.py)

**Reads:** `parse_results`, `dict_tables`, `dict_columns`
**Writes:** `graph_nodes`, `graph_edges`

This builds the three-layer knowledge graph:
- **Canonical layer:** One node per SQL file (your business metrics)
- **Transformation layer:** One node per CTE/temp table (calculation steps)
- **Technical layer:** One node per table and column from the data dictionary

Edges connect the layers: metric → logic steps → source tables.

### 5c: Build Metric Logic (04_build_metric_logic.py)

**Reads:** `graph_nodes`, `graph_edges`
**Writes:** `metric_logic`

This flattens the graph into a single table optimized for the Data Agent:
- One row per metric
- Pre-joined: calculation logic, source tables, table descriptions
- The agent queries this table to answer "How is X calculated?"

### 5d: Validate (05_validate.py)

**Reads:** All tables
**Writes:** `pipeline_validation`, `build_summary`

Validates every step of the pipeline per metric and reports health:
- Step 1: Source loaded
- Step 2: Parse succeeded
- Step 3: Canonical node created
- Step 4: Transform nodes exist
- Step 5: Edges wired
- Step 6: Technical tables reachable

Expected: 95%+ metrics pass all 6 steps.

---

## Step 6: Verify Results

After running the pipeline, check the following:

```sql
-- How many metrics were parsed?
SELECT COUNT(*) FROM parse_successes

-- How many errors?
SELECT error_category, COUNT(*) FROM parse_errors GROUP BY error_category

-- How many nodes and edges in the graph?
SELECT layer, COUNT(*) FROM graph_nodes GROUP BY layer
SELECT edge_type, COUNT(*) FROM graph_edges GROUP BY edge_type

-- How many metrics have calculation logic?
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN calculation_logic IS NOT NULL THEN 1 ELSE 0 END) as with_logic,
  SUM(CASE WHEN source_tables IS NOT NULL THEN 1 ELSE 0 END) as with_tables
FROM metric_logic
```

---

## Step 7: Configure the Data Agent

1. In your workspace, create a new **Fabric Data Agent**
2. Add these Delta tables as data sources:
   - `metric_logic` (primary — the agent queries this first)
   - `graph_nodes`
   - `graph_edges`
   - `parse_errors`
3. Open `notebooks/data_agent_instructions.md`
4. Copy the entire contents and paste into the agent's **Instructions** field
5. Save and publish the agent

### Test the Agent

Ask these questions to verify it's working:

| Question | What it tests |
|---|---|
| "What metrics are available?" | Lists all parsed metrics from metric_logic |
| "How is [metric name] calculated?" | Reads calculation_logic, translates to business language |
| "What tables does [metric name] use?" | Returns source_tables from metric_logic |
| "/errors" | Queries parse_errors, shows error categories and explanations |
| "/coverage" | Shows how many metrics have logic, descriptions, stewards |

---

## Step 8: Set Up Automated Refresh (Optional)

To keep the knowledge graph up-to-date when SQL files change:

1. In your workspace, create a **Data Pipeline**
2. Add **Notebook Activities** for each pipeline step:
   - 02_parse → 03_build_graph → 04_build_metric_logic → 05_validate
3. Set a **Schedule Trigger** (recommended: weekly or after SQL deployments)
4. The pipeline will re-parse, rebuild the graph, and update the agent's data

---

## Troubleshooting

| Issue | Cause | Resolution |
|---|---|---|
| "No module named src" | sys.path not set | Ensure Cell 0 of each notebook has `sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")` |
| "ScriptDom not available" | DLL not found | Verify DLL is at `Files/sql-query-agent/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll` |
| "Failed to initialize Python.Runtime.dll" | pythonnet already loaded | Stop and restart the session. Don't run `%pip install pythonnet` after ScriptDom is loaded. |
| Agent says "no calculation logic" | metric_logic not added as data source | Add `metric_logic` table as a data source in the Data Agent configuration |
| Parse rate below 95% | Unusual SQL patterns | Check `parse_errors` table for error_category and suggested_action |
| 0 tables in graph | Data dictionary not loaded | Load dict_tables and dict_columns before running 03_build_graph |

---

## Delta Table Reference

| Table | Written By | Purpose |
|---|---|---|
| `sql_sources` | load_sql_files | Raw SQL text from your .sql files |
| `dict_tables` | load_clarity_dictionary | Table descriptions from data dictionary |
| `dict_columns` | load_clarity_dictionary | Column descriptions from data dictionary |
| `parse_results` | 02_parse | Parsed CTEs, tables, deps (intermediate) |
| `parse_errors` | 02_parse | Failed parses with explanations |
| `parse_successes` | 02_parse | Successful parses with CTE/table counts |
| `graph_nodes` | 03_build_graph | Knowledge graph nodes (canonical, transform, technical) |
| `graph_edges` | 03_build_graph | Knowledge graph edges |
| `metric_logic` | 04_build_metric_logic | Flattened view for the Data Agent |
| `pipeline_validation` | 05_validate | Per-metric health check results |
| `build_summary` | 05_validate | Pipeline run history (append-only) |

---

## Support

If you encounter issues not covered in this guide:

- Email: support@aiviaapp.com
- Include: error message, notebook cell number, and screenshot if possible
