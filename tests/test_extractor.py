"""Unit tests for the view extractor module."""

from __future__ import annotations

from typing import Any

from src.config import DomainFilterConfig
from src.extractor.discovery import DiscoveredObject, build_discovery_query, strip_create_prefix
from src.extractor.extractor import ViewExtractor
from src.extractor.tracker import ExtractionTracker, compute_sql_hash


# --- Hash tests ---


class TestComputeSqlHash:
    def test_identical_sql(self):
        assert compute_sql_hash("SELECT a FROM t") == compute_sql_hash("SELECT a FROM t")

    def test_whitespace_normalized(self):
        h1 = compute_sql_hash("SELECT  a\n  FROM   t")
        h2 = compute_sql_hash("SELECT a FROM t")
        assert h1 == h2

    def test_case_insensitive(self):
        h1 = compute_sql_hash("SELECT A FROM T")
        h2 = compute_sql_hash("select a from t")
        assert h1 == h2

    def test_different_sql_different_hash(self):
        assert compute_sql_hash("SELECT a FROM t") != compute_sql_hash("SELECT b FROM t")


# --- Tracker tests ---


class TestExtractionTracker:
    def _make_obj(self, name: str, sql: str = "SELECT 1") -> DiscoveredObject:
        return DiscoveredObject(
            schema_name="dbo", object_name=name, object_type="VIEW", sql_definition=sql
        )

    def test_all_new_when_no_tracking(self):
        tracker = ExtractionTracker()
        objs = [self._make_obj("v1"), self._make_obj("v2")]
        delta = tracker.compute_delta(objs)
        assert len(delta.new) == 2
        assert len(delta.changed) == 0
        assert len(delta.unchanged) == 0
        assert len(delta.deleted) == 0

    def test_unchanged_when_hash_matches(self):
        sql = "SELECT col FROM tbl"
        tracking = [{
            "object_id": "dbo.v1",
            "schema_name": "dbo",
            "object_name": "v1",
            "object_type": "VIEW",
            "sql_hash": compute_sql_hash(sql),
            "extracted_at": "2026-01-01",
            "sql_definition": sql,
            "status": "current",
        }]
        tracker = ExtractionTracker(tracking)
        delta = tracker.compute_delta([self._make_obj("v1", sql)])
        assert len(delta.unchanged) == 1
        assert len(delta.new) == 0
        assert len(delta.changed) == 0

    def test_changed_when_hash_differs(self):
        tracking = [{
            "object_id": "dbo.v1",
            "schema_name": "dbo",
            "object_name": "v1",
            "object_type": "VIEW",
            "sql_hash": compute_sql_hash("SELECT old FROM tbl"),
            "extracted_at": "2026-01-01",
            "sql_definition": "SELECT old FROM tbl",
            "status": "current",
        }]
        tracker = ExtractionTracker(tracking)
        delta = tracker.compute_delta([self._make_obj("v1", "SELECT new_col FROM tbl")])
        assert len(delta.changed) == 1
        assert len(delta.new) == 0

    def test_deleted_when_not_discovered(self):
        tracking = [{
            "object_id": "dbo.v1",
            "schema_name": "dbo",
            "object_name": "v1",
            "object_type": "VIEW",
            "sql_hash": "abc",
            "extracted_at": "2026-01-01",
            "sql_definition": "SELECT 1",
            "status": "current",
        }]
        tracker = ExtractionTracker(tracking)
        delta = tracker.compute_delta([])  # nothing discovered
        assert len(delta.deleted) == 1
        assert delta.deleted[0] == "dbo.v1"

    def test_build_updated_records(self):
        tracker = ExtractionTracker()
        obj = self._make_obj("v1", "SELECT 1")
        delta = tracker.compute_delta([obj])
        records = tracker.build_updated_records(delta, [obj])
        assert len(records) == 1
        assert records[0]["object_id"] == "dbo.v1"
        assert records[0]["status"] == "current"


# --- Discovery query tests ---


