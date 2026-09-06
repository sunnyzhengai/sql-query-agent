"""The SHAPES source pack — Script 1 + 2 for the synthetic vendor.

Synthetic packs live in AIVIA_Product (CONTRACT_DATALOAD §2); this one
reads the shapes corpus-of-record (data/shapes: the ADR 0055 diabetic
palette + the deterministic seed) and emits a contract-shaped delivery
into AIVIA_Product/estates/shapes/:

  registration.json      the DBA prerequisite (A1)
  shapes_snapshot/       manifest + tables/columns/pk/joins/values CSVs
  estate_snapshot/       manifest + the 38 corpus files (subfolders kept)

For a synthetic vendor the pack IS the dictionary authority, so the
declarations the seed's DDL omits are DECLARED HERE as pack data —
pk per table and the join map — never inferred at intake (the same
line the contract draws for real vendors' metadata tables).

Deterministic: same corpus in, byte-identical delivery out (the
corpus-of-record law). Usage: python3 generate_extract.py
"""
import csv
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PALETTE = json.loads((ROOT / "data/shapes/palette_diabetes.json")
                     .read_text())
SEED = (ROOT / "data/shapes/generated/seed/01_schema_and_data.sql")
SQL_DIR = ROOT / "data/shapes/generated/sql"
OUT = ROOT / "AIVIA_Product/estates/shapes"

PACK_VERSION = "shapes-pack-1.0"
AS_OF = "2026-09-06T00:00:00Z"
DB, SERVER, SOURCE = "aivia_demo_src", "SHAPESERVER", "shapes"

# --- pack-declared keys: the column whose description declares the
# unique identifier; explicit declarations where no column does.
PK_OVERRIDES = {
    "ENCOUNTER_DIAGNOSIS": ["ENCOUNTER_ID", "DX_LINE"],
    "HOSPITAL_DIAGNOSIS": ["HOSP_ENCOUNTER_ID", "DX_LINE"],
    "PATIENT_PCP_ASSIGNMENT": ["PATIENT_ID"],
    "DM_REGISTRY": ["PATIENT_ID"],
    "DIAGNOSIS_CODESET": ["DX_CODE"],
    "LAB_CODESET": ["LAB_CODE"],
    "MED_CODESET": ["MED_CODE"],
    "CPT_CODESET": ["CPT_CODE"],
    "PROC_CODESET": ["PROC_CODE"],
}
# --- pack-declared joins beyond the same-named-pk rule
JOIN_EXTRAS = [
    ("DIAGNOSIS_CODES", "ICD_CODE", "DIAGNOSIS_CODESET", "DX_CODE"),
]


def declared_pk(table: str, columns: dict) -> list:
    if table in PK_OVERRIDES:
        return PK_OVERRIDES[table]
    for col, desc in columns.items():
        if "unique" in desc.lower() and "identifier" in desc.lower():
            return [col]
    return [next(iter(columns))]  # pack-declared fallback, on record


def main():
    tables = PALETTE["tables"]
    snap = OUT / "shapes_snapshot"
    estate = OUT / "estate_snapshot"
    for d in (snap, estate):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)

    (OUT / "registration.json").write_text(json.dumps({
        "_comment": "DBA prerequisite for the synthetic shapes source "
                    "(A1): one source owns every schema.",
        "db_name": DB, "server": SERVER, "dba_team": "role:shapes-dba",
        "registered_sources": [SOURCE],
        "registered_at": AS_OF,
        "schema_sources": {"dbo": SOURCE, "reporting": SOURCE,
                           "reports": SOURCE},
    }, indent=1) + "\n")

    (snap / "manifest.json").write_text(json.dumps({
        "source": SOURCE, "operator": "shapes.pack",
        "db_name": DB, "server": SERVER, "as_of": AS_OF,
        "source_pack_version": PACK_VERSION,
        "default_schema": "dbo",
    }, indent=1) + "\n")

    with open(snap / "tables.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "table", "description"])
        for name, spec in tables.items():
            w.writerow(["dbo", name, spec["description"]])
    with open(snap / "columns.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "table", "column", "description"])
        for name, spec in tables.items():
            for col, desc in spec["columns"].items():
                w.writerow(["dbo", name, col, desc])
    with open(snap / "pk.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "table", "column", "ordinal"])
        for name, spec in tables.items():
            for i, col in enumerate(declared_pk(name, spec["columns"]), 1):
                w.writerow(["dbo", name, col, i])

    # joins: same-named-pk rule + declared extras, grouped w/ ordinals
    pks = {name: declared_pk(name, spec["columns"])
           for name, spec in tables.items()}
    rows, fk = [], 0
    for name, spec in tables.items():
        for col in spec["columns"]:
            for target, target_pk in pks.items():
                if target != name and target_pk == [col]:
                    fk += 1
                    rows.append([fk, 1, "dbo", name, col,
                                 "dbo", target, col])
    for src_t, src_c, dst_t, dst_c in JOIN_EXTRAS:
        fk += 1
        rows.append([fk, 1, "dbo", src_t, src_c, "dbo", dst_t, dst_c])
    with open(snap / "joins.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fk_num", "ordinal", "src_schema", "src_table",
                    "src_column", "dest_schema", "dest_table",
                    "dest_column"])
        w.writerows(rows)

    # Script 2: the values dump — codeset (code, meaning) rows from the
    # deterministic seed INSERTs
    seed_text = SEED.read_text()
    with open(snap / "values.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["table", "code", "meaning"])
        for name in tables:
            if not name.endswith("_CODESET"):
                continue
            block = re.search(
                rf"INSERT INTO dbo\.\[{name}\][^\n]*VALUES\n(.*?);",
                seed_text, re.S)
            for code, meaning in re.findall(
                    r"\('([^']*)',\s*'([^']*)'\)", block.group(1)):
                w.writerow([name, code, meaning])

    (estate / "manifest.json").write_text(json.dumps({
        "source_kind": "estate", "org": "shapes-demo",
        "location": "repo://shapes-corpus/",
        "declared_dialects": ["tsql"], "as_of": AS_OF,
        "operator": "shapes.pack", "default_schema": "dbo",
    }, indent=1) + "\n")
    n = 0
    for path in sorted(SQL_DIR.rglob("*.sql")):
        rel = path.relative_to(SQL_DIR)
        dest = estate / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        n += 1
    print(f"delivered: {len(tables)} tables, {len(rows)} declared joins, "
          f"{n} estate files -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
