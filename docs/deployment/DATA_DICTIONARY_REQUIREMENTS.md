# Data Dictionary Requirements

**Purpose:** The data dictionary is **mandatory** for the SQL Intelligence Agent to work correctly. Without it, the agent cannot describe what tables and columns mean, making its answers incomplete or misleading.

This document tells customers exactly what to provide, in what format, and how to validate it.

---

## What You Need to Provide

Two CSV files:

| File | Purpose | Required? |
|---|---|---|
| `dict_tables.csv` | One row per database table, with a human-readable description | **Yes** |
| `dict_columns.csv` | One row per column, with a human-readable description | **Yes** |

These files describe the tables and columns referenced by your SQL stored procedures and views. The agent uses these descriptions to explain business logic in plain English.

---

## File 1: dict_tables.csv

### Required Columns

| Column Name | Type | Required | Description |
|---|---|---|---|
| `TABLE_NAME` | string | **Yes** | Exact table name as it appears in your SQL (e.g., `PATIENT`, `ORDER_MED`) |
| `DESCRIPTION` | string | **Yes** | Human-readable description of what this table contains |

### Optional Columns (ignored but allowed)

| Column Name | Description |
|---|---|
| `TABLE_ID` | Internal ID from your EMR metadata — ignored by the pipeline |
| `SCHEMA_NAME` | Schema name — reserved for future use |
| `DATABASE_NAME` | Database name — reserved for future use |

### Example

```csv
TABLE_NAME,DESCRIPTION
PATIENT,"Contains demographic information for all patients including name, date of birth, and medical record number."
ORDER_MED,"Contains medication orders including prescriptions, dosages, and administration routes."
FLOWSHEET_MEASUREMENTS,"Contains clinical flowsheet measurements such as vital signs, intake/output, and assessment scores."
DEPARTMENTS,"Contains department master file records with department names and locations."
```

### Rules

- **Header row is required** — first row must be `TABLE_NAME,DESCRIPTION`
- **TABLE_NAME must match your SQL exactly** — if your SQL says `FROM PATIENT`, the dictionary must have `PATIENT` (not `Patients` or `patient_table`)
- **Case sensitivity:** The pipeline performs **case-insensitive matching** when looking up table descriptions, so `PATIENT` and `Patient` will both match. However, the stored TABLE_NAME is used as-is in agent responses. For consistency, use the same casing as your SQL files. If your EMR metadata exports in mixed case (e.g., Epic Clarity exports as `PATIENT` but your SQL uses `Patient`), either case will work — but pick one and be consistent.
- **One row per table** — duplicates will cause the last row to win
- **Descriptions should be meaningful** — "Patient table" is not helpful. "Contains demographic information for all patients including name, date of birth, and medical record number" is.
- **UTF-8 encoding** — save as UTF-8 (not ANSI or Latin-1)
- **Quote descriptions containing commas** — standard CSV quoting rules apply

---

## File 2: dict_columns.csv

### Required Columns

| Column Name | Type | Required | Description |
|---|---|---|---|
| `TABLE_NAME` | string | **Yes** | Table this column belongs to (must match dict_tables.csv) |
| `COLUMN_NAME` | string | **Yes** | Exact column name as it appears in your SQL |
| `DESCRIPTION` | string | **Yes** | Human-readable description of what this column contains |

### Optional Columns (ignored but allowed)

| Column Name | Description |
|---|---|
| `DATA_TYPE` | Column data type (VARCHAR, INTEGER, etc.) — reserved for future use |
| `TABLE_ID` | Internal ID — ignored |
| `COLUMN_ID` | Internal ID — ignored |

### Example

```csv
TABLE_NAME,COLUMN_NAME,DESCRIPTION
PATIENT,PAT_ID,The unique internal identifier for the patient record.
PATIENT,PAT_MRN_ID,The medical record number assigned to the patient.
PATIENT,PAT_NAME,The full name of the patient.
PATIENT,BIRTH_DATE,The date of birth of the patient.
ORDER_MED,ORDER_MED_ID,The unique identifier for this medication order.
ORDER_MED,MEDICATION_ID,The identifier of the medication that was ordered.
ORDER_MED,ORDER_DTTM,The date and time the medication order was placed.
```

### Rules

- **Header row is required** — first row must be `TABLE_NAME,COLUMN_NAME,DESCRIPTION`
- **TABLE_NAME must match dict_tables.csv** — every TABLE_NAME here should exist in dict_tables.csv
- **COLUMN_NAME must match your SQL exactly** — if your SQL says `SELECT PAT_MRN_ID`, the dictionary must have `PAT_MRN_ID`. Same case-insensitive matching rules as table names apply (see dict_tables rules above).
- **You don't need every column** — only include columns that appear in your SQL files. The agent will still work if some columns are missing, but it won't be able to describe those columns.
- **One row per table+column combination** — duplicates will cause the last row to win

