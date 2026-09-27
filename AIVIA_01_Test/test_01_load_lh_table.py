"""Tests for the F11 table loader (AIVIA_01_Code/load_lh_table.py).

Design under test:
    AIVIA_01_Design/01_subject_sql_files.md — F11: notebook loads the data
    sheet json from Files into lakehouse table 01_subject_sql_files_lh_table.

Written test-first: RED until load_lh_table.py exposes to_table_rows().

to_table_rows is the Spark-free half of F11: read the sheet, validate it
at the production door (loud ValueError naming the offending file), and
return rows with camelCase keys for the lakehouse table (ruled 2026-09-27:
the graph model's NL querying needs camelCase; the sheet stays snake_case).

The Spark lines of the notebook are not pytest-able locally; their
acceptance test is Sunny's notebook run and her eye on the table.
"""

import json
import sys
from pathlib import Path

import pytest
from test_01_subject_sql_files_data_contract import SHEET_PATH

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"

sys.path.insert(0, str(CODE_DIR))
from load_lh_table import to_table_rows  # noqa: E402

sys.path.remove(str(CODE_DIR))

CAMEL_COLUMNS = ["fileName", "databaseName", "schemaName", "fileNameEmbedding"]


def write_sheet(tmp_path, rows):
    sheet = tmp_path / "sheet.json"
    sheet.write_text(json.dumps(rows), encoding="utf-8")
    return sheet


def good_row(name="PROC_A"):
    return {
        "file_name": name,
        "database_name": "CookClarity",
        "schema_name": "Reporting",
        "file_name_embedding": [0.1] * 3072,
    }


def test_real_sheet_becomes_8_camelcase_rows_with_embeddings_intact():
    with open(SHEET_PATH, encoding="utf-8") as f:
        sheet = {r["file_name"]: r for r in json.load(f)}

    rows = to_table_rows(SHEET_PATH)

    assert len(rows) == 8
    for row in rows:
        assert list(row.keys()) == CAMEL_COLUMNS
        original = sheet[row["fileName"]]
        assert row["databaseName"] == original["database_name"]
        assert row["schemaName"] == original["schema_name"]
        assert len(row["fileNameEmbedding"]) == 3072
        assert row["fileNameEmbedding"][:5] == original["file_name_embedding"][:5]


def test_blank_schema_name_fails_loudly_naming_the_file(tmp_path):
    bad = good_row("PROC_BLANK")
    bad["schema_name"] = ""
    sheet = write_sheet(tmp_path, [good_row(), bad])
    with pytest.raises(ValueError, match="PROC_BLANK"):
        to_table_rows(sheet)


def test_short_embedding_fails_loudly_naming_the_file(tmp_path):
    bad = good_row("PROC_SHORT")
    bad["file_name_embedding"] = [0.1] * 10
    sheet = write_sheet(tmp_path, [good_row(), bad])
    with pytest.raises(ValueError, match="PROC_SHORT"):
        to_table_rows(sheet)


def test_wrong_columns_fail_loudly_naming_the_file(tmp_path):
    bad = good_row("PROC_ODD")
    bad["extra_column"] = "surprise"
    sheet = write_sheet(tmp_path, [good_row(), bad])
    with pytest.raises(ValueError, match="PROC_ODD"):
        to_table_rows(sheet)
