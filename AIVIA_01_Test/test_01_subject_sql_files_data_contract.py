"""Mechanical contract tests for 01-subject-sql-files.

Contract under test:
    AIVIA_01_Design/01-subject-sql-files-data-contract.yaml

Written test-first: every test here is RED until two things exist —
    1. the data sheet   AIVIA_01_Data/01_subject_sql_files/01_subject_sql_files_data_sheet.json
    2. the builder      AIVIA_01_Code/build_data_sheet.py  exposing  build_data_sheet(sql_dir, sheet_path, embedder)

Builder behavior these tests pin down (contract "Who fills out the data sheet", lines 40-45):
    - build_data_sheet writes one row per sql file found in sql_dir
    - a file with no existing row gets blank database_name/schema_name
    - after writing, any blank database_name/schema_name raises ValueError
      naming every unfilled file (fail loudly)
    - rebuilding NEVER overwrites hand-filled database_name/schema_name
    - embedder is a function names -> list of embeddings

CLAUDE.md Standing law (ruled 2026-09-26): all LLM calls use paid API
calls, no fake calls. The embedder used here is the REAL OpenAI API
(text-embedding-3-large, key from .env). Running this file therefore
needs network + OPENAI_API_KEY; a red caused by a missing key or a
network outage is infrastructure, not a code failure.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = REPO_ROOT / "AIVIA_01_Data" / "01_subject_sql_files"
SHEET_PATH = SQL_DIR / "01_subject_sql_files_data_sheet.json"
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"

# Contract lines 27-31: the four columns, embedding last.
EXPECTED_COLUMNS = ["file_name", "database_name", "schema_name", "file_name_embedding"]

# Contract lines 60-62: OpenAI text-embedding-3-large, 3072 numbers per embedding.
EMBEDDING_LENGTH = 3072


def sql_file_names(folder: Path) -> set:
    """The subject sql files: every visible file in the folder except the
    data sheet itself (the sheet lives alongside the files per the design doc)."""
    return {
        p.name
        for p in folder.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.suffix != ".json"
    }


# ---------------------------------------------------------------------------
# Group A - the real data sheet obeys the contract
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sheet_rows():
    assert SHEET_PATH.exists(), (
        f"Data sheet not found at {SHEET_PATH} - contract line 25 names it as the output"
    )
    with open(SHEET_PATH, encoding="utf-8") as f:
        rows = json.load(f)  # raises if not valid JSON
    assert isinstance(rows, list), "Data sheet must be a JSON list of records"
    return rows


def test_one_row_per_sql_file(sheet_rows):
    """Contract lines 7, 19, 41: the sheet mirrors the folder exactly -
    no missing files, no extra rows."""
    files = sql_file_names(SQL_DIR)
    row_names = [row["file_name"] for row in sheet_rows]
    assert len(row_names) == len(set(row_names)), "Duplicate file_name rows in the sheet"
    assert set(row_names) == files, (
        f"Sheet and folder disagree. Missing from sheet: {sorted(files - set(row_names))}. "
        f"In sheet but not folder: {sorted(set(row_names) - files)}"
    )


def test_rows_have_exactly_the_contract_columns(sheet_rows):
    """Contract lines 27-31: four columns, in the contract's order,
    embedding last."""
    for row in sheet_rows:
        assert list(row.keys()) == EXPECTED_COLUMNS, (
            f"Row for {row.get('file_name', '<no file_name>')} has columns "
            f"{list(row.keys())}, contract requires {EXPECTED_COLUMNS}"
        )


def test_database_and_schema_are_filled(sheet_rows):
    """Contract lines 42-43, 45: database_name and schema_name are
    hand-filled by Sunny and must never be blank in a shipped sheet."""
    blanks = [
        row["file_name"]
        for row in sheet_rows
        if not str(row.get("database_name", "")).strip()
        or not str(row.get("schema_name", "")).strip()
    ]
    assert not blanks, f"Rows with blank database_name/schema_name: {blanks}"


def test_embeddings_are_3072_numbers(sheet_rows):
    """Contract lines 60-62: every embedding is exactly 3072 numbers
    (text-embedding-3-large)."""
    for row in sheet_rows:
        emb = row["file_name_embedding"]
        assert isinstance(emb, list), f"{row['file_name']}: embedding is not a list"
        assert len(emb) == EMBEDDING_LENGTH, (
            f"{row['file_name']}: embedding has {len(emb)} numbers, "
            f"contract requires {EMBEDDING_LENGTH}"
        )
        assert all(isinstance(x, (int, float)) for x in emb), (
            f"{row['file_name']}: embedding contains non-numeric values"
        )


# ---------------------------------------------------------------------------
# Group B - the builder script behaves per the contract
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def build_data_sheet():
    sys.path.insert(0, str(CODE_DIR))
    try:
        from build_data_sheet import build_data_sheet as fn
    finally:
        sys.path.remove(str(CODE_DIR))
    return fn


def load_openai_key():
    env_file = REPO_ROOT / ".env"
    assert env_file.exists(), "No .env at repo root - contract line 63 says the key lives there"
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise AssertionError("OPENAI_API_KEY not found in .env")


def real_embedder(names):
    """The REAL OpenAI call - CLAUDE.md law: no fake calls.
    Same model the contract pins (lines 60-62)."""
    from openai import OpenAI

    client = OpenAI(api_key=load_openai_key())
    response = client.embeddings.create(
        model="text-embedding-3-large", input=list(names)
    )
    return [item.embedding for item in response.data]


def make_sql_folder(tmp_path, names):
    folder = tmp_path / "sql"
    folder.mkdir()
    for name in names:
        (folder / name).write_text("SELECT 1;", encoding="utf-8")
    return folder


def read_sheet(sheet_path):
    with open(sheet_path, encoding="utf-8") as f:
        return {row["file_name"]: row for row in json.load(f)}


def fill_all(sheet_path, database_name="CookClarity", schema_name="Reporting"):
    """Simulate Sunny hand-filling the blanks in the sheet."""
    with open(sheet_path, encoding="utf-8") as f:
        rows = json.load(f)
    for row in rows:
        row["database_name"] = database_name
        row["schema_name"] = schema_name
    with open(sheet_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def test_first_build_writes_blanks_then_fails_loudly(build_data_sheet, tmp_path):
    """Contract line 45: a file with no row gets blanks, and blanks fail
    loudly. On a first-ever build every row is new, so the builder must
    still WRITE the sheet (so Sunny has something to fill) and then raise."""
    folder = make_sql_folder(tmp_path, ["PROC_A", "PROC_B"])
    sheet = folder / "sheet.json"

    with pytest.raises(ValueError, match="PROC_A"):
        build_data_sheet(folder, sheet, real_embedder)

    rows = read_sheet(sheet)
    assert set(rows) == {"PROC_A", "PROC_B"}
    for name, row in rows.items():
        assert row["database_name"] == "" and row["schema_name"] == "", (
            f"{name}: new row must get blanks for Sunny to fill"
        )
        assert len(row["file_name_embedding"]) == EMBEDDING_LENGTH


def test_build_succeeds_once_sunny_fills_the_blanks(build_data_sheet, tmp_path):
    """Contract lines 42-43: after Sunny fills database_name/schema_name,
    the build passes without raising."""
    folder = make_sql_folder(tmp_path, ["PROC_A"])
    sheet = folder / "sheet.json"
    with pytest.raises(ValueError):
        build_data_sheet(folder, sheet, real_embedder)
    fill_all(sheet)

    build_data_sheet(folder, sheet, real_embedder)  # must not raise

    row = read_sheet(sheet)["PROC_A"]
    assert row["database_name"] == "CookClarity"
    assert row["schema_name"] == "Reporting"


def test_rebuild_preserves_hand_filled_values(build_data_sheet, tmp_path):
    """Contract line 45: rebuilding keeps existing database_name/schema_name
    values - the script must never overwrite Sunny's hand-filled truth."""
    folder = make_sql_folder(tmp_path, ["PROC_A", "PROC_B"])
    sheet = folder / "sheet.json"
    with pytest.raises(ValueError):
        build_data_sheet(folder, sheet, real_embedder)
    fill_all(sheet, database_name="CookClarity", schema_name="CookRPT")

    build_data_sheet(folder, sheet, real_embedder)
    build_data_sheet(folder, sheet, real_embedder)  # rebuild again, still kept

    for name, row in read_sheet(sheet).items():
        assert row["database_name"] == "CookClarity", f"{name}: database_name was overwritten"
        assert row["schema_name"] == "CookRPT", f"{name}: schema_name was overwritten"