---

## Where Do I Get This Data?

### If you use Epic Clarity

Run the provided SQL query against your Clarity metadata database:

```sql
-- Tables
SELECT TABLE_NAME, TABLE_INTRODUCTION AS DESCRIPTION
FROM CLARITY_TBL
WHERE TABLE_NAME IN ('PATIENT', 'ORDER_MED', ...)  -- your tables here
ORDER BY TABLE_NAME;

-- Columns
SELECT t.TABLE_NAME, c.COLUMN_NAME, c.COLUMN_DESCRIPTION AS DESCRIPTION
FROM CLARITY_COL c
INNER JOIN CLARITY_TBL t ON c.TABLE_ID = t.TABLE_ID
WHERE t.TABLE_NAME IN ('PATIENT', 'ORDER_MED', ...)
ORDER BY t.TABLE_NAME, c.COLUMN_NAME;
```

A helper script is included: `scripts/extract_clarity_dictionary.sql` — update the table list to match your SQL files, run against your metadata database, and export as CSV.

### If you use Epic Caboodle

Similar approach using Caboodle metadata tables (CABOODLE_TBL, CABOODLE_COL).

### If you use another system

Create the CSVs manually or export from your data catalog (Collibra, Purview, Alation, etc.). The only requirement is the column format above.

### If you don't have descriptions

At minimum, provide table names with placeholder descriptions. The agent needs to know which tables exist even if descriptions are sparse:

```csv
TABLE_NAME,DESCRIPTION
PATIENT,Patient demographics
ORDER_MED,Medication orders
```

This is better than nothing, but the agent's answers will be proportionally less helpful.

---

## How Many Tables/Columns Do I Need?

**Tables:** Every table referenced in your SQL files should be in dict_tables.csv. Run this to find out which tables your SQL uses:

```sql
-- Look for FROM, JOIN, INTO targets in your SQL
-- Or use the pipeline's parse_results output which lists all referenced tables
```

**Columns:** At minimum, include columns that appear in SELECT, WHERE, JOIN ON, GROUP BY, and CASE statements. These are the columns the agent will be asked about most.

**Coverage guidance:**

| Coverage | Impact |
|---|---|
| All tables + all columns | Best — agent can answer any question |
| All tables + key columns only | Good — agent can answer most questions, some column details missing |
| Most tables + no columns | Partial — agent can trace lineage but can't describe column-level logic |
| Missing tables | Broken — agent will say "0 source tables" for metrics that use those tables |

**Warning — dictionary bloat:** Do NOT upload your entire enterprise data dictionary if only a subset of tables are referenced by your SQL files. A dictionary with 50,000 columns from 2,000 tables when your SQL only uses 50 tables will:
- Slow down the graph build step unnecessarily
- Add noise to the agent's context window, potentially degrading answer quality
- Make validation harder (thousands of "unused table" warnings)

**Best practice:** Filter your dictionary export to only include tables and columns referenced by your target SQL files. The helper script `scripts/extract_clarity_dictionary.sql` generates a filtered query based on your exact table list. After the first pipeline run, check `parse_results` to see which tables were actually referenced, then refine your dictionary accordingly.

---

## Validation

After uploading your dictionary, the pipeline validates it automatically. Check the `pipeline_validation` table for warnings:

| Warning | Meaning | Action |
|---|---|---|
| "0 source tables mapped" | A metric's SQL references tables not in the dictionary | Add those tables to dict_tables.csv |
| "No calculation logic" | The SQL couldn't be parsed (dictionary unrelated) | Check parse_errors table |
| "Missing description" | A table or column has an empty description | Update the CSV |

You can also run the validation notebook (`06_validate`) independently to check coverage before asking the agent questions.

---

## File Placement

Upload your CSV files to this location in your Fabric Lakehouse:

```
Demo_Lakehouse/
└── Files/
    └── sql-query-agent/
        └── dictionary/
            ├── dict_tables.csv
            └── dict_columns.csv
```

The setup notebook will automatically load these into Delta tables.

---

## Checklist

Before running the pipeline, verify:

- [ ] `dict_tables.csv` has a header row: `TABLE_NAME,DESCRIPTION`
- [ ] `dict_columns.csv` has a header row: `TABLE_NAME,COLUMN_NAME,DESCRIPTION`
- [ ] Both files are UTF-8 encoded
- [ ] TABLE_NAME values match your SQL exactly (case-sensitive)
- [ ] Every table referenced in your SQL has an entry in dict_tables.csv
- [ ] Descriptions are meaningful (not just the table/column name repeated)
- [ ] No proprietary/internal references that shouldn't be visible to end users
- [ ] Files are saved to `Files/sql-query-agent/dictionary/` in the Lakehouse
