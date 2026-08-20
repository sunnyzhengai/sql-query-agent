# Deployment Checklist

**Purpose:** Step-by-step checklist for deploying the SQL Intelligence Agent to a customer's Fabric workspace. This is the master plan — every step must be completed and verified before handoff.

**Audience:** Internal deployment team (us) and eventually automated by the product.

**Goal:** Customer goes from "purchased" to "first question answered" in under 30 minutes.

---

## Architecture Decisions (Finalized)

| Decision | Choice | Rationale |
|---|---|---|
| Storage layer | Both Delta + LPG | Build both; ship Delta for Data Agent, LPG tables populated for future self-service report generation |
| Data Agent grounding | `metric_logic` (Delta flat table) | Simpler, proven, no Graph Model setup for customer |
| LPG tables | Exported automatically by pipeline | 9 typed tables populated silently — no customer action |
| Data dictionary | **Mandatory** | Without it, agent gives incomplete/misleading answers |
| Collibra integration | Optional add-on (Phase 7) | For customers with Collibra — publishes AI-generated descriptions to PBI report assets |

---

## Pre-Deployment: What We Ship vs. What Customer Provides

### We Ship (packaged, no customer action)

- [ ] `src/` — Core Python library (parser, graph builder, traversal, adapters)
- [ ] Pipeline notebooks (01-09) — pre-configured, numbered for run order
- [ ] `libs/` — ScriptDom DLL (Microsoft.SqlServer.TransactSql.ScriptDom.dll)
- [ ] `environment/requirements.txt` — pinned dependency list for Fabric Environment
- [ ] `org_config.yaml` (at package root) — pre-filled with defaults, customer overrides org name only
- [ ] Data Agent instructions — shipped with product, customer does not modify
- [ ] `installation_errors` knowledge base — pre-seeded error signatures for `/troubleshoot`
- [ ] This checklist and the Data Dictionary Requirements doc

### Customer Provides

- [ ] Fabric workspace with F2+ capacity
- [ ] SQL files (.sql) — stored procedures and/or views from their data warehouse
- [ ] Data dictionary CSVs — `dict_tables.csv` and `dict_columns.csv` (**mandatory** — see DATA_DICTIONARY_REQUIREMENTS.md)
- [ ] Contributor-level workspace access for the deployment account
- [ ] *(Optional, Phase 7)* Collibra API credentials and domain ID

---

## Phase 1: Environment Setup

**Goal:** Fabric workspace is ready to run code.

### 1.0 Pre-Flight Checks

Before creating anything, verify the workspace meets requirements:

- [ ] **Capacity SKU:** F2 or higher (F4 recommended for production workloads)
- [ ] **Region alignment:** Workspace capacity, Lakehouse, and Data Agent must all be in the **same Azure region**. Cross-region configurations cause silent query failures or capacity errors. Check: Workspace Settings → Capacity → Region.
- [ ] **Workspace role:** Deployment account has Contributor role or higher
- [ ] **Security & access control:**
  - [ ] Verify workspace access control list (ACL) — only authorized users should have access
  - [ ] If customer uses Microsoft Purview sensitivity labels, verify labels are configured for the Lakehouse tables
  - [ ] Confirm no row-level security (RLS) conflicts with the Data Agent's service principal
  - [ ] Review: Data Agent responses are derived from SQL logic metadata, NOT raw patient data — but workspace permissions must still follow customer's governance policies

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
    ├── notebooks/pipeline/     ← Pipeline notebooks (01-09)
    ├── libs/                   ← ScriptDom DLL
    ├── org_config.yaml         ← config (at the root, NOT a subfolder)
    └── dictionary/             ← (empty — customer fills this)
```

- [ ] `src/` uploaded with all subpackages (parser/, graph/, extractor/, adapters/, governance/)
- [ ] `libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll` uploaded (from NuGet, netstandard2.0)
- [ ] `org_config.yaml` uploaded to `Files/sql-query-agent/` (root) with defaults
- [ ] Verify: File count matches expected (`src/` = ~30 files, `notebooks/` = 7 files)

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
- [ ] **This release supports T-SQL (Microsoft SQL Server) only.** The primary parser (ScriptDom) is a native T-SQL parser. Non-T-SQL files (PL/SQL, PgSQL, Snowflake SQL) are not supported in this version. Future releases will add multi-dialect support via a dialect adapter layer — the pipeline architecture is designed for this, but only the T-SQL adapter is implemented today.
- [ ] Files contain `CREATE PROCEDURE`, `ALTER PROCEDURE`, `CREATE VIEW`, or `ALTER VIEW` statements
- [ ] Verify: At least 1 file is present

### 2.2 Upload Data Dictionary (Mandatory)

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
- [ ] TABLE_NAME values match table names in the SQL files (matching is case-insensitive, mirroring SQL Server collation — ADR 0016)
- [ ] Verify: Open each CSV in the Lakehouse file browser, confirm headers are correct
- [ ] Refer customer to DATA_DICTIONARY_REQUIREMENTS.md for format details and extraction queries

### 2.3 Configure org_config.yaml

Customer updates one field:

```yaml
org:
  name: "Their Health System Name"
