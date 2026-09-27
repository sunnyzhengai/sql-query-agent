"""Mirror tests for the F14 GQL gates (AIVIA_01_Test/test_01_graph_gql_gates.md).

Design under test:
    AIVIA_01_Design/01_subject_sql_files.md — F14: test suites using GQL to
    validate the loading of the table is correct.

The gates themselves run by Sunny's hand in the graph model's query
experience (no local API — the FABRIC_GRAPH_LOAD.md precedent). What CAN
be mechanical is the old project's mirror pattern: every expected number
and name printed in the gates doc is RE-DERIVED here from the real data
sheet, so the doc and the truth can never drift apart silently.

Written test-first: RED until the gates doc exists and carries exactly
the values the sheet dictates.
"""

import json
from pathlib import Path

from test_01_subject_sql_files_data_contract import SHEET_PATH

GATES_DOC = Path(__file__).resolve().parent / "test_01_graph_gql_gates.md"

NODE_LABEL = "SQL_FILE"  # Sunny's mapping choice, ruled 2026-09-27
EMBEDDING_LENGTH = 3072


def sheet_rows():
    with open(SHEET_PATH, encoding="utf-8") as f:
        return json.load(f)


def doc_text():
    assert GATES_DOC.exists(), f"gates doc missing: {GATES_DOC}"
    return GATES_DOC.read_text(encoding="utf-8")


def test_doc_uses_the_ruled_node_label():
    assert NODE_LABEL in doc_text()


def test_node_count_gate_matches_the_sheet():
    assert f"fileCount = {len(sheet_rows())}" in doc_text()


def test_every_file_name_is_an_expected_answer():
    text = doc_text()
    for row in sheet_rows():
        assert row["file_name"] in text, f"{row['file_name']} missing from gates doc"


def test_distinct_names_gate_matches_the_sheet():
    names = {row["file_name"] for row in sheet_rows()}
    assert f"distinctNames = {len(names)}" in doc_text()


def test_database_counts_match_the_sheet():
    counts = {}
    for row in sheet_rows():
        counts[row["database_name"]] = counts.get(row["database_name"], 0) + 1
    text = doc_text()
    for database_name, n in sorted(counts.items()):
        assert f"{database_name} | {n}" in text, f"expected '{database_name} | {n}'"


def test_schema_counts_match_the_sheet():
    counts = {}
    for row in sheet_rows():
        counts[row["schema_name"]] = counts.get(row["schema_name"], 0) + 1
    text = doc_text()
    for schema_name, n in sorted(counts.items()):
        assert f"{schema_name} | {n}" in text, f"expected '{schema_name} | {n}'"


def test_blank_gate_and_graph_table_gate_are_pinned():
    text = doc_text()
    assert "badRows = 0" in text
    assert f"graphTableRows = {len(sheet_rows())}" in text
    assert "f01_subject_sql_files_graph" in text


def test_embedding_gates_are_retired_with_the_ruling_not_dropped():
    """Ruled 2026-09-27: embeddings cannot be graph properties. The gates
    doc must RECORD that ruling (and where embedding completeness is now
    enforced), never silently lose the gates."""
    text = doc_text()
    assert "ruled 2026-09-27" in text.lower()
    assert str(EMBEDDING_LENGTH) in text
    assert "test_01_load_lh_table.py" in text
