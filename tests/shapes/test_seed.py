"""The demo-source seed (shape-store tenant load, 2026-08-27):
deterministic, palette-total, oracle-by-construction, PHI-free.

Proves: contract:suite-legibility
"""

import json
import re
from pathlib import Path

from devtools.generate_shape_seed import (
    build_rows,
    render_procs,
    render_schema_and_data,
)

REPO = Path(__file__).resolve().parent.parent.parent
SEED_DIR = REPO / "data" / "shapes" / "generated" / "seed"


def test_committed_seed_matches_regeneration():
    assert (SEED_DIR / "01_schema_and_data.sql").read_text() == \
        render_schema_and_data()
    assert (SEED_DIR / "02_procs.sql").read_text() == render_procs()


def test_every_palette_table_is_created_and_populated():
    palette = json.loads(
        (REPO / "data" / "shapes"
         / "palette_diabetes.json").read_text())
    text = (SEED_DIR / "01_schema_and_data.sql").read_text()
    rows, _ = build_rows()
    for t in palette["tables"]:
        assert f"CREATE TABLE dbo.[{t}]" in text, t
        assert rows[t], f"{t} seeded empty — a dead demo table"


def test_oracle_counts_hold_by_construction():
    rows, oracle = build_rows()
    dx = {r["PATIENT_ID"] for r in rows["DIAGNOSIS_CODES"]}
    lab = {r["PATIENT_ID"] for r in rows["LAB_RESULTS"]
           if r["HBA1C_VALUE"] >= 6.5}
    med = {r["PATIENT_ID"] for r in rows["MEDICATION_ORDERS"]
           if r["MED_NAME"] in ("METFORMIN", "INSULIN GLARGINE")}
    composite = {p for p in dx | lab | med
                 if (p in dx) + (p in lab) + (p in med) >= 2}
    assert len(composite) == oracle["composite_cohort"]
    # the stamped header carries the same number
    header = (SEED_DIR / "01_schema_and_data.sql").read_text()[:600]
    assert str(oracle["composite_cohort"]) in header


def test_seed_names_are_synthetic_shapes_only():
    rows, _ = build_rows()
    for r in rows["PATIENTS"]:
        assert re.fullmatch(r"Test Patient \d{4}", r["PATIENT_NAME"])
    for r in rows["PATIENT_PCP_ASSIGNMENT"]:
        assert r["PCP_NAME"].startswith("PCP Provider ")


def test_procs_file_carries_all_corpus_procs_verbatim():
    text = (SEED_DIR / "02_procs.sql").read_text()
    sql_dir = REPO / "data" / "shapes" / "generated" / "sql"
    files = sorted(sql_dir.rglob("*.sql"))
    assert len(files) == 38
    for f in files:
        assert f.read_text().rstrip() in text, f.name
        assert f"DROP PROCEDURE IF EXISTS {f.parent.name}.{f.stem};" \
            in text


def test_isolation_guard_precedes_every_drop():
    # source-leg law (field find 2026-08-27): the seed refuses a
    # database holding foreign tables BEFORE any DROP executes
    text = (SEED_DIR / "01_schema_and_data.sql").read_text()
    assert text.index("ISOLATION GUARD") < text.index("DROP TABLE")
    assert "THROW 50001" in text
    # every palette table is whitelisted inside the guard
    guard = text[:text.index("DROP TABLE")]
    palette = json.loads(
        (REPO / "data" / "shapes"
         / "palette_diabetes.json").read_text())
    for t in palette["tables"]:
        assert f"'{t}'" in guard, t


def test_ddl_and_inserts_are_separate_batches():
    # Msg-207 lesson: a batch compiles against the PRE-batch schema —
    # DDL and INSERTs must be GO-separated for every starting state
    text = (SEED_DIR / "01_schema_and_data.sql").read_text()
    for block in text.split("\nGO\n"):
        assert not ("CREATE TABLE" in block and "INSERT INTO" in block), \
            "DDL and INSERT share a batch"