```

- [ ] Org name is set (used in agent responses and metadata)
- [ ] All other defaults are correct for standard deployment

---

## Phase 3: Setup Notebook (100_install)

**Goal:** Delta tables created, data loaded, environment validated — all in one click.

### 3.1 Run `100_install` Notebook

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
  - `graph_nodes` — knowledge graph nodes
  - `graph_edges` — knowledge graph edges
  - `graph_canonical` — LPG: canonical metric nodes
  - `graph_transformation` — LPG: transformation nodes
  - `graph_technical` — LPG: technical table/column nodes
  - `graph_dimension` — LPG: dimension nodes
  - `graph_edge_c2t` — LPG: canonical-to-transform edges
  - `graph_edge_t2t` — LPG: transform-to-transform edges
  - `graph_edge_t2tech` — LPG: transform-to-technical edges
  - `graph_edge_tech2dim` — LPG: technical-to-dimension edges
  - `metric_logic` — flattened view for Data Agent
  - `agent_descriptions` — AI-generated descriptions (for Collibra publish)
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

1. [ ] `200_parse` — parses SQL files with ScriptDom
   - Verify: `parse_successes` has rows, `parse_errors` is empty or has known issues
2. [ ] `300_build_graph` — builds knowledge graph from parse results + dictionary
   - Verify: `graph_nodes` and `graph_edges` have rows
3. [ ] `400_build_metric_logic` — flattens graph for Data Agent
   - Verify: `metric_logic` has rows with `calculation_logic` and `source_tables` populated
4. [ ] `800_export_graph_tables` — exports typed tables for LPG (automatic, no config needed)
   - Verify: 9 graph tables have rows (4 node tables, 5 edge tables)
5. [ ] `500_validate` — validates pipeline health
   - Verify: `pipeline_validation` shows coverage percentages

### 4.1 Pipeline Health Check (Automated Gate)

The `500_validate` notebook enforces minimum coverage thresholds. If any threshold is not met, the notebook outputs a **DEPLOYMENT BLOCKED** warning with the specific gap. The deployment team must resolve the gap before proceeding to Phase 5.

| Metric | Minimum threshold | Blocking? |
|---|---|---|
| Parse rate | >90% of SQL files parsed | **Yes** — below this, too many metrics are missing |
| Metrics with calculation logic | >80% | **Yes** — agent can't answer questions about these |
| Metrics with source tables mapped | >70% | Warning — agent works but shows "0 source tables" |
| Dictionary coverage (tables in SQL found in dict) | >90% | **Yes** — missing tables degrade all answers |

After pipeline completes, verify:

- [ ] `500_validate` output shows all thresholds met (no DEPLOYMENT BLOCKED warnings)
- [ ] Parse rate meets threshold
- [ ] Calculation logic coverage meets threshold
- [ ] Dictionary coverage meets threshold
- [ ] Review `parse_errors` for any unexpected failures

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

- [ ] Paste agent instructions (shipped with product in `notebooks/delta_agent_instructions.md`)
- [ ] Verify instructions include:
  - [ ] Rule: "ALWAYS query the data" (never hardcode answers)
  - [ ] Rule: PHI protection
  - [ ] Rule: Broad search (case-insensitive, partial match)
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

**Known limitation — response truncation:** Fabric Data Agents may truncate or summarize long list responses. If the customer has 100+ metrics, "What metrics are available?" may return a partial list. The agent instructions should direct users to ask narrower questions (e.g., "What sepsis metrics are available?") or use `/coverage` for a complete count. This is a platform behavior, not a product bug.

---

## Phase 6: Graph Export (Automatic)

**Goal:** LPG tables are populated for future use. No customer action required.

The pipeline step `800_export_graph_tables` automatically populates 9 typed Delta tables from the knowledge graph. These tables are structured for future Fabric Graph Model ingestion when the self-service report generation feature is released.

**Tables created:**

| Table | Contents |
|---|---|
| `graph_canonical` | Business metric nodes (name, description, steward) |
| `graph_transformation` | SQL transformation nodes (metric_id, sql_fragment) |
| `graph_technical` | Source table/column nodes (schema, database, description) |
| `graph_dimension` | Dimension nodes (table, column, description) |
| `graph_edge_c2t` | Canonical → Transformation edges |
| `graph_edge_t2t` | Transformation → Transformation edges |
| `graph_edge_t2tech` | Transformation → Technical edges |
| `graph_edge_tab2col` | Technical table → column edges |
| `graph_edge_tech2dim` | Technical → Dimension edges |

- [ ] Verify: All 8 tables exist and have rows after pipeline run
- [ ] No customer configuration needed — this is fully automated

---

## Phase 7: Collibra Integration (Optional)

**Goal:** AI-generated report descriptions published to Collibra PBI report assets.

> **Skip this phase** if the customer does not use Collibra. This is a premium add-on feature.

### Prerequisites

- [ ] Phases 1-5 are complete and Data Agent is working
- [ ] Customer has Collibra with Power BI integration (reports ingested as assets)
- [ ] Customer's SQL procs/views follow the `_PBI` naming convention (procs that feed Power BI end in `_PBI`)
- [ ] Customer provides Collibra API credentials (API key or username/password)
- [ ] Customer provides Collibra domain ID and community ID

### 7.1 Configure Collibra in org_config.yaml

```yaml
adapters:
  collibra:
    base_url: "https://customer-org.collibra.com/rest/2.0"
    api_key: "their-api-key"        # or use username/password
    domain_id: "their-domain-id"
    community_id: "their-community-id"

