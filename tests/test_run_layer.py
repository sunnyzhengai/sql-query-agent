"""ADR 0061 slice 1 — the run layer's cage. THE ACCEPTANCE IS P5:
result rows reach the display and structurally never the model.
The fixture is the cohort-105 estate loaded straight from the seed
generator's own rows (same provenance as
data/shapes/generated/seed/01_schema_and_data.sql, zero SQL-parsing
of our own fixture, zero tenant dependency).

Proves: contract:suite-legibility
"""

import sqlite3

import pytest

from devtools.generate_shape_seed import build_rows
from src.run_layer import (
    RunRefusal,
    cap_wrap_sqlite,
    check_single_select,
    run_step,
)


@pytest.fixture(scope="module")
def fixture_db():
    rows, oracle = build_rows()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for table, trows in rows.items():
        if not trows:
            continue
        cols = list(trows[0].keys())
        conn.execute(f"CREATE TABLE {table} ("
                     + ", ".join(f'"{c}"' for c in cols) + ")")
        conn.executemany(
            f"INSERT INTO {table} VALUES ("
            + ", ".join("?" for _ in cols) + ")",
            [tuple(r.get(c) for c in cols) for r in trows])
    conn.commit()
    return conn, oracle


def _exec(conn):
    def execute(sql):
        return [dict(r) for r in conn.execute(sql).fetchall()]
    return execute


class TestStatementGate:
    def test_single_select_passes(self):
        check_single_select("SELECT PATIENT_ID FROM DM_REGISTRY")

    def test_update_refused_with_type_named(self):
        with pytest.raises(RunRefusal) as e:
            check_single_select("UPDATE PATIENTS SET ACTIVE_FLAG='N'")
        assert e.value.reason_class == "not_select"
        assert "Update" in str(e.value)

    def test_exec_refused(self):
        with pytest.raises(RunRefusal) as e:
            check_single_select("EXEC reporting.USP_Diabetes_Registry")
        assert e.value.reason_class == "not_select"

    def test_two_statements_refused(self):
        with pytest.raises(RunRefusal) as e:
            check_single_select("SELECT 1; SELECT 2;")
        assert e.value.reason_class == "multi_statement"

    def test_select_into_refused(self):
        with pytest.raises(RunRefusal) as e:
            check_single_select(
                "SELECT PATIENT_ID INTO #tmp FROM PATIENTS")
        assert e.value.reason_class == "select_into"

    def test_drop_refused(self):
        with pytest.raises(RunRefusal):
            check_single_select("DROP TABLE PATIENTS")


class TestRunAgainstTheCohortEstate:
    def test_registry_select_returns_the_seeded_rows(self, fixture_db):
        conn, oracle = fixture_db
        res = run_step("SELECT PATIENT_ID FROM DM_REGISTRY",
                       _exec(conn), cap=200,
                       cap_wrap=cap_wrap_sqlite, source="fixture")
        # 117 registry rows seeded; cap 200 leaves them uncapped
        assert res.row_count == oracle["registry_rows"]
        assert res.capped is False
        assert res.columns == ["PATIENT_ID"]

    def test_the_cap_is_a_fact_not_a_guess(self, fixture_db):
        conn, _ = fixture_db
        res = run_step("SELECT PATIENT_ID FROM PATIENTS",
                       _exec(conn), cap=100,
                       cap_wrap=cap_wrap_sqlite, source="fixture")
        assert res.row_count == 100 and res.capped is True
        assert "TOP 100 (capped)" in res.sampling_label(100, "fixture")

    def test_sampling_label_carries_the_contract(self, fixture_db):
        conn, _ = fixture_db
        res = run_step("SELECT PATIENT_ID FROM DM_REGISTRY",
                       _exec(conn), cap=200,
                       cap_wrap=cap_wrap_sqlite, source="aivia_shapes")
        label = res.sampling_label(200, "aivia_shapes")
        assert "read-only" in label and "aivia_shapes" in label


class TestP5TheHeartOfTheSlice:
    def test_model_stamps_carry_no_rows_and_no_values(self, fixture_db):
        """P5 ABSOLUTE: the only model-visible shape is
        count/schema/elapsed. No row objects, no cell values."""
        conn, _ = fixture_db
        res = run_step("SELECT PATIENT_ID, PATIENT_NAME FROM PATIENTS",
                       _exec(conn), cap=50,
                       cap_wrap=cap_wrap_sqlite, source="fixture")
        stamps = res.model_stamps()
        assert set(stamps) == {"row_count", "columns", "capped",
                               "elapsed_ms"}
        blob = str(stamps)
        # not one seeded VALUE leaks into the stamp shape (values of
        # length >= 4 — names, dates; short ids colliding with count
        # digits are string accidents, not leaks)
        assert "Test Patient" not in blob
        for row in res.rows[:5]:
            for v in row.values():
                sv = str(v)
                if len(sv) >= 4 and sv not in ("PATIENT_ID",
                                               "PATIENT_NAME"):
                    assert sv not in blob, sv


def test_run_is_not_an_engine_tool():
    """P5 structural half: the model cannot CALL the run — it is not
    in ENGINE_TOOLS, so rows cannot enter model context by
    construction; the display owns them."""
    from src.orchestrator.turn_engine import ENGINE_TOOLS
    names = {t["function"]["name"] for t in ENGINE_TOOLS}
    assert "run" not in names and "run_step" not in names


class TestRW16EveryFailureNamesItsCure:
    """RW-16 (field find 2026-08-29, Sunny's laptop: pyodbc +
    unixodbc + msodbcsql18 all absent, bind failed with no
    remediation): unbound/failed run states DISTINGUISH themselves
    and NAME their cure — the error-contract law."""

    def test_missing_pyodbc_names_the_pip_line(self):
        from src.run_layer import classify_run_error
        cls, msg = classify_run_error(
            ImportError("No module named 'pyodbc'"))
        assert cls == "driver_stack"
        assert "pip install pyodbc" in msg

    def test_missing_odbc_driver_names_the_brew_and_apt_lines(self):
        from src.run_layer import classify_run_error
        cls, msg = classify_run_error(Exception(
            "('01000', \"[01000] [unixODBC][Driver Manager]"
            "Can't open lib 'ODBC Driver 18 for SQL Server' : "
            "file not found (0) (SQLDriverConnect)\")"))
        assert cls == "driver_stack"
        assert "brew trust microsoft/mssql-release" in msg
        assert "msodbcsql18" in msg and "apt-get" in msg

    def test_auth_failure_names_the_az_login_line(self):
        from src.run_layer import classify_run_error
        cls, msg = classify_run_error(Exception(
            "AADSTS70043: the refresh token has expired"))
        assert cls == "auth"
        assert "az login" in msg

    def test_unclassified_failure_stays_typed_execution(self):
        from src.run_layer import classify_run_error
        cls, msg = classify_run_error(Exception("mystery"))
        assert cls == "execution"
        assert "mystery" in msg
