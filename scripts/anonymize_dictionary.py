"""
Anonymize Clarity data dictionary using the master crosswalk.

Reads:
  - data/synthetic/sepsis_sql/sepsis_clarity_tables.csv
  - data/synthetic/sepsis_sql/sepsis_clarity_columns.csv
  - data/synthetic/crosswalk.json

Writes:
  - data/synthetic/dict_tables.csv
  - data/synthetic/dict_columns.csv

Usage:
    python scripts/anonymize_dictionary.py
"""

import csv
import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CROSSWALK_PATH = PROJECT_ROOT / "data" / "synthetic" / "crosswalk.json"
# Raw vendor dictionary lives OUTSIDE the repo (wall rule, relocated
# 2026-08-16). Override with AIVIA_RAW_SQL_DIR.
_RAW_ROOT = Path(os.environ.get(
    "AIVIA_RAW_SQL_DIR", str(Path.home() / "aivia-private" / "sepsis_sql")))
INPUT_TABLES = _RAW_ROOT / "sepsis_clarity_tables.csv"
INPUT_COLUMNS = _RAW_ROOT / "sepsis_clarity_columns.csv"
OUTPUT_TABLES = PROJECT_ROOT / "data" / "synthetic" / "dict_tables.csv"
OUTPUT_COLUMNS = PROJECT_ROOT / "data" / "synthetic" / "dict_columns.csv"


def load_crosswalk() -> dict:
    with open(CROSSWALK_PATH) as f:
        return json.load(f)


def build_table_map(crosswalk: dict) -> dict[str, str]:
    """Build table name mapping (original -> anonymized).

    Keys preserve original casing from the crosswalk for description matching.
    Also includes uppercased keys for CSV TABLE_NAME lookups.
    """
    table_map = {}
    for orig, anon in crosswalk.get("tables", {}).get("_emr_tables", {}).items():
        table_map[orig] = anon  # preserve original case
        table_map[orig.upper()] = anon  # also uppercase for lookups
    for orig, anon in crosswalk.get("tables", {}).get("_org_specific_tables", {}).items():
        table_map[orig] = anon
        table_map[orig.upper()] = anon
    return table_map


