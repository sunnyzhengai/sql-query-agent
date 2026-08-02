"""Tests for the generic data-invariant checker (enforcement half of contracts)."""

from src.invariants import check_all_invariants, check_table_invariants

# A miniature registry exercising every invariant kind.
REGISTRY = {
    "graph_nodes": {
        "table_name": "graph_nodes",
        "status": "active",
        "columns": [("node_id", "string", False), ("layer", "string", False)],
        "invariants": [
            {"kind": "unique", "columns": ["node_id"]},
            {"kind": "allowed_values", "column": "layer",
             "values": ["canonical", "technical"]},
        ],
    },
    "graph_edges": {
        "table_name": "graph_edges",
        "status": "active",
        "columns": [("source_id", "string", False), ("target_id", "string", False)],
        "invariants": [
            {"kind": "reference", "column": "source_id", "references": "graph_nodes.node_id"},
        ],
    },
    "ops_future": {
        "table_name": "ops_future",
        "status": "planned",
        "columns": [("x", "string", False)],
        "invariants": [{"kind": "unique", "columns": ["x"]}],
    },
}

CLEAN_DATA = {
    "graph_nodes": [
        {"node_id": "c:1", "layer": "canonical"},
        {"node_id": "t:1", "layer": "technical"},
    ],
    "graph_edges": [
        {"source_id": "c:1", "target_id": "t:1"},
    ],
}


def _fetch(data):
    def fetch(table, columns):
        return [{c: row.get(c) for c in columns} for row in data[table]]
    return fetch


def test_clean_data_has_no_violations():
    violations = check_all_invariants(
        _fetch(CLEAN_DATA), lambda t: t in CLEAN_DATA, registry=REGISTRY
    )
    assert violations == {}


def test_unique_violation_is_reported_with_sample():
    data = {**CLEAN_DATA, "graph_nodes": [
        {"node_id": "c:1", "layer": "canonical"},
        {"node_id": "c:1", "layer": "canonical"},
    ]}
    violations = check_table_invariants("graph_nodes", _fetch(data), registry=REGISTRY)
    assert len(violations) == 1
    assert "unique" in violations[0] and "c:1" in violations[0]


def test_composite_unique_uses_all_columns():
    registry = {
        "t": {
            "table_name": "t", "status": "active",
            "columns": [("a", "string", False), ("b", "string", False)],
            "invariants": [{"kind": "unique", "columns": ["a", "b"]}],
        }
    }
    data = {"t": [{"a": "x", "b": "1"}, {"a": "x", "b": "2"}, {"a": "x", "b": "2"}]}
    violations = check_table_invariants("t", _fetch(data), registry=registry)
    assert len(violations) == 1 and "('x', '2')" in violations[0]


def test_allowed_values_violation_reports_bad_value():
    data = {**CLEAN_DATA, "graph_nodes": [
        {"node_id": "c:1", "layer": "canonical"},
        {"node_id": "z:9", "layer": "zombie"},
    ]}
    violations = check_table_invariants("graph_nodes", _fetch(data), registry=REGISTRY)
    assert len(violations) == 1 and "zombie" in violations[0]


def test_allowed_values_ignores_nulls():
    registry = {
        "t": {
            "table_name": "t", "status": "active",
            "columns": [("kind", "string", True)],
            "invariants": [{"kind": "allowed_values", "column": "kind",
                            "values": ["a", "b"]}],
        }
    }
    data = {"t": [{"kind": "a"}, {"kind": None}]}
    assert check_table_invariants("t", _fetch(data), registry=registry) == []


def test_reference_violation_reports_missing_target():
    data = {**CLEAN_DATA, "graph_edges": [
        {"source_id": "c:1", "target_id": "t:1"},
        {"source_id": "ghost:1", "target_id": "t:1"},
    ]}
    violations = check_table_invariants("graph_edges", _fetch(data), registry=REGISTRY)
    assert len(violations) == 1
    assert "ghost:1" in violations[0] and "graph_nodes.node_id" in violations[0]


def test_check_all_skips_planned_and_missing_tables():
    data = {"graph_nodes": CLEAN_DATA["graph_nodes"]}  # edges table absent
    violations = check_all_invariants(
        _fetch(data), lambda t: t in data, registry=REGISTRY
    )
    assert violations == {}  # planned ops_future and missing graph_edges skipped
