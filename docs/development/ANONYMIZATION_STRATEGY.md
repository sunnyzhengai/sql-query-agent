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
- **Proc names:** Strip org prefixes (USP_CCMC_IP_SEPSIS → USP_IP_Sepsis_Screening)
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

## Source Files (28 Sepsis Procedures)

### Original Proc Names → Anonymized Names

| # | Original Name | Anonymized Name | Category |
|---|---|---|---|
| 1 | USP_IPSO_SEVERE_SEPSIS | USP_Sepsis_Severe_Screening | Screening |
| 2 | USP_IPSO_NON_SEVERE_SEPSIS | USP_Sepsis_NonSevere_Screening | Screening |
| 3 | USP_CCMC_ED_SEPSIS | USP_ED_Sepsis_Dashboard | ED |
| 4 | USP_CCMC_IP_SEPSIS_PBI | USP_IP_Sepsis_Overview | Inpatient |
| 5 | USP_CCMC_IP_SEPSIS | USP_IP_Sepsis_Summary | Inpatient |
| 6 | USP_CCMC_IP_SepsisDetails | USP_IP_Sepsis_Detail | Inpatient |
| 7 | USP_CCMC_IP_SepsisShiftCompliance | USP_IP_Sepsis_ShiftCompliance | Compliance |
| 8 | USP_CCMC_IP_SepsisScreeningAudit | USP_IP_Sepsis_ScreeningAudit | Audit |
| 9 | USP_CCHCS_Stroke_Study_Sepsis_Newborn_PBI | USP_Sepsis_Newborn_Study | Study |
| 10 | USP_CCHCS_Stroke_Study_Sepsis_PBI | USP_Sepsis_Clinical_Study | Study |
| 11 | USP_CCMC_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES_PBI | USP_IP_Sepsis_NurseShiftCompliance | Compliance |
| 12 | USP_CCMC_IP_SEPSIS_COMPLIANCE_PBI | USP_IP_Sepsis_ComplianceRate | Compliance |
| 13 | USP_IP_Sepsis_Details_PBI | USP_IP_Sepsis_PatientDetails | Inpatient |
| 14 | USP_CCMC_IP_SepsisPatientDates | USP_IP_Sepsis_PatientTimeline | Inpatient |
| 15 | USP_CCMC_IP_SepsisEncountersWLocations | USP_IP_Sepsis_EncounterLocations | Inpatient |
| 16 | USP_CCMC_IP_SepsisEncounters | USP_IP_Sepsis_EncounterList | Inpatient |
| 17 | USP_IP_Sepsis_ScreeningTool_PBI | USP_IP_Sepsis_ScreeningTool | Screening |
| 18 | USP_IP_SepsisScreeningAudit_PBI | USP_IP_Sepsis_AuditReport | Audit |
| 19 | USP_IP_Sepsis_ComplianceByShift_PBI | USP_IP_Sepsis_ComplianceByShift | Compliance |
| 20 | USP_IP_SepsisDetails_PBI | USP_IP_Sepsis_ClinicalDetail | Inpatient |
| 21 | USP_IP_Sepsis_ComplianceMetrics_PBI | USP_IP_Sepsis_ComplianceMetrics | Compliance |
| 22 | USP_IP_SepsisShiftComplianceByShift_PBI | USP_IP_Sepsis_ShiftMetrics | Compliance |
| 23 | USP_IP_SepsisShiftComplianceMetrics_PBI | USP_IP_Sepsis_ShiftSummary | Compliance |
| 24 | USP_IP_SepsisEncountersWLocations_PBI | USP_IP_Sepsis_LocationReport | Inpatient |
| 25 | USP_IP_SepsisEncountersDetails_PBI | USP_IP_Sepsis_EncounterDetail | Inpatient |
| 26 | USP_IP_Sepsis_Encounters_PBI | USP_IP_Sepsis_EncounterSummary | Inpatient |
| 27 | USP_IP_SepsisPatientDates_PBI | USP_IP_Sepsis_DateTimeline | Inpatient |
| 28 | USP_IP_SepsisDates_PBI | USP_IP_Sepsis_DateReport | Inpatient |

### Folder Organization

```
data/synthetic/
├── crosswalk.json              ← Name mapping (original → anonymized)
├── sql/
│   ├── 01_staging_views/       ← 8 base views
│   ├── 02_transformations/     ← 12 transformation procedures
│   └── 03_sepsis_metrics/      ← 8 final reporting procedures
├── dict_tables.csv             ← Anonymized table descriptions
└── dict_columns.csv            ← Anonymized column descriptions
```

---

## Scrubbing Checklist

For each SQL file, verify removal of:

- [ ] Epic/vendor database names (Clarity, Caboodle, CookClarity, CDWPRD, CookCDW)
- [ ] Organization-specific prefixes (CCMC, CCHCS, CCHP, CC, Cook)
- [ ] Schema names (Reporting, COOK_RPT, cookrpt)
- [ ] Epic-specific table names (CLARITY_*, ZC_*, PAT_ENC_*, ORDER_*)
- [ ] Epic utility functions (EPIC_UTIL.EFN_DIN)
- [ ] Author names in comments
- [ ] Ticket/change request numbers (#1815556, ZD#4195198, RITM#)
- [ ] Department/facility names (Cook Children's, CCMC, PCCMC)
- [ ] Provider/staff names
- [ ] Hardcoded IDs that reference proprietary systems (grouper IDs, flowsheet IDs)

---

## Proprietary Terms to Watch For

| Category | Examples to scrub |
|---|---|
| Vendor databases | Clarity, Caboodle, CookClarity, CookCDW, CDWPRD |
| Vendor schemas | EPIC_UTIL, Reporting, COOK_RPT |
| Vendor tables | CLARITY_ADT, CLARITY_DEP, CLARITY_EMP, CLARITY_SER, PAT_ENC_HSP, ORDER_MED, ZC_*, IP_FLWSHT_*, MAR_ADMIN_INFO |
| Vendor functions | EFN_DIN, EPIC_UTIL.* |
| Org names | Cook Children's, CCMC, PCCMC, CCHCS, CCHP |
| Org prefixes | USP_CCMC_*, USP_CCHCS_*, CC_*, COOK_* |
| People names | Any author/developer names in comment headers |
| Ticket numbers | #nnnnnnn, ZD#, RITM# |
| Dept/location names | Specific department names, building names, service area IDs |
