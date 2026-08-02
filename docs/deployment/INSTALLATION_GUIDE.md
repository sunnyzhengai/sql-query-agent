# Installation Guide for Administrators

**Purpose:** Step-by-step installation instructions for the customer's IT or data team. Follow every step in order. Each step includes a verification check — do not proceed until the check passes.

> This is the **canonical installation document**. If any other document
> disagrees with it about installation steps, this one wins.

**Time:** ~30 minutes (plus Environment publish time)

---

## Prerequisites

Before starting, confirm you have:

- [ ] Microsoft Fabric workspace with **F2+ capacity** (F4 recommended for production)
- [ ] **Contributor** role or higher in the workspace
- [ ] The deployment package (provided by your vendor), containing:
  - `sql_query_agent-<version>-py3-none-any.whl` — the product library
  - `org_config.yaml` — configuration file
  - `Microsoft.SqlServer.TransactSql.ScriptDom.dll` — SQL parser engine
  - Pipeline notebooks (01-09)
  - Data Agent instructions file
- [ ] Your organization's SQL files (`.sql` stored procedures and/or views)
- [ ] Your data dictionary CSVs (`dict_tables.csv`, `dict_columns.csv`) — see DATA_DICTIONARY_REQUIREMENTS.md

---

## Step 1: Create the Fabric Environment

The Environment pre-installs all required Python packages so notebooks don't need `%pip install` (which breaks the SQL parser).

1. Open your Fabric workspace
2. Click **+ New** → **Environment**
3. Name it: `sql-logic-env`

### 1a: Add Python packages

4. Go to **External repositories** (left sidebar)
5. Click **Add library** and add each package from PyPI:

| Package | Version |
|---|---|
| `pydantic` | 2.5.0 |
| `pyyaml` | 6.0.1 |
| `sqlglot` | 19.7.0 |
| `sqlparse` | 0.5.3 |
| `pythonnet` | 3.0.1 |

### 1b: Upload the product wheel

6. Go to **Custom** (left sidebar)
7. Click **Upload**
8. Select `sql_query_agent-<version>-py3-none-any.whl` from the deployment package
   - **Note:** Navigate to the correct folder — the file picker only shows `.whl`, `.jar`, and `.tar.gz` files. Text files like `requirements.txt` will be grayed out. That's expected.

### 1c: Publish

9. Click **Publish** in the top toolbar
10. Wait for the build to complete (~5 minutes)

**Verification:**
- [ ] Environment status shows **"Published"** with no build errors
- [ ] All 5 packages listed under External repositories
- [ ] The `.whl` file listed under Custom libraries

> **You can proceed to Step 2 while the Environment publishes.** The Lakehouse and file uploads don't depend on the Environment.

---

## Step 2: Create the Lakehouse

1. Go to your workspace
2. Click **+ New** → **Lakehouse**
3. Name it: `sql_query_lh` (or your preferred name)

