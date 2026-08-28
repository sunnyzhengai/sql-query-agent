"""Shape-store demo SOURCE seed (tenant-load order, 2026-08-27).

Generates the T-SQL that seeds the demo source SQL database
(`aivia_demo_src`) the Diabetes Registry Dashboard executes against:

  data/shapes/generated/seed/01_schema_and_data.sql
      every palette table (DROP IF EXISTS + CREATE + INSERTs) with
      DETERMINISTIC synthetic rows (fixed seed; byte-identical regen,
      the corpus-of-record law) — fully synthetic, no PHI shapes
      ("Test Patient NNNN" names only)
  data/shapes/generated/seed/02_procs.sql
      CREATE SCHEMA guards + DROP IF EXISTS + the 38 corpus proc
      files VERBATIM (the corpus stays the one truth for logic)

Oracle by construction: the generator computes the U7 composite
cohort (>=2 of dx/lab/med paths) from its own rows and stamps the
expected counts in the file header — the dashboard's card is
checkable against the seed, not vibes.

Usage: python3.11 devtools/generate_shape_seed.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SEED = 20260827
N_PATIENTS = 400
OUT_DIR = PROJECT_ROOT / "data" / "shapes" / "generated" / "seed"
SQL_DIR = PROJECT_ROOT / "data" / "shapes" / "generated" / "sql"

_TYPES = (
    ("HBA1C_VALUE", "DECIMAL(4,1)"),
    ("ACTIVE_FLAG", "CHAR(1)"),
    ("_DATE", "DATE"),
    ("_ID", "INT"),
)


def col_type(name: str) -> str:
    for suffix, t in _TYPES:
        if name.endswith(suffix) or name == suffix.lstrip("_"):
            return t
    return "NVARCHAR(200)"


def sql_lit(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def month_date(rng, start_year=2024, months=24) -> str:
    m = rng.randrange(months)
    y, mo = start_year + m // 12, m % 12 + 1
    return f"{y:04d}-{mo:02d}-{rng.randint(1, 28):02d}"


def build_rows() -> "tuple[dict, dict]":
    """(rows per table, expected-count oracle). Deterministic."""
    rng = random.Random(SEED)
    pids = list(range(1, N_PATIENTS + 1))
    dx_p = set(rng.sample(pids, 150))
    lab_p = set(rng.sample(pids, 140))
    med_p = set(rng.sample(pids, 130))
    composite = {p for p in pids
                 if (p in dx_p) + (p in lab_p) + (p in med_p) >= 2}
    rows: "dict[str, list[dict]]" = {t: [] for t in _tables()}

    for p in pids:
        rows["PATIENTS"].append({
            "PATIENT_ID": p, "PATIENT_NAME": f"Test Patient {p:04d}",
            "BIRTH_DATE": f"{1950 + p % 55:04d}-{p % 12 + 1:02d}-"
                          f"{p % 28 + 1:02d}",
            "ACTIVE_FLAG": "Y" if rng.random() < 0.9 else "N",
            "PRIMARY_LANGUAGE": rng.choice(
                ["English", "Spanish", "Mandarin"])})
    dx_codes = ["E11.9", "E11.65", "E11.40", "E11.22", "E11.8"]
    k = 0
    for p in sorted(dx_p):
        k += 1
        rows["DIAGNOSIS_CODES"].append({
            "DX_ID": k, "PATIENT_ID": p,
            "ICD_CODE": rng.choice(dx_codes),
            "DX_DATE": month_date(rng)})
    k = 0
    for p in sorted(lab_p):
        k += 1
        rows["LAB_RESULTS"].append({
            "LAB_ID": k, "PATIENT_ID": p, "LAB_CODE": "HBA1C",
            "HBA1C_VALUE": round(rng.uniform(6.5, 11.0), 1),
            "RESULT_DATE": month_date(rng)})
    for p in sorted(rng.sample(sorted(set(pids) - lab_p), 80)):
        k += 1
        rows["LAB_RESULTS"].append({
            "LAB_ID": k, "PATIENT_ID": p, "LAB_CODE": "HBA1C",
            "HBA1C_VALUE": round(rng.uniform(4.8, 6.4), 1),
            "RESULT_DATE": month_date(rng)})
    k = 0
    for p in sorted(med_p):
        k += 1
        rows["MEDICATION_ORDERS"].append({
            "ORDER_ID": k, "PATIENT_ID": p,
            "MED_NAME": rng.choice(["METFORMIN", "INSULIN GLARGINE"]),
            "ORDER_DATE": month_date(rng)})
    k = 0
    for p in sorted(composite | set(rng.sample(pids, 20))):
        k += 1
        rows["DM_REGISTRY"].append({
            "REGISTRY_ID": k, "PATIENT_ID": p,
            "ENROLLED_DATE": month_date(rng)})
    # light plausibility fill for the remaining lego tables
    for i in range(1, 301):
        p = rng.choice(pids)
        rows["ENCOUNTERS"].append({
            "ENCOUNTER_ID": i, "PATIENT_ID": p,
            "ENCOUNTER_DATE": month_date(rng),
            "DEPARTMENT": rng.choice(
                ["ENDOCRINOLOGY", "PRIMARY CARE", "ED"])})
    for i in range(1, 121):
        p = rng.choice(pids)
        rows["HOSPITAL_ENCOUNTERS"].append({
            "HOSP_ENC_ID": i, "PATIENT_ID": p,
            "ENCOUNTER_TYPE": rng.choice(["INPATIENT", "ED"]),
            "ADMIT_DATE": month_date(rng)})
        rows["HOSPITAL_DIAGNOSIS"].append({
            "HOSP_DX_ID": i, "HOSP_ENC_ID": i, "PATIENT_ID": p,
            "DX_CODE": rng.choice(dx_codes + ["I10", "J45.909"])})
        rows["LAB_ORDERS"].append({
            "LAB_ORDER_ID": i, "HOSP_ENC_ID": i, "PATIENT_ID": p,
            "ORDERED_DATE": month_date(rng)})
    for i in range(1, 201):
        p = rng.choice(pids)
        rows["ENCOUNTER_DIAGNOSIS"].append({
            "ENC_DX_ID": i, "ENCOUNTER_ID": rng.randint(1, 300),
            "PATIENT_ID": p,
            "DX_CODE": rng.choice(dx_codes + ["I10"])})
        rows["CPT_CODES"].append({
            "CPT_ROW_ID": i, "CPT_CODE": rng.choice(
                ["99213", "99214", "83036"]), "PATIENT_ID": p})
        rows["PROFESSIONAL_BILLING"].append({
            "BILLING_ID": i, "PATIENT_ID": p, "CPT_ROW_ID": i,
            "SERVICE_DATE": month_date(rng)})
        rows["APPOINTMENTS"].append({
            "APPT_ID": i, "PATIENT_ID": p,
            "APPT_STATUS": rng.choice(
                ["COMPLETED", "COMPLETED", "NO SHOW"]),
            "APPT_DATE": month_date(rng)})
    for i in range(1, 61):
        p = rng.choice(pids)
        rows["OR_CASES"].append({
            "CASE_ID": i, "PATIENT_ID": p,
            "CASE_DATE": month_date(rng)})
        rows["PROCEDURE_ORDERS"].append({
            "PROC_ORDER_ID": i, "CASE_ID": i, "PATIENT_ID": p,
            "PROC_CODE": rng.choice(["0DB60ZZ", "3E0G76Z"])})
    for i, p in enumerate(sorted(rng.sample(pids, 250)), start=1):
        rows["PATIENT_PCP_ASSIGNMENT"].append({
            "ASSIGN_ID": i, "PATIENT_ID": p,
            "PCP_NAME": f"PCP Provider {p % 12 + 1:02d}"})
    for i, p in enumerate(sorted(dx_p)[:90], start=1):
        rows["PROBLEM_LIST"].append({
            "PROBLEM_ID": i, "PATIENT_ID": p,
            "PROBLEM_CODE": rng.choice(dx_codes),
            "NOTED_DATE": month_date(rng)})
    for code in ["E11.9", "E11.65", "E11.40", "E11.22", "E11.8",
                 "E11.80"]:
        rows["DIAGNOSIS_CODESET"].append({
            "DX_CODE": code,
            "DX_DESCRIPTION": f"Type 2 diabetes mellitus ({code})"})
    rows["LAB_CODESET"].append({
        "LAB_CODE": "HBA1C",
        "LAB_DESCRIPTION": "Hemoglobin A1c percentage"})
    for m in ["METFORMIN", "INSULIN GLARGINE"]:
        rows["MED_CODESET"].append({
            "MED_CODE": m, "MED_DESCRIPTION": f"{m.title()} order"})
    for cpt, desc in [("99213", "Office visit, established, low"),
                      ("99214", "Office visit, established, moderate"),
                      ("83036", "Hemoglobin A1c test")]:
        rows["CPT_CODESET"].append({
            "CPT_CODE": cpt, "CPT_DESCRIPTION": desc})
    for pc, desc in [("0DB60ZZ", "Excision of stomach, open"),
                     ("3E0G76Z", "Introduction of nutritional "
                                 "substance")]:
        rows["PROC_CODESET"].append({
            "PROC_CODE": pc, "PROC_DESCRIPTION": desc})
    oracle = {"composite_cohort": len(composite),
              "registry_rows": len(rows["DM_REGISTRY"]),
              "dx_path": len(dx_p), "lab_path": len(lab_p),
              "med_path": len(med_p)}
    return rows, oracle


def _tables() -> "list[str]":
    palette = json.loads(
        (PROJECT_ROOT / "data" / "shapes"
         / "palette_diabetes.json").read_text())
    return list(palette["tables"].keys())


def _columns() -> "dict[str, list[str]]":
    palette = json.loads(
        (PROJECT_ROOT / "data" / "shapes"
         / "palette_diabetes.json").read_text())
    return {t: list(spec["columns"]) for t, spec in
            palette["tables"].items()}


def render_schema_and_data() -> str:
    rows, oracle = build_rows()
    cols = _columns()
    out = [
        "-- GENERATED by devtools/generate_shape_seed.py — do not "
        "edit.",
        f"-- Deterministic (seed {SEED}); regeneration is "
        "byte-identical.",
        "-- Fully synthetic demo data; no PHI shapes.",
        "-- ORACLE (computed from these rows at generation):",
        f"--   U7 composite cohort (>=2 of dx/lab/med): "
        f"{oracle['composite_cohort']}",
        f"--   DM_REGISTRY rows: {oracle['registry_rows']}; paths "
        f"dx={oracle['dx_path']} lab={oracle['lab_path']} "
        f"med={oracle['med_path']}",
        "",
    ]
    for t in _tables():
        cdefs = ", ".join(f"[{c}] {col_type(c)}" for c in cols[t])
        out.append(f"DROP TABLE IF EXISTS dbo.[{t}];")
        out.append(f"CREATE TABLE dbo.[{t}] ({cdefs});")
        for chunk_start in range(0, len(rows[t]), 500):
            chunk = rows[t][chunk_start:chunk_start + 500]
            if not chunk:
                continue
            values = ",\n".join(
                "(" + ", ".join(sql_lit(r.get(c)) for c in cols[t])
                + ")" for r in chunk)
            out.append(
                f"INSERT INTO dbo.[{t}] ("
                + ", ".join(f"[{c}]" for c in cols[t])
                + ") VALUES\n" + values + ";")
        out.append("")
    return "\n".join(out) + "\n"


def render_procs() -> str:
    out = [
        "-- GENERATED by devtools/generate_shape_seed.py — do not "
        "edit.",
        "-- The 38 corpus procs VERBATIM (data/shapes/generated/sql "
        "is the one truth); DROP guards make the seed idempotent.",
        "",
        "IF SCHEMA_ID('reporting') IS NULL EXEC('CREATE SCHEMA "
        "reporting');",
        "GO",
        "IF SCHEMA_ID('reports') IS NULL EXEC('CREATE SCHEMA "
        "reports');",
        "GO",
        "",
    ]
    for f in sorted(SQL_DIR.rglob("*.sql")):
        schema = f.parent.name
        proc = f.stem
        out.append(f"DROP PROCEDURE IF EXISTS {schema}.{proc};")
        out.append("GO")
        out.append(f.read_text().rstrip())
        out.append("GO")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "01_schema_and_data.sql").write_text(
        render_schema_and_data())
    (OUT_DIR / "02_procs.sql").write_text(render_procs())
    _, oracle = build_rows()
    print(f"wrote {OUT_DIR} — composite cohort "
          f"{oracle['composite_cohort']}, registry rows "
          f"{oracle['registry_rows']}")


if __name__ == "__main__":
    main()
