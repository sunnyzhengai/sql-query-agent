# Marketplace Reviewer Guide

**Product:** SQL Intelligence Agent for Microsoft Fabric
**Version:** 1.1.0
**Reviewer Sandbox:** [workspace URL to be filled]

---

## Quick Start (5 minutes)

### Step 1: Open the Workspace

1. Log in to [Microsoft Fabric](https://app.fabric.microsoft.com)
2. Navigate to workspace: **[WORKSPACE_NAME]**
3. Open the Lakehouse: **Demo_Lakehouse**

### Step 2: Run the Pipeline (optional — already pre-run)

The pipeline has already been executed and results are loaded. If you want to see it run:

1. Open notebook **02_parse**
2. Click **Run all** — parses 20 SQL files in ~30 seconds
3. Open notebook **03_build_graph** → Run all — builds knowledge graph
4. Open notebook **04_build_metric_logic** → Run all — flattens for agent
5. Open notebook **05_validate** → Run all — shows pipeline health

### Step 3: Test the Data Agent

1. Open the **SQL Query Agent** Data Agent
2. Try these questions:

| Question | What it demonstrates |
|---|---|
| "What metrics are available?" | Lists all parsed metrics from the knowledge graph |
| "How is the Daily Census calculated?" | Translates SQL logic to plain English — business user view |
| "Show me the technical details for Daily Census" | Shows SQL fragments, source tables, transformation chain — developer view |
| "Which reports use the PATIENT table?" | Reverse lineage — traces from source table back to metrics |
| "/errors" | Shows parse errors with user-friendly explanations and suggested fixes |
| "/coverage" | Shows system health: how many metrics have logic, tables, stewards |

---

## What This Product Does

The SQL Intelligence Agent automatically:

1. **Parses** SQL stored procedures and views using Microsoft's native ScriptDom parser (99%+ accuracy on enterprise T-SQL)
2. **Builds** a three-layer knowledge graph in Delta tables: Business Metrics → Calculation Logic → Source Tables
3. **Enables** a Fabric Data Agent to answer natural language questions about any metric's business logic

**The problem it solves:** Organizations have thousands of SQL-based reports with business logic buried in code. Nobody documents them. Analysts wait weeks for answers. This product extracts and organizes that knowledge automatically.

---

## Sample Data Overview

The demo environment contains **20 synthetic SQL files** representing a realistic hospital data warehouse:

### SQL File Categories

| Category | Count | Patterns Demonstrated |
|---|---|---|
| Simple views (SELECT FROM) | 4 | Direct table queries, WHERE filters, JOINs |
| CTE-based reports | 6 | WITH...AS patterns, multi-CTE chains, dependencies |
| Temp table procedures | 5 | SELECT INTO #temp, multi-statement staging, temp chains |
| Complex procedures | 3 | UNION ALL, CASE expressions, nested subqueries |
| Edge cases | 2 | PIVOT, TRY_PARSE, long IN lists, inline comments |

### Intentional Complexity

The sample SQL files include real-world patterns that standard tools cannot parse:

- **Inconsistent formatting:** Mixed casing, varied whitespace, tab vs space indentation
- **Multi-statement procedures:** 5-10 temp tables feeding into a final SELECT
- **Nested CTE dependencies:** CTE A depends on CTE B which depends on CTE C
- **SQL Server-specific syntax:** CROSS APPLY, STRING_AGG, COALESCE chains, window functions
- **Comments and documentation headers:** Block comments, inline comments, revision history

### Data Dictionary

A synthetic data dictionary provides table and column descriptions for ~50 tables, enabling the graph to show human-readable descriptions alongside SQL logic.

---

## Workspace Structure

```
[WORKSPACE_NAME]
├── Demo_Lakehouse
│   ├── Files/
│   │   └── sql-query-agent/          ← Product code + config
│   │       ├── src/                   ← Core library
│   │       ├── notebooks/pipeline/    ← Pipeline notebooks (02-05)
│   │       ├── libs/                  ← ScriptDom DLL
│   │       └── org_config.yaml        ← Configuration
│   └── Tables/
│       ├── sql_sources                ← Input: raw SQL files
│       ├── dict_tables                ← Input: table descriptions
│       ├── dict_columns               ← Input: column descriptions
│       ├── parse_results              ← Intermediate: parsed CTEs + tables
│       ├── parse_errors               ← Output: failed parses with explanations
│       ├── parse_successes            ← Output: successful parses
│       ├── graph_nodes                ← Output: knowledge graph nodes
│       ├── graph_edges                ← Output: knowledge graph edges
│       ├── metric_logic               ← Output: flattened view for agent
│       ├── pipeline_validation        ← Output: per-metric health check
│       └── build_summary              ← Output: pipeline run history
├── Environment: sql-logic-env         ← Pre-installed dependencies
├── Notebooks
│   ├── 02_parse                       ← Parse SQL files
│   ├── 03_build_graph                 ← Build knowledge graph
│   ├── 04_build_metric_logic          ← Flatten for agent
│   └── 05_validate                    ← Validate pipeline health
└── SQL Query Agent                    ← Fabric Data Agent
```

---

## The Golden Path (3 Test Scenarios)

### Scenario 1: Business User Asks About a Metric

**Type in the agent:**
> How is the Daily Census calculated?

**Expected result:** The agent reads the `metric_logic` table and translates the SQL logic into plain English:
- What the metric measures
- What filters are applied (e.g., "active patients only", "excludes cancelled events")
- What time period it covers
- What departments/locations are included

**What it proves:** The product automatically extracts business logic from SQL and makes it accessible to non-technical users.

### Scenario 2: Developer Asks for Technical Details

**Type in the agent:**
> Show me the technical details for the Daily Census

**Expected result:** The agent shows:
- Full SQL fragments from each transformation step
- Source tables with data dictionary descriptions
- The CTE dependency chain
- Table and column references

**What it proves:** The same knowledge graph serves both business users and developers with appropriate detail levels.

### Scenario 3: Admin Checks System Health

**Type in the agent:**
> /coverage

**Expected result:** The agent queries `metric_logic` and reports:
- Total metrics in the system
- How many have calculation logic extracted
- How many have source tables mapped
- How many have stewards assigned

**What it proves:** The product provides operational visibility into data governance coverage.

---

## Before & After

### Before: Raw SQL File (what developers see)

```sql
CREATE PROCEDURE [Reporting].[USP_Daily_Census] (
    @StartDate DATE = NULL,
    @EndDate DATE = NULL
)
AS
BEGIN
    DECLARE @dStart DATE = COALESCE(@StartDate, DATEADD(DAY, -30, GETDATE()))
    
    SELECT 
        adt.EFFECTIVE_TIME AS CensusDate,
        dep.DEPARTMENT_NAME,
        COUNT(DISTINCT adt.PAT_ID) AS PatientCount
    FROM dbo.ADMISSIONS adt
    INNER JOIN dbo.DEPARTMENTS dep ON adt.DEPT_ID = dep.DEPT_ID
    WHERE adt.EVENT_TYPE = 'Census'
        AND adt.EFFECTIVE_TIME BETWEEN @dStart AND @EndDate
        AND adt.STATUS <> 'Cancelled'
    GROUP BY adt.EFFECTIVE_TIME, dep.DEPARTMENT_NAME
END
```

### After: Knowledge Graph (what the agent answers)

**Business user asks:** "How is the Daily Census calculated?"

**Agent responds:**
> The Daily Census counts the number of unique patients present in each department on a given date. It:
> - Filters to census events only (excludes other event types)
> - Excludes cancelled events
> - Covers the selected date range (default: last 30 days)
> - Groups results by date and department
> - Sources data from the Admissions and Departments tables

---

## Known Limitations

- **Parse errors:** Some SQL files may fail to parse if they contain no SELECT statements (utility procedures, DDL-only scripts). These are logged in `parse_errors` with user-friendly explanations.
- **Data dictionary coverage:** Metrics that reference tables not in the data dictionary will show "0 source tables" in the graph but still have their SQL logic extracted.
- **No real-time data:** The agent explains HOW metrics are calculated, not current data values.

---

## System Requirements

| Requirement | Details |
|---|---|
| Microsoft Fabric | F2 capacity or higher |
| Workspace role | Contributor or higher |
| Environment | `sql-logic-env` attached to all notebooks |
| ScriptDom DLL | Pre-uploaded to Files/sql-query-agent/libs/ |

---

## Support

If you encounter issues during testing:

- Check the `/troubleshoot` command in the Data Agent — it queries known installation errors
- Email: support@aiviaapp.com
- Response time: within 24 hours
