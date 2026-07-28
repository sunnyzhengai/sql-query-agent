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
| "What metrics are available?" | Lists all 28 parsed metrics from the knowledge graph |
| "How is the Sepsis 3-Hour Bundle calculated?" | Translates complex multi-criteria SQL logic to plain English |
| "What tables feed into the sepsis bundle compliance?" | Traces upstream dependencies through the graph |
| "Show me the technical details for Sepsis Screening" | Shows SQL fragments, source tables, transformation chain |
| "Which reports use the LabResultsFact table?" | Reverse lineage — traces from source table back to metrics |
| "How does the system handle missing lactate values?" | Deep business logic extraction from COALESCE/ISNULL patterns |
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

The demo environment contains **28 synthetic SQL files** representing a realistic **clinical quality metrics** domain — specifically, sepsis bundle compliance reporting from a hospital data warehouse.

### Why Sepsis Metrics

Sepsis quality reporting is one of the most complex analytics challenges in healthcare. It involves tracking multiple criteria over time — vitals (heart rate, blood pressure), lab results (white blood cell count, lactate), nursing interventions, and antibiotic administration — all across different source tables with temporal dependencies. This gives the parser a realistic stress test against production-grade SQL complexity.

All files use **anonymized, synthetic schema names** (e.g., `PatientDim`, `VitalSignsFact`, `LabResultsFact`). No real patient data, provider names, or protected health information is included.

### SQL File Organization

Files are grouped into sequential processing stages:

| Stage | Folder | Count | What it contains |
|---|---|---|---|
| 1. Staging views | `01_staging_views/` | 8 | Base views that read from source tables — patient demographics, encounters, vitals, labs, medications |
| 2. Transformations | `02_transformations/` | 12 | Temp table procedures that stage, filter, join, and transform data — time-window calculations, threshold comparisons, missing-value handling |
| 3. Metrics & reports | `03_sepsis_metrics/` | 8 | Final reporting procedures that calculate bundle compliance rates, dashboard rollups, trend analysis |

### SQL Complexity Patterns Demonstrated

| Pattern | Example | Why it matters |
|---|---|---|
| Multi-CTE chains | 6+ CTEs feeding into a final SELECT | Tests dependency tracking and graph wiring |
| Temp table staging | SELECT INTO #screening → #eligible → #compliant | Tests temp table → CTE conversion and chain resolution |
| Complex CASE logic | CASE WHEN lactate > 4.0 AND antibiotics_within_3hr = 1 THEN 'Compliant' | Tests business rule extraction |
| UNION ALL rollups | Department + facility + system-level aggregations | Tests multi-query merging |
| Temporal JOINs | Events within 3-hour or 6-hour windows | Tests complex WHERE clause extraction |
| PIVOT / aggregation | Compliance rates by department, month, bundle element | Tests advanced T-SQL parsing |
| Missing value handling | COALESCE, ISNULL, LEFT JOIN with NULL checks | Tests real-world data quality patterns |
| Inconsistent formatting | Mixed casing, varied whitespace, inline comments, revision headers | Tests whitespace normalization |

### Data Dictionary

A synthetic data dictionary provides table and column descriptions for ~50 tables covering the clinical domain (patient demographics, encounters, vital signs, lab results, medications, flowsheets). This enables the knowledge graph to show human-readable descriptions alongside the SQL logic.

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

### Scenario 1: Business User Asks About a Complex Metric

**Type in the agent:**
> How is the Sepsis 3-Hour Bundle compliance calculated?

**Expected result:** The agent reads the `metric_logic` table and translates complex multi-criteria SQL logic into plain English:
- What the metric measures (compliance with sepsis treatment protocols)
- What criteria are evaluated (blood cultures, antibiotics, lactate measurement — each within time windows)
- How missing values are handled (e.g., "if lactate is not available, the criterion is marked incomplete")
- How compliance is calculated (percentage of encounters meeting all bundle elements)

**What it proves:** The product automatically extracts deeply nested business logic from SQL and makes it accessible to non-technical users — even for clinically complex, multi-criteria calculations.

### Scenario 2: Developer Traces Upstream Dependencies

**Type in the agent:**
> Which upstream tables feed into the Sepsis 3-Hour Bundle, and what logic handles missing lactate values?

