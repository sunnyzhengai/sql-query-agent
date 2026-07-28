# Deployment Checklist

**Purpose:** Step-by-step checklist for deploying the SQL Intelligence Agent to a customer's Fabric workspace. This is the master plan — every step must be completed and verified before handoff.

**Audience:** Internal deployment team (us) and eventually automated by the product.

**Goal:** Customer goes from "purchased" to "first question answered" in under 30 minutes.

---

## Pre-Deployment: What We Ship vs. What Customer Provides

### We Ship (packaged, no customer action)

- [ ] `src/` — Core Python library (parser, graph builder, traversal, adapters)
- [ ] Pipeline notebooks (01-06) — pre-configured, numbered for run order
- [ ] `libs/` — ScriptDom DLL (Microsoft.SqlServer.TransactSql.ScriptDom.dll)
- [ ] `environment/requirements.txt` — pinned dependency list for Fabric Environment
- [ ] `config/org_config.yaml` — pre-filled with defaults, customer overrides org name only
- [ ] Data Agent instructions — baked into setup, not a separate copy-paste step
- [ ] `installation_errors` knowledge base — pre-seeded error signatures for `/troubleshoot`
- [ ] This checklist and the Data Dictionary Requirements doc

### Customer Provides

- [ ] Fabric workspace with F2+ capacity
- [ ] SQL files (.sql) — stored procedures and/or views from their data warehouse
- [ ] Data dictionary CSVs — `dict_tables.csv` and `dict_columns.csv` (see DATA_DICTIONARY_REQUIREMENTS.md)
- [ ] Contributor-level workspace access for the deployment account

---

## Phase 1: Environment Setup

**Goal:** Fabric workspace is ready to run code.

### 1.1 Create Fabric Environment

- [ ] Create Environment named `sql-logic-env` in the workspace
- [ ] Upload `environment/requirements.txt` as the pip requirements
- [ ] Publish the Environment and wait for build to complete (~5 minutes)
- [ ] Verify: Environment status shows "Published" with no build errors

**Packages installed:**
| Package | Version | Purpose |
|---|---|---|
| pydantic | 2.5.0 | Config validation |
| pyyaml | 6.0.1 | Config loading |
| sqlglot | 19.7.0 | SQL parsing (fallback for non-T-SQL) |
| sqlparse | 0.5.3 | SQL tokenization |
| pythonnet | 3.0.1 | .NET interop for ScriptDom |

### 1.2 Create Lakehouse