def build_description_replacements(crosswalk: dict) -> list[tuple[str, str]]:
    """Build replacements for vendor/org terms in descriptions.

    Only replaces standalone references in prose — NOT table name
    cross-references (those are handled separately by table_map).
    """
    replacements = []

    # Vendor product names in prose
    replacements.append(("Hyperspace", "the clinical application"))
    replacements.append(("Caboodle", "the analytics database"))
    replacements.append(("EpicCare", "the clinical system"))
    replacements.append(("EpicEurope", "regional clinical system"))
    replacements.append(("EPIC_DEPTOSA", "FN_DEPT_SERVICE_AREA"))
    replacements.append(("EPIC_DAT", "INTERNAL_DAT"))
    replacements.append(("EPIC_DTE", "INTERNAL_DTE"))
    replacements.append(("galaxy.epic.com", "vendor.emr.com"))
    replacements.append(("https://vendor.emr.com/redirect.aspx?documentid=1577542", "[see vendor documentation]"))
    replacements.append(("CLARITY_ECL", "SECURITY_CLASS"))
    replacements.append(("EPIC_DX_PARENT", "FN_DX_PARENT"))
    replacements.append(("Clarity Report", "EMR Report"))
    replacements.append(("Clarity report", "EMR report"))
    replacements.append(("CLARITY_EMP_2", "EMPLOYEES_EXT"))
    replacements.append(("EpicWeb", "the web portal"))
    replacements.append(("AffiliateLink", "the affiliate portal"))
    replacements.append(("PlanLink", "the plan portal"))
    replacements.append(("OutReach", "the outreach module"))
    replacements.append(("EMR Compass", "EMR system"))
    # Cross-references to tables not in our set
    replacements.append(("CLARITY_EAP_OT", "PROCEDURES_CATALOG_EXT"))
    replacements.append(("CLARITY_EAP_3", "PROCEDURES_CATALOG_3"))
    replacements.append(("CLARITY_LWS", "WORKSTATIONS"))
    replacements.append(("CLARITY_TDL", "TRANSACTION_DETAIL"))
    replacements.append(("CLARITY_EMP__", "EMPLOYEES__"))
    replacements.append(("CLARITY_COMPONENT__", "LAB_COMPONENTS__"))
    replacements.append(("HOM_CLARITY_FLG_YN", "HOM_RPT_FLG_YN"))
    replacements.append(("EPICCARE_PAT_YN", "CLINICAL_PAT_YN"))
    replacements.append(("EPICCARE_PROV_YN", "CLINICAL_PROV_YN"))
    replacements.append(("EPIC_PAT_ID", "INTERNAL_PAT_ID"))
    replacements.append(("EPIC_PROV_ID", "INTERNAL_PROV_ID"))
    replacements.append(("EPIC_EMP_ID", "INTERNAL_EMP_ID"))
    replacements.append(("EPIC_DAT", "INTERNAL_DAT"))
    replacements.append(("EPIC_DTE", "INTERNAL_DTE"))
    replacements.append(("CLARITY_SER_2", "PROVIDERS_EXT"))
    replacements.append(("CLARITY_SER_DEPT", "PROVIDERS_DEPT"))
    replacements.append(("PAT_ENC_HSP_2", "HOSPITAL_ENCOUNTERS_EXT"))
    replacements.append(("PAT_ENC_HSP", "HOSPITAL_ENCOUNTERS"))
    replacements.append(("contact serial number (CSN)", "encounter identifier"))
    replacements.append(("contact serial number", "encounter identifier"))

    # Org references
    for orig, anon in crosswalk.get("org_references_to_remove", {}).get("string_literals", {}).items():
        replacements.append((orig, anon))

    return replacements


