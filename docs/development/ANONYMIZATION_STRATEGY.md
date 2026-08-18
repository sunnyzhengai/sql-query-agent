# SQL File Anonymization Strategy

> **2026-08-16 amendments:** (1) The column-level crosswalk is now
> REQUIRED and complete — the earlier "columns are Epic-standard, keep
> as-is" note is reversed (verdict: no vendor dialect anywhere
> customer-facing). 1,264 rule-generated renames (CSN family, PAT_/HSP_
> prefixes, _C/_YN suffixes), collision-checked per table. (2) Dictionary
> prose is LLM-paraphrased after anonymization
> (scripts/paraphrase_dictionary.py) — vendor documentation text must
> not survive verbatim. (3) Raw sources live OUTSIDE the repo
> (~/aivia-private, AIVIA_RAW_SQL_DIR). Regeneration order:
> anonymize_sql -> anonymize_dictionary -> paraphrase_dictionary.
> (4) Output filenames are pinned via crosswalk `output_file`.

**Purpose:** Transform proprietary SQL files into clean, generic demo files for Microsoft Marketplace reviewer sandbox. Remove all vendor-specific (Epic Clarity/Caboodle), health system-specific, and author-specific references while preserving SQL structural complexity.

---

## The 5-Step Process

### Step 1: Define the Crosswalk

A JSON mapping file (`data/synthetic/crosswalk.json`) that translates every proprietary name to a generic equivalent. Three categories:

- **Database/schema names:** Clarity → ClinicalDB, Caboodle → AnalyticsDB
- **Table names:** Semantic replacements (CLARITY_ADT → admissions, PATIENT → patients)
- **Column names:** Functional equivalents (PAT_ID → patient_id, PAT_ENC_CSN_ID → encounter_id)
- **Proc names:** Strip org prefixes (USP_<ORGPREFIX>_IP_SEPSIS → USP_IP_Sepsis_Screening)
- **Author/ticket references:** Remove entirely

The crosswalk serves as the **backtrack reference** — if we need to trace an anonymized name back to the original, look it up here.

### Step 2: Build the Crosswalk

Scan all 28 SQL files to extract every unique:
- Database name, schema name
- Table name (FROM, JOIN, INTO targets)
- Column name (SELECT, WHERE, ON, GROUP BY)
- Proc/view name (CREATE PROCEDURE, EXEC)
- Author names, ticket numbers, org-specific comments

Map each to a generic replacement. Prioritize readability — `patients` is better than `table_001`.

### Step 3: Run the Anonymization Script

`scripts/anonymize_sql.py`:
1. Reads SQL files from input folder
2. Loads crosswalk.json
3. Applies all replacements (case-insensitive, whole-word matching)
4. Strips proprietary headers (revision history, author blocks, org-specific comments)
5. Writes anonymized files to `data/synthetic/sql/`
6. Reports any unmatched proprietary terms for manual review

### Step 4: Build the Matching Data Dictionary

Generate from the crosswalk:
- `data/synthetic/dict_tables.csv` — TABLE_NAME, DESCRIPTION (using replacement names)
- `data/synthetic/dict_columns.csv` — TABLE_NAME, COLUMN_NAME, DESCRIPTION

Descriptions are realistic but generic: "Patient demographic information", "Date and time of hospital admission", etc.

### Step 5: Validate

1. Run anonymized files through the parser locally
2. Verify 100% parse rate
3. Run the full pipeline (parse → graph → metric_logic)
4. Test the Data Agent with reviewer questions
5. Manual review for any missed proprietary terms

---

---

## Source corpus (anonymized side only)

28 sepsis procedures, organized as staging views, transformations, and
final reporting procedures under data/synthetic/ (folder layout below).
The mapping from ORIGINAL proprietary names — and the full inventory of
proprietary terms to scrub (vendor databases/schemas/tables/functions,
org names and prefixes, people, tickets, departments) — lives OUTSIDE
the repo, with the raw sources:

- authoritative term list: private/SCRUB_TERMS.md (gitignored)
- raw SQL: ~/aivia-private (AIVIA_RAW_SQL_DIR)

The crosswalk is DATA supplied at run time (src/anonymization.py) —
nothing proprietary is hardcoded in the repo, INCLUDING this document.

### Folder Organization

```
data/synthetic/
├── crosswalk.json              ← Name mapping (original → anonymized; gitignored source side)
├── sql/
│   ├── 01_staging_views/       ← 8 base views
│   ├── 02_transformations/     ← 12 transformation procedures
│   └── 03_sepsis_metrics/      ← 8 final reporting procedures
├── dict_tables.csv             ← Anonymized table descriptions
└── dict_columns.csv            ← Anonymized column descriptions
```

## Verification

Local (non-CI) leak check reads private/SCRUB_TERMS.md and sweeps the
FULL repo — src docstrings, tests, fixtures, notebooks, docs — before
any push or release (see HANDOFF_WORK_TERM_HYGIENE). CI cannot hold the
term list, by design; the check is a local pre-push discipline.