- [ ] Create Lakehouse named `Demo_Lakehouse` (or customer's preferred name)
- [ ] Verify: Lakehouse appears in workspace with Files/ and Tables/ sections

### 1.3 Upload Product Files

Upload the product package to `Files/sql-query-agent/`:

```
Demo_Lakehouse/Files/
└── sql-query-agent/
    ├── src/                    ← Core library (all .py files)
    ├── notebooks/pipeline/     ← Pipeline notebooks (01-06)
    ├── libs/                   ← ScriptDom DLL
    ├── config/                 ← org_config.yaml
    └── dictionary/             ← (empty — customer fills this)
```

- [ ] `src/` uploaded with all subpackages (parser/, graph/, extractor/, adapters/, governance/)
- [ ] `libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll` uploaded (from NuGet, netstandard2.0)
- [ ] `config/org_config.yaml` uploaded with defaults
- [ ] Verify: File count matches expected (`src/` = ~30 files, `notebooks/` = 6 files)

### 1.4 Import Notebooks

- [ ] Import all pipeline notebooks into the workspace Notebooks section
- [ ] Attach `sql-logic-env` Environment to each notebook
- [ ] Attach `Demo_Lakehouse` as the default Lakehouse for each notebook
- [ ] Verify: Each notebook shows the correct Environment and Lakehouse in the toolbar

---

## Phase 2: Customer Data Loading

**Goal:** Customer's SQL and dictionary are in the Lakehouse, ready for the pipeline.

### 2.1 Upload SQL Files

Customer uploads their .sql files to:

```
Demo_Lakehouse/Files/
└── sql-query-agent/
    └── sql_input/
        ├── reporting/          ← Optional: organize by schema
        │   ├── proc1.sql
        │   └── proc2.sql
        └── views/
            └── view1.sql
```

- [ ] SQL files are .sql extension (UTF-8 encoded)
- [ ] Files are T-SQL stored procedures or views with CREATE/ALTER PROCEDURE|VIEW statements
- [ ] Verify: At least 1 file is present

### 2.2 Upload Data Dictionary

Customer uploads their dictionary CSVs to:

```
Demo_Lakehouse/Files/
└── sql-query-agent/
    └── dictionary/
        ├── dict_tables.csv
        └── dict_columns.csv
```

- [ ] `dict_tables.csv` has header: `TABLE_NAME,DESCRIPTION`
- [ ] `dict_columns.csv` has header: `TABLE_NAME,COLUMN_NAME,DESCRIPTION`
- [ ] Both files are UTF-8 encoded
- [ ] TABLE_NAME values match table names in the SQL files (case-sensitive)
- [ ] Verify: Open each CSV in the Lakehouse file browser, confirm headers are correct

### 2.3 Configure org_config.yaml

Customer updates one field:

```yaml
org:
  name: "Their Health System Name"
```

- [ ] Org name is set (used in agent responses and metadata)
- [ ] All other defaults are correct for standard deployment

---

## Phase 3: Setup Notebook (01_install)

**Goal:** Delta tables created, data loaded, environment validated — all in one click.

### 3.1 Run `01_install` Notebook

This notebook does everything:

- [ ] **Environment check** — verifies `sql-logic-env` is attached, fails fast if not
- [ ] **ScriptDom check** — verifies DLL is present at expected path, fails fast if not
- [ ] **Create Delta table schemas** — creates all required tables if they don't exist:
  - `sql_sources` — input SQL files
  - `dict_tables` — table dictionary
  - `dict_columns` — column dictionary
  - `parse_results` — parsed CTE/table/column extractions
  - `parse_errors` — failed parses with explanations
  - `parse_successes` — successful parse summaries
  - `graph_nodes` — knowledge graph nodes (or typed LPG tables — TBD)
  - `graph_edges` — knowledge graph edges (or typed LPG tables — TBD)
  - `metric_logic` — flattened view for Data Agent
  - `pipeline_validation` — per-metric health check
  - `build_summary` — pipeline run history
  - `installation_errors` — known error signatures
- [ ] **Load SQL files** — reads all .sql from `Files/sql-query-agent/sql_input/` into `sql_sources`
- [ ] **Load dictionary** — reads CSVs from `Files/sql-query-agent/dictionary/` into `dict_tables`/`dict_columns`
- [ ] **Validate dictionary** — checks that TABLE_NAME values in dict match tables referenced in SQL
- [ ] **Seed installation errors** — populates `installation_errors` with known error signatures
- [ ] **Print summary** — shows counts and any warnings

### 3.2 Verify Setup Output

- [ ] "Setup complete" message with no errors
- [ ] `sql_sources` row count matches number of .sql files
- [ ] `dict_tables` row count matches CSV
- [ ] `dict_columns` row count matches CSV
- [ ] No "missing table" warnings (or known/accepted gaps)

---

## Phase 4: Run Pipeline

**Goal:** SQL is parsed, knowledge graph is built, agent data is ready.

### Option A: Fabric Data Pipeline (preferred — one click)

- [ ] Open the Data Pipeline
- [ ] Click "Run"
- [ ] Wait for all steps to complete (typically 1-5 minutes depending on SQL file count)
- [ ] Verify: Pipeline shows all green checkmarks

### Option B: Run Notebooks Manually (fallback)

Run in order:

1. [ ] `02_parse` — parses SQL files with ScriptDom
   - Verify: `parse_successes` has rows, `parse_errors` is empty or has known issues
2. [ ] `03_build_graph` — builds knowledge graph from parse results + dictionary
   - Verify: `graph_nodes` and `graph_edges` have rows
3. [ ] `04_build_metric_logic` — flattens graph for Data Agent
   - Verify: `metric_logic` has rows with calculation_logic and source_tables populated
4. [ ] **(If LPG) `05_export_graph_tables`** — exports typed tables for Graph Model
   - Verify: 8 graph tables have rows
5. [ ] `06_validate` — validates pipeline health
   - Verify: `pipeline_validation` shows coverage percentages

### 4.1 Pipeline Health Check

After pipeline completes, verify in `06_validate` output:

- [ ] Parse rate: >90% of SQL files parsed successfully
- [ ] Metrics with calculation logic: >80%
- [ ] Metrics with source tables mapped: >80%
- [ ] No unexpected parse errors (check `parse_errors` for new signatures)

---

## Phase 5: Data Agent Configuration

**Goal:** Users can ask natural language questions and get answers.

### 5.1 Create Data Agent (if not pre-provisioned)

- [ ] Open Fabric workspace → New → Data Agent
- [ ] Name: "SQL Intelligence Agent" (or customer's preferred name)
- [ ] Add `metric_logic` table as a data source
- [ ] Add `parse_errors` table as a data source (for `/errors` command)
- [ ] Add `pipeline_validation` table as a data source (for `/coverage` command)

### 5.2 Configure Agent Instructions

- [ ] Paste agent instructions (from `notebooks/data_agent_instructions.md` or generated by setup)
- [ ] Verify instructions include:
  - [ ] Rule: "ALWAYS query the data" (never hardcode answers)
  - [ ] Rule: PHI protection (#7)
  - [ ] Rule: Broad search (#8)
  - [ ] Commands: `/errors`, `/coverage`, `/troubleshoot`
  - [ ] No metric-specific examples (teaches HOW to query, not specific answers)

### 5.3 Test the Agent

Run the golden path test scenarios:

| # | Question | Expected behavior |
|---|---|---|
| 1 | "What metrics are available?" | Lists all metrics from metric_logic |
| 2 | "How is [metric name] calculated?" | Shows calculation logic in plain English |
| 3 | "What tables feed into [metric name]?" | Shows source tables with descriptions |
| 4 | "/coverage" | Shows system health percentages |
| 5 | "/errors" | Shows parse errors with explanations (or "no errors") |

- [ ] All 5 scenarios return correct, non-empty responses
- [ ] Agent does NOT hallucinate or make up answers
- [ ] Agent correctly says "I don't have that information" for unknown metrics

---

## Phase 6: Graph Backend (TBD — pending LPG validation)

> **This section will be filled in after the LPG vs. Delta decision is made.**

### If Delta Only (current)
- [ ] No additional steps — metric_logic table is the agent's data source

### If LPG (Fabric Graph)
- [ ] Create Graph Model in Fabric workspace
- [ ] Map 8 source tables to node/edge types in Graph Model editor
- [ ] Configure FabricGraphBackend connection in org_config.yaml
- [ ] Run comparison script to validate LPG matches Delta results
- [ ] Switch Data Agent to use Graph-backed traversal

---

## Phase 7: Handoff & Validation

**Goal:** Customer is self-sufficient.

### 7.1 Documentation Handoff

- [ ] DATA_DICTIONARY_REQUIREMENTS.md — how to update their dictionary
- [ ] REVIEWER_GUIDE.md — how to use the agent (test scenarios)
- [ ] DEPLOYMENT_GUIDE.md — how to re-run the pipeline after SQL changes

### 7.2 Final Validation

- [ ] Customer can independently ask the agent a question and get a correct answer
- [ ] Customer knows how to re-run the pipeline when they update SQL files
- [ ] Customer knows how to update the data dictionary
- [ ] `/troubleshoot` command works and returns relevant help for common errors

### 7.3 Sign-Off

- [ ] All Phase 1-6 checkboxes are checked
- [ ] Customer confirms agent answers are accurate for their domain
- [ ] No open issues or workarounds documented

---

## Quick Reference: What Goes Wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| "No documented calculation logic" | Agent instructions have hardcoded examples | Remove examples, use teaching rules only |
| "0 source tables" for a metric | Tables not in data dictionary | Add tables to dict_tables.csv, re-run pipeline |
| Parse errors on all files | ScriptDom DLL not loaded | Check 01_install output, verify DLL path |
| pythonnet initialization fails | `%pip install` was used in a notebook | Remove %pip, use Fabric Environment only |
| Agent gives wrong table names | Dictionary TABLE_NAME doesn't match SQL | Fix casing in dict_tables.csv |
| Pipeline runs but metric_logic is empty | No parse_results (parse step failed) | Check parse_errors, run 02_parse with verbose |

---

## Timing Estimates

| Phase | Duration | Who |
|---|---|---|
| 1. Environment Setup | 10-15 min | Deployment team |
| 2. Customer Data Loading | 5-10 min | Customer (with guidance) |
| 3. Setup Notebook | 2-3 min | Automated |
| 4. Run Pipeline | 1-5 min | Automated |
| 5. Data Agent Config | 5-10 min | Deployment team |
| 6. Graph Backend | TBD | TBD |
| 7. Handoff | 15-20 min | Deployment team + customer |
| **Total** | **~45-60 min** | |
