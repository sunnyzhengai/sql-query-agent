"""The SEPSIS source pack — the truth-check delivery (round 2).

Reads the anonymized ED/IP-sepsis corpus-of-record (data/synthetic:
dict_tables/dict_columns/dict_relationships CSVs + 28 procs) and emits
a contract-shaped delivery into AIVIA_Product/estates/sepsis/. This
estate's JOB is Sunny's gap-check: real-shaped logic whose meaning he
knows cold — the floors, decisions and findings must say TRUE things
(the ED-sepsis acceptance law).

DECLARED CAVEATS (on the record, per pack law):
- dict_relationships derive from RECORDED LINEAGE (EVIDENCE=corpus),
  not vendor FK metadata — join-compliance over this estate is
  near-vacuous by construction; read the descriptions, not the
  compliance column.
- no pk metadata exists in the anonymized dictionary: the pack
  declares pk = each table's first dictionary column (fallback rule,
  overridable) — INTAKE-10 needs a declaration and this one is
  written down, never inferred silently.
- no values dump exists (no ZC-style source): values.csv is empty and
  the coverage gap is the honest state.

Deterministic: byte-identical regeneration. Usage: python3 generate_extract.py
"""
import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data" / "synthetic"
OUT = ROOT / "AIVIA_Product" / "estates" / "sepsis"

PACK_VERSION = "sepsis-pack-1.0"
AS_OF = "2026-09-06T00:00:00Z"
DB, SERVER, SOURCE = "aivia_demo_src", "SEPSISSERVER", "emr"


def main():
    tables = list(csv.DictReader(open(SRC / "dict_tables.csv")))
    columns = list(csv.DictReader(open(SRC / "dict_columns.csv")))
    rels = list(csv.DictReader(open(SRC / "dict_relationships.csv")))
    snap = OUT / "sepsis_snapshot"
    estate = OUT / "estate_snapshot"
    for d in (snap, estate):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)

    (OUT / "registration.json").write_text(json.dumps({
        "_comment": "DBA prerequisite (A1) for the anonymized sepsis "
                    "source; one source owns every schema.",
        "db_name": DB, "server": SERVER, "dba_team": "role:emr-dba",
        "registered_sources": [SOURCE],
        "registered_at": AS_OF,
        "schema_sources": {"dbo": SOURCE, "reporting": SOURCE,
                           "reports": SOURCE},
    }, indent=1) + "\n")

    (snap / "manifest.json").write_text(json.dumps({
        "source": SOURCE, "operator": "sepsis.pack",
        "db_name": DB, "server": SERVER, "as_of": AS_OF,
        "source_pack_version": PACK_VERSION,
        "default_schema": "dbo",
    }, indent=1) + "\n")

    with open(snap / "tables.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "table", "description"])
        for row in tables:
            w.writerow(["dbo", row["TABLE_NAME"], row["DESCRIPTION"]])
    cols_by_table = {}
    with open(snap / "columns.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "table", "column", "description"])
        for row in columns:
            w.writerow(["dbo", row["TABLE_NAME"], row["COLUMN_NAME"],
                        row["DESCRIPTION"]])
            cols_by_table.setdefault(row["TABLE_NAME"], []).append(
                row["COLUMN_NAME"])
    with open(snap / "pk.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "table", "column", "ordinal"])
        for row in tables:
            name = row["TABLE_NAME"]
            declared = cols_by_table.get(name, [f"{name}_ID"])[0]
            w.writerow(["dbo", name, declared, 1])
    with open(snap / "joins.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fk_num", "ordinal", "src_schema", "src_table",
                    "src_column", "dest_schema", "dest_table",
                    "dest_column"])
        for i, row in enumerate(rels, 1):
            w.writerow([i, 1, "dbo", row["SOURCE_TABLE"],
                        row["SOURCE_COLUMN"], "dbo", row["DEST_TABLE"],
                        row["DEST_COLUMN"]])
    with open(snap / "values.csv", "w", newline="") as f:
        csv.writer(f).writerow(["table", "code", "meaning"])

    (estate / "manifest.json").write_text(json.dumps({
        "source_kind": "estate", "org": "sepsis-demo",
        "location": "repo://sepsis-corpus/",
        "declared_dialects": ["tsql"], "as_of": AS_OF,
        "operator": "sepsis.pack", "default_schema": "dbo",
    }, indent=1) + "\n")
    n = 0
    for path in sorted((SRC / "sql").rglob("*.sql")):
        rel = path.relative_to(SRC / "sql")
        dest = estate / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        n += 1
    print(f"delivered: {len(tables)} tables, {len(columns)} columns, "
          f"{len(rels)} declared joins (lineage-derived, see caveat), "
          f"{n} estate files -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
