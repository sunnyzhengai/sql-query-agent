"""Phase 04 contract tests (AIVIA_01_Design/04_fabric_move_data_contract.md).

Current section: the Delta loader (AIVIA_01_Code/load_dictionary_tables.py,
design M02; decisions 1, 2, 6).

Written test-first: RED until load_dictionary_tables.py exposes
    build_table_rows(dir02, dir03, expected_counts=GOLDEN_COUNTS),
    GOLDEN_COUNTS.

Zero API cost — the loader embeds nothing; it validates, renames to
camelCase at the door, derives the graph tables, and counts to the
digit. The Spark lines live in the notebook; their acceptance is
Sunny's run and her eye.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
DIR02 = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
DIR03 = REPO_ROOT / "AIVIA_01_Data" / "03_chat_bot"

sys.path.insert(0, str(CODE_DIR))
import chat_bot  # noqa: E402
import load_dictionary_tables as ldt  # noqa: E402
from test_03_chat_bot_data_contract import _mini_chat_assets  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return ldt.build_table_rows(DIR02, DIR03)


def test_golden_counts_to_the_digit(built):
    tables, census = built
    assert ldt.GOLDEN_COUNTS == {
        "dict_tables": 38, "dict_columns": 1618, "dict_joins": 5262,
        "dict_values": 14476, "dict_value_embeddings": 14476,
        "dict_no_match": 1, "chat_abstract_names": 1656,
        "chat_technical_terms": 9, "graph_join_edges": 391,
        "graph_table_nodes": 38, "graph_column_nodes": 1618}
    assert set(tables) == set(ldt.GOLDEN_COUNTS)
    for name, expected in ldt.GOLDEN_COUNTS.items():
        assert len(tables[name]) == expected, name
        assert census[name] == expected, name
    assert census["joinsByFk"] == 210
    assert census["joinsByRule"] == 181


def test_every_key_is_camelcase(built):
    tables, _ = built
    for name, rows in tables.items():
        for key in rows[0]:
            assert "_" not in key and key[0].islower(), (
                f"{name}: non-camelCase key {key!r}")


def test_embeddings_survive_intact(built):
    tables, _ = built
    sheet = json.loads(
        (DIR02 / "02_emr_data_dictionary_extraction_table.json")
        .read_text(encoding="utf-8"))
    local = next(r for r in sheet if r["table_name"] == "PATIENT")
    loaded = next(r for r in tables["dict_tables"]
                  if r["tableName"] == "PATIENT")
    assert len(loaded["tableNameEmbedding"]) == 3072
    assert loaded["tableNameEmbedding"][:3] == (
        local["table_name_embedding"][:3])
    assert loaded["tableDescription"] == local["table_description"]


def test_graph_node_tables_are_embedding_free(built):
    # The F12/F13 ruling: the graph model reads embedding-free tables.
    tables, _ = built
    for name in ("graph_table_nodes", "graph_column_nodes"):
        for key in tables[name][0]:
            assert "mbedding" not in key, f"{name} carries {key}"
    assert set(tables["graph_table_nodes"][0]) == {
        "tableId", "tableName", "databaseName", "schemaName",
        "deprecatedYn"}
    assert set(tables["graph_column_nodes"][0]) == {
        "columnId", "tableId", "tableName", "columnName", "dataType",
        "deprecatedYn"}


def test_graph_join_edges_shape(built):
    tables, _ = built
    edges = tables["graph_join_edges"]
    kinds = {}
    node_ids = {r["tableId"] for r in tables["graph_table_nodes"]}
    for e in edges:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        assert e["sourceTableId"] in node_ids
        assert e["destinTableId"] in node_ids
        pairs = json.loads(e["columnPairs"])
        assert pairs and pairs[0]["source_column_name"]
    assert kinds == {"joins_by_fk": 210, "joins_by_rule": 181}


def test_terms_table_matches_the_md(built):
    tables, _ = built
    md_rows = chat_bot.parse_terms(
        (DIR03 / "03_chat_technical_terms.md").read_text(encoding="utf-8"))
    assert [r["keyword"] for r in tables["chat_technical_terms"]] == [
        r["keyword"] for r in md_rows]
    assert tables["chat_technical_terms"][0]["mapsTo"]


def test_validation_fails_loudly_at_the_door(tmp_path):
    _mini_chat_assets(tmp_path)
    # the synthetic estate passes with counts disabled...
    tables, _ = ldt.build_table_rows(tmp_path, tmp_path,
                                     expected_counts=None)
    assert tables["dict_tables"]
    # ...and a blanked description fails loudly, naming the offender
    sheet_path = tmp_path / "02_emr_data_dictionary_extraction_table.json"
    rows = json.loads(sheet_path.read_text(encoding="utf-8"))
    rows[0]["table_description"] = "   "
    sheet_path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match=rows[0]["table_name"]):
        ldt.build_table_rows(tmp_path, tmp_path, expected_counts=None)


def test_count_drift_fails_loudly(tmp_path):
    # the golden numbers are a law: a corpus that disagrees cannot load
    _mini_chat_assets(tmp_path)
    with pytest.raises(ValueError, match="dict_tables"):
        ldt.build_table_rows(tmp_path, tmp_path)


# ---------------------------------------------------------------------------
# Section 2 — the files sync (AIVIA_01_Code/sync_files.py, the M02
# transport). RED until the real code lands. The live upload is Sunny's
# hand; these pin the file list, the chunk math, the skip rule, and the
# sign-in refactor's safety.
# ---------------------------------------------------------------------------

import inspect  # noqa: E402
import subprocess  # noqa: E402

import sync_files  # noqa: E402
import sync_wheel  # noqa: E402

MB = 1024 * 1024


def test_sync_file_list_matches_the_contract():
    files = [(subdir, name) for subdir, name in sync_files.SYNC_FILES]
    assert files == [
        ("02_emr_data_dictionary",
         "02_emr_data_dictionary_extraction_table.json"),
        ("02_emr_data_dictionary",
         "02_emr_data_dictionary_extraction_column.json"),
        ("02_emr_data_dictionary",
         "02_emr_data_dictionary_extraction_join.json"),
        ("02_emr_data_dictionary",
         "02_emr_data_dictionary_extraction_value.json"),
        ("02_emr_data_dictionary",
         "02_emr_data_dictionary_extraction_value_embeddings.json"),
        ("02_emr_data_dictionary", "02_no_dictionary_match.json"),
        ("03_chat_bot", "03_chat_technical_terms.md"),
        ("03_chat_bot", "03_chat_abstract_names.json"),
    ]


def test_every_listed_local_file_exists():
    # the truth is present on this machine before anyone ships it
    for subdir, name in sync_files.SYNC_FILES:
        path = REPO_ROOT / "AIVIA_01_Data" / subdir / name
        assert path.exists(), f"missing local truth: {path}"


def test_sync_refuses_without_ids_naming_them():
    proc = subprocess.run(
        [sys.executable, str(CODE_DIR / "sync_files.py")],
        capture_output=True, text=True)
    assert proc.returncode != 0
    assert "--workspace" in proc.stderr
    assert "--lakehouse" in proc.stderr


def test_chunk_math():
    assert sync_files.chunk_spans(70 * MB) == [
        (0, 32 * MB), (32 * MB, 32 * MB), (64 * MB, 6 * MB)]
    assert sync_files.chunk_spans(1) == [(0, 1)]
    assert sync_files.chunk_spans(0) == []


def test_skip_rule():
    should = sync_files.should_upload
    assert should(100, 100, force=False) is False   # same size -> skip
    assert should(100, 99, force=False) is True     # drifted -> upload
    assert should(100, None, force=False) is True   # absent -> upload
    assert should(100, 100, force=True) is True     # the hammer


def test_sign_in_scope_default_is_unchanged():
    # the refactor must not change wheel-sync behavior
    sig = inspect.signature(sync_wheel.sign_in)
    assert sig.parameters["scope"].default == sync_wheel.FABRIC_SCOPE
    assert sync_files.STORAGE_SCOPE == "https://storage.azure.com/.default"


def test_wheel_carries_the_loader():
    pyproject = (CODE_DIR / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.3.0"' in pyproject
    for module in ("load_dictionary_tables", "dictionary_graph",
                   "chat_bot", "build_abstract_names"):
        assert module in pyproject, f"{module} missing from py-modules"