fabric_graph:
  workspace_id: "their-workspace-id"
  data_agent_id: "their-agent-id"
```

- [ ] Collibra base URL is correct and accessible
- [ ] API credentials have write access to the target domain
- [ ] Fabric workspace and Data Agent IDs are set

### 7.2 Run Discovery (Optional — First-Time Only)

Run `notebooks/utilities/collibra_discovery.py` to verify Collibra connectivity:

- [ ] Successfully connects to Collibra API
- [ ] Finds PBI Report assets in the target domain
- [ ] Shows asset type IDs and relation types

### 7.3 Run `900_publish_collibra` Notebook

This notebook orchestrates the full flow:

1. **Loads knowledge graph** from Delta tables
2. **Identifies `_PBI` metrics** — filters canonical nodes with `_PBI` suffix
3. **Generates descriptions** via Data Agent — sends each metric to the agent, which translates SQL logic into business language. Descriptions are persisted to `agent_descriptions` Delta table.
4. **Matches to Collibra** — fuzzy-matches metric names to PBI Report assets in Collibra
5. **Review step** — prints matched and unmatched items for human review before publishing
6. **Publishes** — writes AI-generated descriptions to Collibra Report assets' Description attribute
7. **Summary** — prints counts (total, matched, published, failed, unmatched)

### 7.4 Verify Results

- [ ] Review the match summary — confirm matches are correct before publishing
- [ ] After publish: check 2-3 reports in Collibra UI to verify descriptions appeared
- [ ] Verify descriptions are accurate (correct SQL logic translation, no hallucinations)
- [ ] Check for unmatched reports — may need manual review or naming convention adjustment

### 7.5 Collibra Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| 0 matches found | Procs don't follow `_PBI` naming convention | Rename procs or adjust match threshold |
| 401/403 from Collibra API | API key lacks write permissions | Get write access to the target domain |
| Description is wrong/hallucinated | Agent instructions need tuning | Review and update agent persona instructions |
| Report matched to wrong proc | Fuzzy match scored wrong candidate | Review matches in step 5, exclude false matches |
| "Asset not found" on publish | Report name in Collibra doesn't match expected format | Run discovery notebook, check exact asset names |

---

## Phase 8: Automated Acceptance Testing

**Goal:** Programmatically verify the deployment works end-to-end before human handoff.

> Manual golden-path testing (Phase 5.3) validates the UI experience. This phase validates the system programmatically — catching issues that manual testing might miss.

### 8.1 Run Acceptance Test Script

The acceptance test script (`scripts/acceptance_test.py`) programmatically validates:

1. **Delta table integrity** — all required tables exist and have expected row counts
2. **metric_logic completeness** — every metric has non-null `calculation_logic` and `source_tables`
3. **Dictionary coverage** — cross-references SQL table refs against dict_tables
4. **Parse error review** — flags any new error signatures not in `installation_errors`
5. **Agent smoke test** (if Fabric REST API access is available) — fires 3 test questions against the Data Agent endpoint and asserts:
   - Response status is 200
   - Response contains expected keywords (not empty, not error)
   - No hallucination indicators (response references tables that exist in the graph)

### 8.2 Acceptance Criteria

| Check | Pass condition | Blocking? |
|---|---|---|
| All Delta tables exist | 11+ tables with rows | **Yes** |
| metric_logic row count | > 0, matches parse_successes count | **Yes** |
| calculation_logic populated | > 80% of metrics have non-null logic | **Yes** |
| source_tables populated | > 70% of metrics have non-null tables | Warning |
| Dictionary coverage | > 90% of SQL tables found in dict | **Yes** |
| Agent smoke test (if available) | 3/3 queries return valid responses | **Yes** |

- [ ] Acceptance test script passes with no blocking failures
- [ ] Any warnings are reviewed and documented

---

## Phase 9: Handoff & Validation

**Goal:** Customer is self-sufficient.

### 9.1 Documentation Handoff

- [ ] DATA_DICTIONARY_REQUIREMENTS.md — how to prepare and update their dictionary
- [ ] REVIEWER_GUIDE.md — how to use the agent (test scenarios)
- [ ] INSTALLATION_GUIDE.md (docs/deployment/) — installation and how to re-run the pipeline after SQL changes

### 9.2 Final Validation

- [ ] Customer can independently ask the agent a question and get a correct answer
- [ ] Customer knows how to re-run the pipeline when they update SQL files
- [ ] Customer knows how to update the data dictionary when tables change
- [ ] `/troubleshoot` command works and returns relevant help for common errors
- [ ] *(If Collibra)* Customer can re-run `900_publish_collibra` after pipeline updates

### 9.3 Sign-Off

- [ ] All required phase checkboxes are checked (Phases 1-6, 8-9)
- [ ] Optional phases (7) completed if applicable
- [ ] Customer confirms agent answers are accurate for their domain
- [ ] No open issues or workarounds documented

---

## Quick Reference: What Goes Wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| "No documented calculation logic" | Agent instructions have hardcoded examples | Remove examples, use teaching rules only |
| "0 source tables" for a metric | Tables not in data dictionary | Add tables to dict_tables.csv, re-run pipeline |
| Parse errors on all files | ScriptDom DLL not loaded | Check 100_install output, verify DLL path |
| Parse errors on non-T-SQL files | Wrong SQL dialect (PL/SQL, PgSQL) | This release supports T-SQL only — remove non-T-SQL files |
| pythonnet initialization fails | `%pip install` was used in a notebook | Remove %pip, use Fabric Environment only |
| Agent gives wrong table names | Table missing from dictionary | Add the table to dict_tables.csv (matching is case-insensitive) |
| Pipeline runs but metric_logic is empty | No parse_results (parse step failed) | Check parse_errors, run 200_parse with verbose |
| Agent returns truncated list | Fabric Data Agent response limit | Ask narrower questions or use `/coverage` for counts |
| Data Agent query fails silently | Workspace/capacity/agent in different regions | Move all resources to same Azure region |
| "Cross-geo" or capacity errors | Region mismatch | Verify in Workspace Settings → Capacity → Region |
| Collibra publish fails | API credentials or permissions | Verify with collibra_discovery notebook |
| Agent description is wrong | Agent instructions need tuning | Update delta_agent_instructions.md, re-run 07 |

---

## Timing Estimates

| Phase | Duration | Who | Required? |
|---|---|---|---|
| 1. Environment Setup (incl. pre-flight) | 15-20 min | Deployment team | Yes |
| 2. Customer Data Loading | 5-10 min | Customer (with guidance) | Yes |
| 3. Setup Notebook | 2-3 min | Automated | Yes |
| 4. Run Pipeline | 1-5 min | Automated | Yes |
| 5. Data Agent Config | 5-10 min | Deployment team | Yes |
| 6. Graph Export | Automatic | Automated (part of pipeline) | Yes (no action) |
| 7. Collibra Integration | 15-30 min | Deployment team + customer | Optional |
| 8. Acceptance Testing | 5-10 min | Automated + review | Yes |
| 9. Handoff | 15-20 min | Deployment team + customer | Yes |
| **Total (without Collibra)** | **~50-75 min** | | |
| **Total (with Collibra)** | **~70-105 min** | | |