def anonymize_description(
    desc: str,
    replacements: list[tuple[str, str]],
    table_map: dict[str, str],
) -> str:
    """Replace vendor/org terms and table cross-references in a description.

    Uses word-boundary matching for table names to avoid replacing
    inside other words (e.g., 'PATIENT' inside 'patients').
    Handles 'Clarity' specially: only replaces standalone 'Clarity'
    (the product name), not when it's part of a table name like CLARITY_ADT.
    """
    if not desc:
        return desc

    # Step 1: Replace table cross-references (longest first, word-boundary)
    # These appear in descriptions like "link this table to the ALERT table"
    seen = set()
    for orig, anon in sorted(table_map.items(), key=lambda x: -len(x[0])):
        if orig.upper() in seen:
            continue
        seen.add(orig.upper())
        desc = re.sub(r"\b" + re.escape(orig) + r"\b", anon, desc)

    # Step 2: Replace "Clarity" as a product name (not inside table names)
    # Match standalone Clarity, "Clarity database", "your Clarity database"
    desc = re.sub(r"\bClarity\b", "the EMR", desc)
    desc = re.sub(r"\bclarity\b", "the EMR", desc)
    desc = re.sub(r"\bEpic\b", "the EMR system", desc)

    # Step 2b: Strip vendor master-file item references — proprietary
    # record-numbering vocabulary in every observed form: "(EPT/18838)",
    # "(EPT .1)", "(I SER 21000)", "(EDG 2002)", "HNO-34150", "HNO 34021",
    # and bare master-file words ("HNO records"). Enumerated from the raw
    # source (2026-08-16); CSN/ADT handled elsewhere.
    desc = re.sub(r"\(\s*\.\d+\s+ITEM\s*\)", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"\bLDA\b", "device", desc)
    _INI = r"(?:CID|EPT|ORD|HNO|UCI|EMP|EDG|SER|HAR|ERX|EAP|ALT)"
    desc = re.sub(r"\s*\(\s*I?\s*" + _INI + r"\b[^)]*\)", "", desc)
    desc = re.sub(r"\s*\([A-Z]{2,4}\s*[./]\s*\d+\)", "", desc)
    desc = re.sub(r"\b" + _INI + r"[- ]\d{2,6}\b", "the source item", desc)
    for word, plain in [("HNO", "note"), ("EPT", "patient"), ("SER", "provider"),
                        ("EDG", "diagnosis"), ("EAP", "procedure"), ("ORD", "order"),
                        ("EMP", "employee"), ("HAR", "billing account"),
                        ("ERX", "medication"), ("UCI", "contact"), ("CID", "contact")]:
        desc = re.sub(r"\b" + word + r"\b", plain, desc)

    # Step 3: Clean up artifacts
    desc = desc.replace("the the EMR", "the EMR")  # "the Clarity" -> "the the EMR"
    desc = desc.replace("your the EMR", "the EMR")  # "your Clarity" -> "your the EMR"
    desc = desc.replace("the EMR the EMR", "the EMR")  # double replacement
    desc = desc.replace("  ", " ")  # double spaces

    # Step 4: Apply general prose replacements
    for orig, anon in replacements:
        desc = re.sub(re.escape(orig), anon, desc, flags=re.IGNORECASE)

    # Step 5: Generic dialect scrub for cross-references to vendor tables
    # OUTSIDE our set (PAT_ENC_7, HSP_ACCOUNT_2, ...) — no enumerated map
    # can cover them, and any survivor is a leak. Specific before generic.
    # Anchor-free, most-specific-first: compounds like
    # INPATIENT_PAT_ENC_CSN_ID and EIX_FILT_PAT_ENC_RFL must resolve too.
    desc = desc.replace("PAT_ENC_CSN_ID", "ENCOUNTER_ID")   # catches plural too
    desc = desc.replace("PAT_ENC_CSN", "ENCOUNTER_NUM")
    desc = desc.replace("PAT_CSN_ID", "VISIT_ID")   # before generic CSN->ENC,
    desc = desc.replace("PAT_CSN", "VISIT_ID")      # which would mint PAT_ENC_*
    desc = desc.replace("PAT_ENC", "PATIENT_ENC")
    desc = desc.replace("HSP_ACCOUNT", "HOSPITAL_ACCOUNT")
    desc = desc.replace("HSP_ACCT", "HOSPITAL_ACCT")
    desc = desc.replace("PAT_MRN", "PATIENT_MRN")
    desc = desc.replace("PAT_ID", "PATIENT_ID")   # mid-token too (NBA_PAT_ID)
    desc = desc.replace("CSN", "ENC")                        # any last survivor
    # Vendor database name in prose (75 occurrences, found 2026-08-16)
    desc = re.sub(r"\bChronicles\b", "the source system", desc)
    desc = desc.replace("in the the source system", "in the source system")

    return desc


ORG_TABLE_DESCRIPTIONS = {
    "IP_SEPSIS": "Staging table containing inpatient sepsis screening results, encounter details, compliance metrics, and clinical observations for sepsis-flagged patients.",
    "IP_SepsisDetails": "Detailed clinical data for sepsis encounters including vitals, lab results, medication administration times, and organ dysfunction scores.",
    "IP_SepsisEncounters": "Base encounter records for inpatient sepsis patients including demographics, admission/discharge times, and diagnosis codes.",
    "IP_SepsisEncountersWLocations": "Sepsis encounter records enriched with ADT location history showing department transfers and timestamps during the encounter.",
    "IP_SepsisPatientDates": "Date-indexed view of sepsis patient encounters with department rollup information for trend and compliance reporting.",
    "IP_SepsisScreeningAudit": "Audit trail of sepsis screening activities including organ dysfunction scores, huddle documentation, alert responses, and nursing assessments.",
    "IP_SepsisShiftCompliance": "Shift-level sepsis screening compliance data with AM/PM shift breakdowns, compliance rates, and responsible nursing staff.",
    "SEVERE_SEPSIS_STAGING": "ETL staging table for severe sepsis case identification. Stores patients meeting severe sepsis criteria with bundle element compliance tracking.",
    "NON_SEVERE_SEPSIS_STAGING": "ETL staging table for non-severe sepsis case identification. Stores patients with suspected sepsis who do not meet severe sepsis criteria.",
    "FY_DATE_DIMENSION": "Fiscal year date dimension table with fiscal year number, month, and calendar date mappings for reporting period alignment.",
    "CONFIG_VALUE_SET": "Configuration lookup table containing value sets used for department rollups, location groupings, and other reporting categorizations.",
}

