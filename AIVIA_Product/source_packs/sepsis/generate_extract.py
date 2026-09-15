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
- pack 1.3: columns.csv carries data_type (contract §2b) — the
  vendor dictionary's declared type verbatim; §3c rows take the demo
  catalog's DDL type where declared, else stay untyped. The §3c org
  columns + authored descriptions (Phase C ruling T-3) are pack data
  in org_dictionary.csv — the runbook's step-4c merged CSV — so
  regeneration reproduces the authored truth instead of wiping it.

Deterministic: byte-identical regeneration. Usage: python3 generate_extract.py
"""
import csv
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data" / "synthetic"
OUT = ROOT / "AIVIA_Product" / "estates" / "sepsis"

PACK_VERSION = "sepsis-pack-1.3"
AS_OF = "2026-09-06T00:00:00Z"
DB, SERVER, SOURCE = "aivia_demo_src", "SEPSISSERVER", "emr"

# FINDING (first shakedown, 2026-09-06): the anonymized dictionary
# carries NO schema column — the original extraction predates the
# contract's §3 ruling (containment is an explicit extract field) —
# and pack-1.0's dbo default produced 39 unresolved refs, ALL of them
# schema mismatches: the corpus qualifies these org-created tables to
# reporting/reports, consistently, never dbo. Declared here per the
# corpus's own testimony; the real fix upstream is re-extracting with
# the schema column (contract §3).
SCHEMA_OVERRIDES = {
    "reports": ["CONFIG_VALUE_SET", "SEVERE_SEPSIS_STAGING",
                "NON_SEVERE_SEPSIS_STAGING", "FY_DATE_DIMENSION"],
    "reporting": ["IP_SEPSIS", "IP_SepsisEncounters",
                  "IP_SepsisEncountersWLocations", "IP_SepsisPatientDates",
                  "IP_SepsisShiftCompliance", "IP_SepsisDetails",
                  "IP_SepsisScreeningAudit"],
}
_SCHEMA_OF = {t.upper(): s for s, ts in SCHEMA_OVERRIDES.items()
              for t in ts}


def schema_of(table: str) -> str:
    return _SCHEMA_OF.get(table.upper(), "dbo")


# --- DEMO-DATA REPAIR (pack 1.2) — OUR problem, never the customer's.
# Our legacy dictionary lost the org tables' column lists in the old
# extraction/anonymization pipeline. A real customer's Script 1 reads
# these from the DATABASE CATALOG (contract §3c) — the catalog always
# exists. The demo database's catalog IS the stub DDL
# (data/demo/seed_demo_tables*.sql), so we read it from there: the
# same §3c part, sourced from the only catalog this synthetic estate
# has. Descriptions are empty by construction -> counted documentation
# gaps, exactly as a real org-catalog part behaves.
STUB_DDL = ("data/demo/seed_demo_tables.sql",
            "data/demo/seed_demo_tables_supplement.sql")
_CREATE = re.compile(
    r"CREATE TABLE \[(reporting|reports)\]\.\[(\w+)\]\s*\((.*?)\);",
    re.S | re.I)
_COL = re.compile(r"^\s*\[(\w+)\]\s+([A-Z][A-Z0-9]*(?:\([^)]*\))?)", re.M)


def org_catalog_columns() -> "dict[str, list[tuple]]":
    """§3c for the demo source: org-schema columns from the stub DDL
    (the demo database's catalog). {TABLE_UPPER: [(column, type)]} —
    the type is the catalog's declared type, verbatim (§2b)."""
    out = {}
    for name in STUB_DDL:
        for schema, table, body in _CREATE.findall(
                (ROOT / name).read_text()):
            out[table.upper()] = _COL.findall(body)
    return out


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
            w.writerow([schema_of(row["TABLE_NAME"]),
                        row["TABLE_NAME"], row["DESCRIPTION"]])
    cols_by_table = {}
    catalog = org_catalog_columns()
    org_dict = list(csv.DictReader(
        open(Path(__file__).resolve().parent / "org_dictionary.csv")))
    with open(snap / "columns.csv", "w", newline="") as f:
        w = csv.writer(f)
        # pack 1.3: data_type emitted per contract §2b — the source's
        # declared type, verbatim; dictionary rows carry the vendor's
        # DATA_TYPE, §3c rows carry the catalog's DDL type
        w.writerow(["schema", "table", "column", "description",
                    "data_type"])
        for row in columns:
            w.writerow([schema_of(row["TABLE_NAME"]),
                        row["TABLE_NAME"], row["COLUMN_NAME"],
                        row["DESCRIPTION"], row["DATA_TYPE"]])
            cols_by_table.setdefault(row["TABLE_NAME"], []).append(
                row["COLUMN_NAME"])
        # §3c org-catalog part, as the runbook's step-4c MERGED CSV:
        # the org columns + their authored descriptions are pack data
        # (org_dictionary.csv — the Phase C T-3 repair, moved out of
        # the snapshot so regeneration reproduces it instead of
        # wiping it); the stub DDL (the demo db's catalog) supplies
        # the declared type where it has one — a column the catalog
        # never declared stays untyped, never guessed
        type_of = {(t, c.upper()): dtype
                   for t, cols in catalog.items()
                   for c, dtype in cols}
        seen = {(r["TABLE_NAME"].upper(), r["COLUMN_NAME"].upper())
                for r in columns}
        for row in org_dict:
            name, col = row["table"], row["column"]
            if (name.upper(), col.upper()) in seen:
                continue
            w.writerow([row["schema"], name, col, row["description"],
                        type_of.get((name.upper(), col.upper()), "")])
            cols_by_table.setdefault(name, []).append(col)
            seen.add((name.upper(), col.upper()))
        uncovered = [(t, c) for t, cols in catalog.items()
                     for c, _ in cols if (t, c.upper()) not in seen]
        assert not uncovered, (
            "demo catalog columns missing from the merged org "
            f"dictionary — extend org_dictionary.csv: {uncovered}")
    with open(snap / "pk.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "table", "column", "ordinal"])
        for row in tables:
            name = row["TABLE_NAME"]
            declared = cols_by_table.get(name, [f"{name}_ID"])[0]
            w.writerow([schema_of(name), name, declared, 1])
    with open(snap / "joins.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fk_num", "ordinal", "src_schema", "src_table",
                    "src_column", "dest_schema", "dest_table",
                    "dest_column"])
        for i, row in enumerate(rels, 1):
            w.writerow([i, 1, schema_of(row["SOURCE_TABLE"]),
                        row["SOURCE_TABLE"], row["SOURCE_COLUMN"],
                        schema_of(row["DEST_TABLE"]),
                        row["DEST_TABLE"], row["DEST_COLUMN"]])
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