**Expected result:** The agent traces through the knowledge graph and shows:
- Source tables: `LabResultsFact`, `VitalSignsFact`, `MedicationAdminFact`, `PatientDim`, `EncounterFact`
- The transformation chain: staging views → screening procedure → eligibility → bundle compliance
- The specific SQL logic handling missing lactate (COALESCE, LEFT JOIN with NULL checks)

**What it proves:** The product doesn't just list tables — it traces the full lineage chain and explains the transformation logic at each step. A developer can understand the entire data pipeline in seconds.

### Scenario 3: Admin Checks System Health

**Type in the agent:**
> /coverage

**Expected result:** The agent queries `metric_logic` and reports:
- Total metrics: 28
- With calculation logic: 26+ (93%+)
- With source tables mapped: 25+ (89%+)
- With stewards assigned: 0 (not yet configured)

**What it proves:** The product provides operational visibility into data governance coverage — administrators can instantly see how much of their SQL library has been documented.

---

## Before & After

### Before: Raw SQL File (what developers see)

```sql
CREATE PROCEDURE [dbo].[USP_Sepsis_3Hr_Bundle] (
    @StartDate DATE, @EndDate DATE
)
AS
BEGIN
    SELECT enc.PAT_ID, enc.ENCOUNTER_ID, enc.ADMIT_TIME,
        CASE WHEN bc.CULTURE_TIME IS NOT NULL 
             AND DATEDIFF(HOUR, enc.ADMIT_TIME, bc.CULTURE_TIME) <= 3
             THEN 1 ELSE 0 END AS BloodCultureCompliant,
        CASE WHEN abx.ADMIN_TIME IS NOT NULL
             AND DATEDIFF(HOUR, enc.ADMIT_TIME, abx.ADMIN_TIME) <= 3
             THEN 1 ELSE 0 END AS AntibioticCompliant,
        CASE WHEN COALESCE(lab.LACTATE_VALUE, -1) >= 0
             AND DATEDIFF(HOUR, enc.ADMIT_TIME, lab.COLLECT_TIME) <= 3
             THEN 1 ELSE 0 END AS LactateCompliant
    INTO #bundle_elements
    FROM dbo.EncounterFact enc
    LEFT JOIN dbo.LabResultsFact lab ON enc.ENCOUNTER_ID = lab.ENCOUNTER_ID
        AND lab.LAB_TYPE = 'LACTATE'
    LEFT JOIN dbo.MedicationAdminFact abx ON enc.ENCOUNTER_ID = abx.ENCOUNTER_ID
        AND abx.MED_CATEGORY = 'ANTIBIOTIC'
    LEFT JOIN dbo.LabResultsFact bc ON enc.ENCOUNTER_ID = bc.ENCOUNTER_ID
        AND bc.LAB_TYPE = 'BLOOD_CULTURE'
    WHERE enc.ADMIT_TIME BETWEEN @StartDate AND @EndDate
        AND enc.SEPSIS_FLAG = 1;

    SELECT DEPARTMENT_NAME,
        COUNT(*) AS TotalEncounters,
        SUM(CASE WHEN BloodCultureCompliant = 1 
             AND AntibioticCompliant = 1 
             AND LactateCompliant = 1 THEN 1 ELSE 0 END) AS FullyCompliant
    FROM #bundle_elements b
    INNER JOIN dbo.DepartmentDim d ON b.DEPT_ID = d.DEPT_ID
    GROUP BY DEPARTMENT_NAME
END
```

### After: Knowledge Graph (what the agent answers)

**Business user asks:** "How is the Sepsis 3-Hour Bundle calculated?"

**Agent responds:**
> The Sepsis 3-Hour Bundle measures compliance with three time-sensitive treatment requirements for sepsis patients:
>
> 1. **Blood cultures** — collected within 3 hours of admission
> 2. **Antibiotics** — administered within 3 hours of admission
> 3. **Lactate measurement** — drawn within 3 hours of admission (if lactate is not available, the criterion is marked incomplete using a default value check)
>
> A patient is **fully compliant** only if all three criteria are met within the time window.
>
> Results are grouped by department, showing total encounters and the number meeting full compliance. The report covers sepsis-flagged encounters within the selected date range.
>
> Source data comes from: encounter records, lab results, and medication administration records.

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
