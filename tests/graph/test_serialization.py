"""Tests for graph serialization — Delta rows ↔ in-memory objects."""

import json

from src.graph.serialization import (
    edges_to_rows,
    nodes_to_rows,
    parse_result_to_parsed_sql,
    parsed_sql_to_parse_result_row,
    rows_to_edges,
    rows_to_nodes,
)
from src.models import EdgeType, NodeLayer
from src.parser.sql_parser import parse_sql
from src.schemas import PARSE_RESULTS


def test_rows_to_nodes_roundtrip():
    rows = [{
        "node_id": "canonical:test",
        "layer": "canonical",
        "name": "Test Metric",
        "description": "A test",
        "properties": json.dumps({"steward": "Alice"}),
    }]
    nodes = rows_to_nodes(rows)
    assert len(nodes) == 1
    assert nodes["canonical:test"].layer == NodeLayer.CANONICAL
    assert nodes["canonical:test"].properties["steward"] == "Alice"

    # Roundtrip back to rows
    out_rows = nodes_to_rows(nodes)
    assert len(out_rows) == 1
    assert out_rows[0][0] == "canonical:test"
    assert out_rows[0][1] == "canonical"


def test_rows_to_edges_roundtrip():
    rows = [{
        "source_id": "canonical:test",
        "target_id": "transform:test:cte1",
        "edge_type": "canonical_to_transform",
        "properties": "{}",
    }]
    edges = rows_to_edges(rows)
    assert len(edges) == 1
    assert edges[0].edge_type == EdgeType.CANONICAL_TO_TRANSFORM

    out_rows = edges_to_rows(edges)
    assert len(out_rows) == 1
    assert out_rows[0][2] == "canonical_to_transform"


def test_parse_result_to_parsed_sql():
    pr = {
        "metric_id": "test",
        "name": "Test",
        "ctes_json": json.dumps([{
            "name": "cte1",
            "sql_fragment": "SELECT * FROM t1",
            "table_refs": [{"table": "t1", "schema": "dbo", "database": None}],
            "depends_on": [],
        }]),
        "final_select_tables": json.dumps([
            {"table": "t2", "schema": "dbo", "database": None}
        ]),
        "final_select_cte_refs": json.dumps(["cte1"]),
    }
    parsed = parse_result_to_parsed_sql(pr)
    assert len(parsed.ctes) == 1
    assert parsed.ctes[0].name == "cte1"
    assert len(parsed.final_select_tables) == 1
    assert parsed.final_select_tables[0].table == "t2"
    assert parsed.final_select_cte_refs == ["cte1"]


def test_parse_result_full_roundtrip():
    """The 02→03 payload contract: writer and reader must be inverses.

    parse → serialize (what 02 stores) → deserialize (what 03 reads) must
    preserve every fact — including column_refs, which were previously
    written but dropped at read.
    """
    sql = """
    WITH er_visits AS (
        SELECT e.encounter_id, e.admit_dt
        FROM encounter e
        INNER JOIN department d ON e.department_id = d.department_id
    ),
    los_calc AS (
        SELECT encounter_id, DATEDIFF(MINUTE, admit_dt, discharge_dt) AS los
        FROM er_visits
    )
    SELECT AVG(los) FROM los_calc
    """
    parsed = parse_sql(sql)
    row = parsed_sql_to_parse_result_row("dbo.ER_LOS", "ER_LOS", parsed)
    restored = parse_result_to_parsed_sql(row)

    assert [c.name for c in restored.ctes] == [c.name for c in parsed.ctes]
    for orig, back in zip(parsed.ctes, restored.ctes):
        assert back.sql_fragment == orig.sql_fragment
        assert back.depends_on == orig.depends_on
        assert [(t.schema, t.table) for t in back.table_refs] == \
               [(t.schema, t.table) for t in orig.table_refs]
        assert [(c.table, c.column) for c in back.column_refs] == \
               [(c.table, c.column) for c in orig.column_refs]
        assert orig.column_refs, "fixture must exercise column_refs"

    assert [(t.schema, t.table) for t in restored.final_select_tables] == \
           [(t.schema, t.table) for t in parsed.final_select_tables]
    assert restored.final_select_cte_refs == parsed.final_select_cte_refs
    assert restored.normalized_sql == parsed.normalized_sql


def test_writer_row_matches_the_contract_shape():
    """Every contract column present, nothing extra (ops_parse_results)."""
    parsed = parse_sql("SELECT 1 AS x FROM t1")
    row = parsed_sql_to_parse_result_row("dbo.M", "M", parsed)
    assert set(row) == {c[0] for c in PARSE_RESULTS["columns"]}


def test_reader_tolerates_rows_without_column_refs():
    """Legacy rows (written before column_refs were read) must still load."""
    pr = {
        "ctes_json": json.dumps([{
            "name": "cte1",
            "sql_fragment": "SELECT 1",
            "table_refs": [],
            "depends_on": [],
        }]),
        "final_select_tables": json.dumps([]),
        "final_select_cte_refs": json.dumps([]),
    }
    parsed = parse_result_to_parsed_sql(pr)
    assert parsed.ctes[0].column_refs == []


def test_parse_result_legacy_string_table_refs():
    """Handle old format where table_refs were plain strings."""
    pr = {
        "ctes_json": json.dumps([{
            "name": "cte1",
            "sql_fragment": "SELECT 1",
            "table_refs": ["legacy_table"],
            "depends_on": [],
        }]),
        "final_select_tables": json.dumps(["another_table"]),
        "final_select_cte_refs": json.dumps([]),
    }
    parsed = parse_result_to_parsed_sql(pr)
    assert parsed.ctes[0].table_refs[0].table == "legacy_table"
    assert parsed.final_select_tables[0].table == "another_table"
