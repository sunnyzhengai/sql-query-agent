# Marketplace Reviewer Guide

**Product:** SQL Intelligence Agent for Microsoft Fabric
**Version:** 1.1.0

---

## Quick Start (5 minutes)

### Step 1: Open the Workspace

1. Log in to [Microsoft Fabric](https://app.fabric.microsoft.com)
2. Navigate to the workspace shared with you
3. Open the **SQL Intelligence Agent** Data Agent

### Step 2: Test the Data Agent

The pipeline has already been executed — 28 SQL stored procedures have been parsed, a knowledge graph has been built, and business descriptions have been generated. You can start asking questions immediately.

Try these questions:

| # | Question | What it demonstrates |
|---|---|---|
| 1 | "What metrics are available?" | Lists all 28 parsed metrics from the knowledge graph |
| 2 | "What is USP_Severe_Sepsis?" | Returns a pre-generated business description with purpose and business logic |
| 3 | "How is USP_IP_SEPSIS calculated?" | Translates complex multi-criteria SQL logic to plain English |
| 4 | "What tables feed into USP_ED_Sepsis?" | Traces upstream dependencies — shows source tables with descriptions |
| 5 | "Which reports use the FLOWSHEET_MEASUREMENTS table?" | Reverse lineage — finds all metrics that read from a specific source table |
| 6 | "Show me the technical details for USP_IP_SepsisShiftCompliance" | Shows SQL fragments, source tables, and transformation chain (developer view) |
| 7 | "How does the system handle missing lactate values?" | Deep business logic extraction — finds COALESCE/ISNULL patterns across metrics |
| 8 | "/coverage" | System health: 28/28 metrics parsed, 28/28 with descriptions, source tables mapped |
| 9 | "/errors" | Parse errors (should show 0 — all 28 files parsed successfully) |
| 10 | "What metrics are in the reports schema?" | Finds metrics grouped by database schema |

### Step 3: Explore the Pipeline (optional)

If you want to see the pipeline run from scratch:

1. Open notebook **01_install** → Run all — validates environment, loads SQL files and dictionary
2. Open notebook **02_parse** → Run all — parses 28 SQL files with Microsoft ScriptDom (~1 minute)
3. Open notebook **03_build_graph** → Run all — builds the three-layer knowledge graph
4. Open notebook **04_build_metric_logic** → Run all — flattens graph for the Data Agent
5. Open notebook **05_export_graph_tables** → Run all — exports typed tables for future graph model
6. Open notebook **06_validate** → Run all — validates pipeline health (should show DEPLOYMENT READY)
7. Open notebook **07_generate_descriptions** → Run all — generates AI descriptions for each metric

> **Note:** On F2 capacity, only one notebook can run at a time. Stop each session before starting the next.

---

## What This Product Does

The SQL Intelligence Agent automatically:

1. **Parses** SQL stored procedures and views using Microsoft's native ScriptDom parser (100% accuracy on T-SQL)
2. **Builds** a three-layer knowledge graph in Delta tables: Business Metrics → Calculation Logic → Source Tables
3. **Generates** AI-powered business descriptions for each metric
4. **Enables** a Fabric Data Agent to answer natural language questions about any metric's business logic, data lineage, and governance status

**The problem it solves:** Organizations have thousands of SQL-based reports with business logic buried in code. Nobody documents them. Analysts wait weeks for answers. This product extracts, organizes, and describes that knowledge automatically.

---

## Sample Data Overview

The demo environment contains **28 synthetic SQL files** representing a realistic **clinical quality metrics** domain — specifically, sepsis bundle compliance reporting from a hospital data warehouse.

### Why Sepsis Metrics

Sepsis quality reporting is one of the most complex analytics challenges in healthcare. It involves tracking multiple criteria over time — vitals, lab results, nursing interventions, and medication administration — all across different source tables with temporal dependencies. This gives the parser a realistic stress test against production-grade SQL complexity.

All files use **anonymized, synthetic schema names** (e.g., `PATIENTS`, `MEDICATION_ORDERS`, `FLOWSHEET_MEASUREMENTS`). No real patient data, provider names, or protected health information is included.

### SQL File Organization

The 28 files come from two database schemas, demonstrating how the product handles same-name procedures in different schemas:

| Schema | Count | What it contains |
|---|---|---|
| `reporting` | 21 | Reporting-layer procedures — staging views, transformations, compliance dashboards |
| `reports` | 7 | ETL-layer procedures — core sepsis identification, bundle compliance calculation |

### SQL Complexity Patterns Demonstrated

| Pattern | Example | Why it matters |
|---|---|---|
| Multi-temp-table chains | 27+ temp tables feeding into final INSERT | Tests dependency tracking and graph wiring |
| Complex CASE logic | CASE WHEN lactate > threshold AND antibiotics_within_3hr = 1 | Tests business rule extraction |
| UNION ALL rollups | Department + facility + system-level aggregations | Tests multi-query merging |
| Temporal JOINs | Events within 3-hour or 6-hour windows | Tests complex WHERE clause extraction |
| Missing value handling | COALESCE, ISNULL, LEFT JOIN with NULL checks | Tests real-world data quality patterns |
| Grouper/config lookups | Dynamic category lookups from config tables | Tests indirect reference resolution |
| Cross-schema references | Procs in `reporting` reading from `reports` staging tables | Tests schema-aware identity |
| Simple reporting views | Single SELECT with column aliases and CASE | Tests that even simple procs get descriptions |

### Data Dictionary

A synthetic data dictionary provides table and column descriptions for 83 tables and 4,123 columns covering the clinical domain (patients, encounters, vital signs, lab results, medications, flowsheets, alerts, clinical notes). This enables the knowledge graph to show human-readable descriptions alongside the SQL logic.

---

## The Golden Path (5 Test Scenarios)

### Scenario 1: Business User Asks About a Metric

**Type in the agent:**
> What is USP_Severe_Sepsis?

**Expected result:** The agent returns a pre-generated business description that includes:
- A purpose statement (what the report does, who uses it)
- Business logic bullets (inclusion criteria, time windows, clinical thresholds, compliance calculations)

**What it proves:** The product automatically generates human-readable business descriptions from raw SQL — no manual documentation required.

### Scenario 2: Developer Traces Data Lineage

**Type in the agent:**
> What tables feed into USP_IP_SEPSIS and what does each table contain?

**Expected result:** The agent shows source tables with their data dictionary descriptions:
- Physical table names from the SQL (e.g., HOSPITAL_TRANSACTIONS, FLOWSHEET_MEASUREMENTS, MED_ADMIN_RECORDS)
- Dictionary descriptions explaining what each table contains

**What it proves:** The product doesn't just list tables — it enriches them with dictionary descriptions, giving developers instant context about unfamiliar data sources.

### Scenario 3: Reverse Lineage Query

**Type in the agent:**
> Which metrics use the FLOWSHEET_MEASUREMENTS table?

**Expected result:** The agent traces from a source table back to all metrics that reference it, showing which reports depend on flowsheet data.

**What it proves:** Impact analysis — when a source table changes, you instantly know which reports are affected.

### Scenario 4: Deep Business Logic Extraction

**Type in the agent:**
> Show me the technical details for USP_IP_SepsisShiftCompliance

**Expected result:** The agent shows the full transformation chain: SQL fragments from each CTE/temp table step, showing how raw data flows from source tables through screening criteria into shift-level compliance calculations.

**What it proves:** Developers can understand the entire data pipeline in seconds — every transformation step, every filter, every join condition.

### Scenario 5: System Health Check

**Type in the agent:**
> /coverage

**Expected result:**
- Total metrics: 28
- With calculation logic: 28 (100%)
- With descriptions: 28 (100%)
- With source tables: 28 (100%)
- With stewards: 0 (not yet configured)

**What it proves:** The product provides operational visibility into documentation coverage — administrators can see exactly how much of their SQL library has been automatically documented.

---

## Before & After

### Before: Raw SQL File (what developers see)

```sql
CREATE PROCEDURE [reports].[USP_Severe_Sepsis] (
    @StartDate VARCHAR(20) = NULL,
    @EndDate VARCHAR(20) = NULL,
    @Hospitals INT = 1
)
AS
BEGIN
    -- 5,400 lines of complex T-SQL with 27 temp tables,
    -- 60+ JOINs, clinical threshold comparisons,
    -- temporal window calculations, and nested CASE logic
    ...
END
```

### After: Knowledge Graph (what the agent answers)

**Business user asks:** "What is USP_Severe_Sepsis?"

**Agent responds with a pre-generated description:**
> This report identifies patients meeting severe sepsis criteria for clinical quality reporting and outcome tracking. It supports quality improvement teams in monitoring sepsis bundle compliance across facilities.
>
> Business logic:
> - Identifies inpatient encounters with sepsis indicators within the reporting period
> - Applies clinical thresholds for organ dysfunction scoring
> - Tracks 3-hour and 6-hour bundle element compliance (blood cultures, antibiotics, lactate, fluid resuscitation)
> - Calculates compliance rates by department and shift
> - Handles missing values with fallback logic for incomplete lab results
> - Groups results by facility for multi-site comparison

---

## Workspace Structure

```
Workspace
├── sql_query_lh (Lakehouse)
│   ├── Files/
│   │   └── sql-query-agent/
│   │       ├── libs/               ← ScriptDom DLL
│   │       ├── sql_input/          ← 28 SQL files
│   │       ├── dictionary/         ← dict_tables.csv + dict_columns.csv
│   │       └── org_config.yaml     ← Configuration
│   └── Tables/
│       ├── input_sql_sources       ← Loaded SQL files
│       ├── input_dict_tables       ← Table descriptions (83 tables)
│       ├── input_dict_columns      ← Column descriptions (4,123 columns)
│       ├── ops_parse_results       ← Parsed SQL structure (JSON)
│       ├── ops_parse_errors        ← Failed parses (0 for demo)
│       ├── ops_parse_successes     ← Successful parses (28)
│       ├── graph_nodes             ← Knowledge graph nodes (~4,700)
│       ├── graph_edges             ← Knowledge graph edges (~1,400)
│       ├── graph_canonical         ← LPG: business metric nodes
│       ├── graph_transformation    ← LPG: SQL transformation nodes
│       ├── graph_technical         ← LPG: source table/column nodes
│       ├── graph_dimension         ← LPG: dimension nodes
│       ├── output_metric_logic     ← Flattened view for Data Agent
│       ├── ops_pipeline_validation ← Pipeline health check
│       └── ops_build_summary       ← Pipeline run history
├── sql-logic-env (Environment)     ← Pre-installed dependencies + .whl
├── SQL Intelligence Agent          ← Fabric Data Agent
└── Notebooks (01-07)               ← Pipeline notebooks
```

---

## Known Limitations

- **T-SQL only:** This version supports Microsoft SQL Server T-SQL. Other SQL dialects (PL/SQL, PostgreSQL) are planned for future releases.
- **Parse complexity:** Some highly dynamic SQL (EXEC with string concatenation, dynamic pivots) may not fully parse. These are logged in `ops_parse_errors` with explanations.
- **No real-time data:** The agent explains HOW metrics are calculated, not current data values.
- **F2 capacity:** On F2 capacity, only one Spark session runs at a time. Stop each notebook session before starting the next.

---

## System Requirements

| Requirement | Details |
|---|---|
| Microsoft Fabric | F2 capacity or higher |
| Workspace role | Contributor or higher |
| Environment | `sql-logic-env` with .whl and pythonnet installed |
| ScriptDom DLL | Pre-uploaded to Files/sql-query-agent/libs/ |

---

## Support

If you encounter issues during testing:

- Check the `/errors` command in the Data Agent for parse issues
- Check the `/coverage` command for system health
- Check `ops_installation_errors` table for known setup issues and fixes
- Email: support@aiviaapp.com
- Response time: within 24 hours