ORG_COLUMN_ENTRIES = [
    ("IP_SEPSIS", "EncounterID", "Unique hospital encounter identifier", "NUMERIC"),
    ("IP_SEPSIS", "PatientID", "Internal patient identifier", "VARCHAR"),
    ("IP_SEPSIS", "PatientMRN", "Patient medical record number", "VARCHAR"),
    ("IP_SEPSIS", "PatientName", "Patient full name", "VARCHAR"),
    ("IP_SEPSIS", "HospAdmsnTime", "Hospital admission date and time", "DATETIME"),
    ("IP_SEPSIS", "HospDischTime", "Hospital discharge date and time", "DATETIME"),
    ("IP_SEPSIS", "ADTDepartmentName", "ADT department name at time of screening", "VARCHAR"),
    ("IP_SEPSIS", "DepartmentRollup", "Rolled-up department grouping for reporting", "VARCHAR"),
    ("IP_SEPSIS", "ODScore", "Organ dysfunction score value", "NUMERIC"),
    ("IP_SEPSIS", "ShiftComplianceFlag", "Whether sepsis screening was compliant for this shift (Y/N)", "VARCHAR"),
    ("IP_SEPSIS", "RefreshDate", "Date when this record was last refreshed", "DATETIME"),
    ("SEVERE_SEPSIS_STAGING", "SepsisDate", "Date the patient met severe sepsis criteria", "DATE"),
    ("SEVERE_SEPSIS_STAGING", "EncounterID", "Unique hospital encounter identifier", "NUMERIC"),
    ("SEVERE_SEPSIS_STAGING", "PatientID", "Internal patient identifier", "VARCHAR"),
    ("NON_SEVERE_SEPSIS_STAGING", "SepsisDate", "Date the patient met non-severe sepsis criteria", "DATE"),
    ("NON_SEVERE_SEPSIS_STAGING", "EncounterID", "Unique hospital encounter identifier", "NUMERIC"),
    ("NON_SEVERE_SEPSIS_STAGING", "PatientID", "Internal patient identifier", "VARCHAR"),
    ("FY_DATE_DIMENSION", "CALENDAR_DT", "Calendar date", "DATE"),
    ("FY_DATE_DIMENSION", "FISCAL_YEAR", "Fiscal year number", "INTEGER"),
    ("FY_DATE_DIMENSION", "FY_MONTH_NUMBER", "Month number within the fiscal year", "INTEGER"),
    ("FY_DATE_DIMENSION", "MONTH_NAME", "Full month name", "VARCHAR"),
    ("FY_DATE_DIMENSION", "DAY_OF_MONTH", "Day of the month", "INTEGER"),
    ("FY_DATE_DIMENSION", "MONTH_END_DT", "Last day of the month", "DATE"),
    ("CONFIG_VALUE_SET", "VALUE_SET_ID", "Unique identifier for the value set", "NUMERIC"),
    ("CONFIG_VALUE_SET", "CODE", "Value code within the set", "VARCHAR"),
    ("CONFIG_VALUE_SET", "CODE_DESC", "Description of the value code", "VARCHAR"),
]


def build_column_map(crosswalk: dict) -> dict[str, str]:
    """Column renames (2026-08-16 verdict): keyed uppercase for lookups."""
    return {
        orig.upper(): anon
        for orig, anon in crosswalk.get("columns", {}).items()
        if not orig.startswith("_") and orig != anon
    }


_COLUMN_RE_CACHE: dict = {}


