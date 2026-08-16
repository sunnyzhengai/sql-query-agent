"""Proc parity: the golden corpus through the extractor path.

The extractor is the turn-key front door (procs AND views), but the
proven ingestion path was manual file load. These tests run the 28
anonymized golden procedures through the extractor pipeline — discovery
filter, hash/change tracking, sql_sources production — and prove the
extracted output is byte-identical to what the file-loaded path feeds
02_parse. Input parity is the whole claim: 02's ScriptDom is
deterministic, so identical input text means identical parse results
(live confirmation on Fabric is a run of extract_views + 02 against the
demo database).

MERGE parity: the notebook MERGE uses UPDATE SET * / INSERT *, which
requires the extractor's row shape to match the input_sql_sources
contract exactly — asserted here against TABLE_REGISTRY so the 5-vs-7
column mismatch class (found 2026-08-16) cannot recur silently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.config import DomainFilterConfig
from src.extractor.discovery import build_discovery_query
from src.extractor.extractor import ViewExtractor
from src.extractor.tracker import compute_sql_hash
from src.schemas import SQL_SOURCES

SQL_DIR = Path(__file__).parent.parent.parent / "data" / "synthetic" / "sql"
GOLDEN_FILES = sorted(SQL_DIR.rglob("*.sql"))


def _discovered_rows() -> "list[dict[str, Any]]":
    """The golden corpus as sys.sql_modules would serve it.

    SQL Server stores definitions with \r\n line endings; the on-disk
    fixtures are \n. Serve \r\n so the test proves the extractor
    normalizes back — the parity claim is against the file bytes.
    """
    rows = []
    for f in GOLDEN_FILES:
        rows.append({
            "schema_name": f.parent.name,
            "object_name": f.stem,
            "object_type": "SQL_STORED_PROCEDURE",
            "sql_definition": f.read_text().replace("\n", "\r\n"),
        })
    return rows


class _CorpusConnection:
    def __init__(self, rows: "list[dict[str, Any]]") -> None:
        self.rows = rows

    def execute_query(self, sql: str) -> "list[dict[str, Any]]":
        return self.rows


@pytest.fixture(scope="module")
def extraction():
    domain = DomainFilterConfig(schemas=["reporting", "reports"])
    conn = _CorpusConnection(_discovered_rows())
    return ViewExtractor(conn, domain).extract()


def test_corpus_present():
    assert len(GOLDEN_FILES) >= 28, "anonymized golden corpus missing"


def test_default_discovery_includes_procs():
    query = build_discovery_query(DomainFilterConfig(schemas=["reporting"]))
    assert "'SQL_STORED_PROCEDURE'" in query
    assert "'VIEW'" in query


def test_extracted_sql_is_byte_identical_to_file_loaded(extraction):
    """Input parity: extracted == file bytes, \r\n normalized away."""
    by_id = {s["metric_id"]: s for s in extraction.sql_sources}
    assert len(by_id) == len(GOLDEN_FILES)
    for f in GOLDEN_FILES:
        metric_id = f"{f.parent.name}.{f.stem}"
        assert by_id[metric_id]["sql"] == f.read_text(), (
            f"{metric_id}: extractor output differs from the file-loaded bytes"
        )


def test_rows_match_sql_sources_contract(extraction):
    """MERGE SET */INSERT * requires the exact contract column set."""
    contract_columns = {name for name, _, _ in SQL_SOURCES["columns"]}
    for row in extraction.sql_sources:
        assert set(row) == contract_columns


def test_source_type_vocabulary_matches_file_loader(extraction):
    """load_sql_files writes 'stored_procedure'/'view'; extractor must agree."""
    assert {s["source_type"] for s in extraction.sql_sources} == {"stored_procedure"}
    schemas = {s["source_schema"] for s in extraction.sql_sources}
    assert schemas == {"reporting", "reports"}


def test_rerun_with_tracking_is_all_unchanged(extraction):
    conn = _CorpusConnection(_discovered_rows())
    result = ViewExtractor(conn, DomainFilterConfig()).extract(
        existing_tracking=extraction.tracking_records
    )
    assert result.summary.unchanged_count == len(GOLDEN_FILES)
    assert result.sql_sources == []


def test_edited_proc_is_detected_as_changed(extraction):
    rows = _discovered_rows()
    rows[0]["sql_definition"] += "\r\n-- hotfix"
    conn = _CorpusConnection(rows)
    result = ViewExtractor(conn, DomainFilterConfig()).extract(
        existing_tracking=extraction.tracking_records
    )
    assert result.summary.changed_count == 1
    assert result.summary.unchanged_count == len(GOLDEN_FILES) - 1


def test_hash_survives_line_ending_normalization():
    """\r\n vs \n must not read as a change — same object, same hash."""
    assert compute_sql_hash("SELECT a\r\nFROM t") == compute_sql_hash("SELECT a\nFROM t")