class TestBuildDiscoveryQuery:
    def test_schema_only(self):
        domain = DomainFilterConfig(schemas=["dbo", "reporting"])
        query = build_discovery_query(domain)
        assert "s.name IN ('dbo', 'reporting')" in query
        assert "sql_expression_dependencies" not in query

    def test_table_only(self):
        domain = DomainFilterConfig(base_tables=["encounter", "patient"])
        query = build_discovery_query(domain)
        assert "referenced_entity_name IN ('encounter', 'patient')" in query
        assert "sql_expression_dependencies" in query

    def test_combined(self):
        domain = DomainFilterConfig(schemas=["dbo"], base_tables=["encounter"])
        query = build_discovery_query(domain)
        assert "s.name IN ('dbo')" in query
        assert "referenced_entity_name IN ('encounter')" in query

    def test_no_filter(self):
        domain = DomainFilterConfig()
        query = build_discovery_query(domain)
        assert "type_desc IN" in query
        assert "s.name IN" not in query
        assert "referenced_entity_name IN" not in query


# --- CREATE VIEW stripping tests ---


class TestStripCreatePrefix:
    def test_simple_create_view(self):
        sql = "CREATE VIEW dbo.v1 AS SELECT a, b FROM t1"
        result = strip_create_prefix(sql)
        assert result.upper().startswith("SELECT")
        assert "CREATE" not in result.upper()

    def test_create_or_alter_view(self):
        sql = "CREATE OR ALTER VIEW dbo.v1 AS SELECT a FROM t1"
        result = strip_create_prefix(sql)
        assert "SELECT" in result.upper()

    def test_plain_select_passthrough(self):
        sql = "SELECT a, b FROM t1 WHERE x = 1"
        result = strip_create_prefix(sql)
        assert "SELECT" in result.upper()

    def test_with_cte(self):
        sql = "CREATE VIEW dbo.v1 AS WITH cte AS (SELECT 1 AS x) SELECT x FROM cte"
        result = strip_create_prefix(sql)
        assert "WITH" in result.upper() or "SELECT" in result.upper()


# --- End-to-end extractor test with mock connection ---


class MockConnection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        return self.rows


class TestViewExtractor:
    def test_extract_new_views(self):
        mock_rows = [
            {
                "schema_name": "dbo",
                "object_name": "vw_er_los",
                "object_type": "VIEW",
                "sql_definition": "CREATE VIEW dbo.vw_er_los AS SELECT encounter_id FROM encounter",
            },
            {
                "schema_name": "reporting",
                "object_name": "vw_patient_count",
                "object_type": "VIEW",
                "sql_definition": "CREATE VIEW reporting.vw_patient_count AS SELECT COUNT(*) AS cnt FROM patient",
            },
        ]
        conn = MockConnection(mock_rows)
        domain = DomainFilterConfig(schemas=["dbo", "reporting"])
        extractor = ViewExtractor(conn, domain)
        result = extractor.extract()

        assert result.summary.total_discovered == 2
        assert result.summary.new_count == 2
        assert len(result.sql_sources) == 2
        assert result.sql_sources[0]["metric_id"] == "dbo.vw_er_los"
        # SQL should have CREATE VIEW stripped
        assert "CREATE" not in result.sql_sources[0]["sql"].upper()

    def test_extract_with_existing_tracking(self):
        sql = "CREATE VIEW dbo.vw_old AS SELECT 1 AS x"
        mock_rows = [
            {
                "schema_name": "dbo",
                "object_name": "vw_old",
                "object_type": "VIEW",
                "sql_definition": sql,
            },
        ]
        tracking = [{
            "object_id": "dbo.vw_old",
            "schema_name": "dbo",
            "object_name": "vw_old",
            "object_type": "VIEW",
            "sql_hash": compute_sql_hash(sql),
            "extracted_at": "2026-01-01",
            "sql_definition": sql,
            "status": "current",
        }]
        conn = MockConnection(mock_rows)
        domain = DomainFilterConfig()
        extractor = ViewExtractor(conn, domain)
        result = extractor.extract(existing_tracking=tracking)

        assert result.summary.unchanged_count == 1
        assert result.summary.new_count == 0
        assert len(result.sql_sources) == 0  # nothing new to write