def apply_column_map(text: str, column_map: dict[str, str]) -> str:
    """Rename column references inside prose (word-boundary, ci).

    One combined alternation, compiled once — 1,200+ individual re.sub
    calls per row thrash the regex cache and take minutes over 4k rows.
    Longest-first alternation preserves most-specific-wins.
    """
    if not text or not column_map:
        return text
    key = id(column_map)
    if key not in _COLUMN_RE_CACHE:
        alternation = "|".join(
            re.escape(k) for k in sorted(column_map, key=len, reverse=True)
        )
        _COLUMN_RE_CACHE[key] = re.compile(
            r"\b(" + alternation + r")\b", re.IGNORECASE)
    pattern = _COLUMN_RE_CACHE[key]
    return pattern.sub(lambda m: column_map[m.group(1).upper()], text)


def main():
    crosswalk = load_crosswalk()
    table_map = build_table_map(crosswalk)
    column_map = build_column_map(crosswalk)
    desc_replacements = build_description_replacements(crosswalk)

    # --- Process tables ---
    tables_out = []
    with open(INPUT_TABLES, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig_name = row["TABLE_NAME"].strip()
            anon_name = table_map.get(orig_name.upper(), orig_name)
            desc = anonymize_description(row["DESCRIPTION"].strip(), desc_replacements, table_map)
            desc = apply_column_map(desc, column_map)
            tables_out.append({"TABLE_NAME": anon_name, "DESCRIPTION": desc})

    # Add org-specific table descriptions
    for anon_name, desc in ORG_TABLE_DESCRIPTIONS.items():
        tables_out.append({"TABLE_NAME": anon_name, "DESCRIPTION": desc})

    tables_out.sort(key=lambda x: x["TABLE_NAME"])

    with open(OUTPUT_TABLES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["TABLE_NAME", "DESCRIPTION"])
        writer.writeheader()
        writer.writerows(tables_out)

    print(f"Tables: {len(tables_out)} written to {OUTPUT_TABLES}")

    # --- Process columns ---
    columns_out = []
    with open(INPUT_COLUMNS, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig_table = row["TABLE_NAME"].strip()
            anon_table = table_map.get(orig_table.upper(), orig_table)
            col_name = row["COLUMN_NAME"].strip()
            # Anonymize column names that contain vendor references
            for orig_col, anon_col in desc_replacements:
                if orig_col in col_name:
                    col_name = col_name.replace(orig_col, anon_col)
            # Column-dialect rename (2026-08-16 verdict). The fallback
            # chain catches names MINTED by the replacements above
            # (EPIC_PAT_ID -> INTERNAL_PAT_ID misses the map).
            col_name = column_map.get(col_name.upper(), col_name)
            for a, b in (("PAT_ID", "PATIENT_ID"), ("PAT_MRN", "PATIENT_MRN"),
                         ("CSN", "ENC")):
                col_name = col_name.replace(a, b)
            desc = anonymize_description(row["DESCRIPTION"].strip(), desc_replacements, table_map)
            desc = apply_column_map(desc, column_map)
            data_type = row.get("DATA_TYPE", "").strip()
            columns_out.append({
                "TABLE_NAME": anon_table,
                "COLUMN_NAME": col_name,
                "DESCRIPTION": desc,
                "DATA_TYPE": data_type,
            })

    # Add org-specific column entries
    for table, col, desc, dtype in ORG_COLUMN_ENTRIES:
        columns_out.append({
            "TABLE_NAME": table,
            "COLUMN_NAME": col,
            "DESCRIPTION": desc,
            "DATA_TYPE": dtype,
        })

    columns_out.sort(key=lambda x: (x["TABLE_NAME"], x["COLUMN_NAME"]))

    with open(OUTPUT_COLUMNS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["TABLE_NAME", "COLUMN_NAME", "DESCRIPTION", "DATA_TYPE"])
        writer.writeheader()
        writer.writerows(columns_out)

    print(f"Columns: {len(columns_out)} written to {OUTPUT_COLUMNS}")


if __name__ == "__main__":
    main()