**Verification:**
- [ ] Lakehouse appears in workspace with **Files/** and **Tables/** sections

---

## Step 3: Upload Product Files

In the Lakehouse, create the folder structure under **Files/**:

### 3a: Create folders

Right-click **Files/** → **New subfolder** → `sql-query-agent`

Then right-click `sql-query-agent` → **New subfolder** for each:
- `libs`
- `sql_input`
- `dictionary`

**Target structure:**
```
Files/
└── sql-query-agent/
    ├── libs/                  ← ScriptDom DLL
    ├── sql_input/             ← your .sql files
    ├── dictionary/            ← dict_tables.csv + dict_columns.csv
    └── org_config.yaml        ← config file (NOT in a subfolder)
```

### 3b: Upload the ScriptDom DLL

1. Navigate to `Files/sql-query-agent/libs/`
2. Upload `Microsoft.SqlServer.TransactSql.ScriptDom.dll`

> **If you don't have the DLL:** Download from NuGet at https://www.nuget.org/packages/Microsoft.SqlServer.TransactSql.ScriptDom — rename `.nupkg` to `.zip`, extract, and use the file from `lib/netstandard2.0/`. Do NOT use files from other subfolders (like `net462` or localized resource DLLs).

### 3c: Upload configuration

1. Navigate to `Files/sql-query-agent/` (the root, NOT a subfolder)
2. Upload `org_config.yaml`
3. Edit the file and set your organization name:
   ```yaml
   org:
     name: "Your Health System Name"
   ```

> **Common mistake:** Do NOT put `org_config.yaml` inside a `config/` subfolder. The notebooks look for it at `Files/sql-query-agent/org_config.yaml` directly.

### 3d: Upload SQL files

1. Navigate to `Files/sql-query-agent/sql_input/`
2. Upload all your `.sql` files — flat or in subfolders, either works

> **How metric identity works:** The pipeline does NOT use the filename as the metric identity. Instead, it reads the `CREATE PROCEDURE` or `CREATE VIEW` statement (`[schema].[object_name]`) inside each SQL file and extracts the **schema + object name** as the unique identifier (e.g., `reporting.USP_IP_SEPSIS`). This means:
> - You do NOT need to rename files or follow any naming convention
> - Two objects with the same name in different schemas (e.g., `[reporting].[USP_ED_Sepsis]` and `[reports].[USP_ED_Sepsis]`) are tracked as separate metrics automatically
> - The identity always comes from the SQL content, not the filename
> - If two files define the **same** `[schema].[object]`, the installer stops and lists the colliding files — each metric must have exactly one definition. Remove or rename the extra file before re-running.

> **IMPORTANT — Upload conflicts:** Even though the pipeline handles identity correctly, the **file upload itself** can have conflicts. If two files have the same filename (e.g., two different `USP_ED_Sepsis.sql` from different schemas), uploading them to a flat folder will overwrite one. **Fix:** Either:
> - **Preserve subfolders** — upload into `sql_input/reporting/` and `sql_input/reports/` to keep them separate
> - **Or rename one file** — add any prefix (e.g., `RPT_USP_ED_Sepsis.sql`). The filename doesn't matter — the identity comes from the SQL content inside.

**Checklist for SQL files:**
- [ ] All files have `.sql` extension
- [ ] All files are **T-SQL** (Microsoft SQL Server dialect) — other dialects (PL/SQL, PostgreSQL) are not supported in this version
- [ ] Each file contains a `CREATE PROCEDURE`, `ALTER PROCEDURE`, `CREATE VIEW`, or `ALTER VIEW` statement
- [ ] All filenames are **unique** across the upload folder (no duplicates)
- [ ] Files are **UTF-8 encoded** (not ANSI or Latin-1)

### 3e: Upload data dictionary

1. Navigate to `Files/sql-query-agent/dictionary/`
2. Upload `dict_tables.csv` and `dict_columns.csv`

**Checklist for dictionary files:**
- [ ] `dict_tables.csv` has header row: `TABLE_NAME,DESCRIPTION`
- [ ] `dict_columns.csv` has header row: `TABLE_NAME,COLUMN_NAME,DESCRIPTION`
- [ ] Both files are UTF-8 encoded
- [ ] `TABLE_NAME` values match the table names used in your SQL files (case matters for display, but matching is case-insensitive)
- [ ] See DATA_DICTIONARY_REQUIREMENTS.md for complete format specification

**Verification:**
- [ ] All 3 subfolders (`libs/`, `sql_input/`, `dictionary/`) exist under `sql-query-agent/`
- [ ] `libs/` contains exactly 1 DLL file
- [ ] `org_config.yaml` is at the `sql-query-agent/` root (NOT in a subfolder) with your org name
- [ ] `sql_input/` contains your `.sql` files (check count)
- [ ] `dictionary/` contains both CSV files

---

## Step 4: Import Notebooks

1. Go to your workspace
2. For each notebook file (01_install through 09_publish_purview):
   a. Click **+ New** → **Import notebook**
   b. Upload the notebook `.py` file
3. For each imported notebook:
   a. Open it
   b. In the toolbar, click the **Environment** dropdown → select `sql-logic-env`
   c. In the left sidebar, click **Lakehouses** → **Add** → select your Lakehouse

> **Note:** The notebooks are numbered for run order. 01-06 are required; 07-09 are optional (description generation and catalog publishing).

**Verification:**
- [ ] All 9 pipeline notebooks imported (01 through 09)
- [ ] Each notebook shows `sql-logic-env` as its Environment
- [ ] Each notebook shows your Lakehouse in the left sidebar

---

## Step 5: Run the Pipeline

Run notebooks in order. **Wait for each to complete before starting the next.**

### 5a: Install & validate setup

1. Open `01_install`
2. Click **Run all**

This one notebook validates the Environment and DLL, creates all Delta tables,
loads your SQL files and dictionary CSVs, and prints a PASS/FAIL summary.
It is idempotent — safe to re-run; it will not destroy existing data.

**Verification:**
- [ ] PASS summary with no errors (any FAIL line names the exact file or setting to fix)
- [ ] `input_sql_sources` row count matches your .sql file count
- [ ] `input_dict_tables` / `input_dict_columns` row counts match your CSVs

### 5b: Parse SQL files

1. Open `02_parse`
2. Click **Run all**
3. Wait for completion (~30 seconds to 5 minutes depending on file count)

**Verification:**
- [ ] Output shows "ScriptDom loaded!"
- [ ] `ops_parse_successes` count > 0
- [ ] `ops_parse_errors` count is 0 or contains only known issues
- [ ] No `%pip install` errors (if you see kernel restart errors, the Environment is not attached)

### 5c: Build knowledge graph

1. Open `03_build_graph`
2. Click **Run all**

**Verification:**
- [ ] Output shows node and edge counts (e.g., "Built graph: 5000 nodes, 2500 edges")
- [ ] `graph_nodes` table exists in the Lakehouse Tables section
- [ ] `graph_edges` table exists

### 5d: Build metric logic

1. Open `04_build_metric_logic`
2. Click **Run all**

**Verification:**
- [ ] `output_metric_logic` table exists with rows
- [ ] "With calculation logic" count > 80% of total

### 5e: Export graph tables

1. Open `05_export_graph_tables`
2. Click **Run all**

**Verification:**
- [ ] 8 graph tables created (graph_canonical, graph_transformation, etc.)

### 5f: Validate pipeline

1. Open `06_validate`
2. Click **Run all**

**Verification:**
- [ ] **DEPLOYMENT READY** message appears (not DEPLOYMENT BLOCKED)
- [ ] Parse rate > 90%
- [ ] Calculation logic > 80%
- [ ] Dictionary coverage > 90%
- [ ] If DEPLOYMENT BLOCKED: resolve the listed issues before proceeding

### Optional notebooks (after the agent is working)

- `07_generate_descriptions` — LLM-generated business descriptions for metrics
- `08_publish_collibra` / `09_publish_purview` — push metadata to your catalog
  (requires adapter credentials in `org_config.yaml`)

---

## Step 6: Configure the Data Agent

1. Go to your workspace
2. Click **+ New** → **Data Agent** (or use the **Add to data agent** button in the Lakehouse)
3. Name it: `SQL Intelligence Agent`
4. Add these tables as data sources:
   - `output_metric_logic`
   - `ops_parse_errors`
   - `ops_pipeline_validation`
   - `ops_installation_errors`
   - `graph_nodes`
   - `graph_edges`
5. Open the Agent's **Instructions** panel
6. Paste the contents of `data_agent_instructions.md`
7. Click **Publish**

### Test the Agent

Ask these questions to verify it's working:

| Question | Expected response |
|---|---|
| "What metrics are available?" | Lists metrics from the graph |
| "How is [pick a metric name] calculated?" | Shows business logic explanation |
| "/coverage" | Shows system health percentages |
| "/errors" | Shows parse errors (or "no errors") |

**Verification:**
- [ ] Agent returns meaningful answers (not empty or error)
- [ ] Agent does NOT hallucinate or reference metrics that don't exist
- [ ] Agent correctly says "I don't have that information" for unknown topics

---

## Common Installation Issues

| Problem | Symptom | Fix |
|---|---|---|
| Environment not attached | `ModuleNotFoundError: No module named 'src'` | Open notebook → toolbar → Environment dropdown → select `sql-logic-env` |
| Lakehouse not attached | `Table not found` errors | Open notebook → left sidebar → Lakehouses → Add your lakehouse |
| Wrong DLL file | `ScriptDom loaded!` never appears, or `Assembly.LoadFrom` error | Re-download from NuGet, use `lib/netstandard2.0/` version only |
| DLL in wrong folder | `FileNotFoundException` for the DLL | Must be at `Files/sql-query-agent/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll` |
| pythonnet init failure | `CLR has already been initialized` or kernel crash | Never use `%pip install` in notebooks — the Environment handles all packages |
| Duplicate SQL filenames | Only one file loaded, missing metrics | Add a prefix to filenames from different schemas (e.g., `RPT_`, `ETL_`) |
| Dictionary TABLE_NAME mismatch | "0 source tables" for metrics | TABLE_NAME in CSV must match the table names in your SQL files |
| Dictionary not UTF-8 | Garbled characters in descriptions | Re-save CSV as UTF-8 (not ANSI/Latin-1) |
| `org_config.yaml` not found | `FileNotFoundError` at notebook start | Must be at `Files/sql-query-agent/org_config.yaml` (the root, not a subfolder) |
| Environment publish failed | Red error during publish | Check for version conflicts — try removing one package at a time to isolate |
| Token expired during long run | `401: User Aad Token is expired` | Restart kernel and re-run — results are saved incrementally |
| Cross-region capacity error | Silent query failures from Data Agent | Workspace capacity, Lakehouse, and Data Agent must all be in the same Azure region |

---

## Post-Installation: Re-running the Pipeline

When your SQL files change (new procs added, existing ones modified):

1. Upload new/updated `.sql` files to `Files/sql-query-agent/sql_input/`
2. Run notebooks 02 → 03 → 04 → 05 → 06 in order
3. The Data Agent automatically uses the updated `output_metric_logic` table

When your data dictionary changes:

1. Upload updated CSVs to `Files/sql-query-agent/dictionary/`
2. Re-run notebooks 03 → 04 → 05 → 06 (skip 02 — no need to re-parse)

### Automated refresh (optional)

To keep the knowledge graph up to date without manual runs:

1. In your workspace, create a **Data Pipeline**
2. Add **Notebook Activities** in order: 02_parse → 03_build_graph → 04_build_metric_logic → 05_export_graph_tables → 06_validate
3. Set a **Schedule Trigger** (recommended: weekly, or after SQL deployments)
4. The Data Agent automatically uses the refreshed tables

---

## Support

If you encounter issues not covered in this guide:

- Email: support@aiviaapp.com
- Include: the error message, which notebook and cell it occurred in, and a screenshot if possible

---

## File Reference

| File | Location in Lakehouse | Purpose |
|---|---|---|
| ScriptDom DLL | `Files/sql-query-agent/libs/` | SQL parser engine |
| org_config.yaml | `Files/sql-query-agent/` | Configuration |
| *.sql files | `Files/sql-query-agent/sql_input/` | Your SQL stored procedures/views |
| dict_tables.csv | `Files/sql-query-agent/dictionary/` | Table descriptions |
| dict_columns.csv | `Files/sql-query-agent/dictionary/` | Column descriptions |

| Delta Table | Domain | Purpose |
|---|---|---|
| `input_sql_sources` | Input | Loaded SQL files |
| `input_dict_tables` | Input | Table dictionary |
| `input_dict_columns` | Input | Column dictionary |
| `ops_parse_results` | Operations | Parsed SQL structure (JSON) |
| `ops_parse_errors` | Operations | Failed parses with explanations |
| `ops_parse_successes` | Operations | Successful parse summaries |
| `ops_build_summary` | Operations | Pipeline run history |
| `ops_pipeline_validation` | Operations | Per-metric health check |
| `ops_installation_errors` | Operations | Known error signatures |
| `graph_nodes` | Graph | Knowledge graph nodes |
| `graph_edges` | Graph | Knowledge graph edges |
| `graph_canonical` | Graph (LPG) | Business metric nodes |
| `graph_transformation` | Graph (LPG) | SQL transformation nodes |
| `graph_technical` | Graph (LPG) | Source table/column nodes |
| `graph_dimension` | Graph (LPG) | Dimension nodes |
| `graph_edge_c2t` | Graph (LPG) | Canonical → Transform edges |
| `graph_edge_t2t` | Graph (LPG) | Transform → Transform edges |
| `graph_edge_t2tech` | Graph (LPG) | Transform → Technical edges |
| `graph_edge_tech2dim` | Graph (LPG) | Technical → Dimension edges |
| `output_metric_logic` | Output | Flattened table for Data Agent |
| `gov_steward_assignments` | Governance | Metric ownership |