def test_new_file_gets_blank_row_and_fails_loudly(build_data_sheet, tmp_path):
    """Contract line 45: a file added later appears as a new row with blanks,
    the build fails loudly naming it, and existing rows keep their values."""
    folder = make_sql_folder(tmp_path, ["PROC_A"])
    sheet = folder / "sheet.json"
    with pytest.raises(ValueError):
        build_data_sheet(folder, sheet, real_embedder)
    fill_all(sheet)

    (folder / "PROC_NEW").write_text("SELECT 2;", encoding="utf-8")
    with pytest.raises(ValueError, match="PROC_NEW"):
        build_data_sheet(folder, sheet, real_embedder)

    rows = read_sheet(sheet)
    assert rows["PROC_NEW"]["database_name"] == ""
    assert rows["PROC_NEW"]["schema_name"] == ""
    assert rows["PROC_A"]["database_name"] == "CookClarity", "existing row lost its value"


def test_removed_file_row_disappears(build_data_sheet, tmp_path):
    """Contract lines 7, 41 (one row per file, both directions): a deleted
    sql file's row must not linger in the rebuilt sheet."""
    folder = make_sql_folder(tmp_path, ["PROC_A", "PROC_B"])
    sheet = folder / "sheet.json"
    with pytest.raises(ValueError):
        build_data_sheet(folder, sheet, real_embedder)
    fill_all(sheet)

    (folder / "PROC_B").unlink()
    build_data_sheet(folder, sheet, real_embedder)

    assert set(read_sheet(sheet)) == {"PROC_A"}
