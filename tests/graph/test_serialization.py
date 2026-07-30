"""Tests for graph serialization — Delta rows ↔ in-memory objects."""

import json

from src.graph.serialization import (
    rows_to_nodes, rows_to_edges, nodes_to_rows, edges_to_rows,
    parse_result_to_parsed_sql,
)
from src.models import NodeLayer, EdgeType


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
