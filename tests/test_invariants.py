"""Tests for the generic data-invariant checker (enforcement half of contracts)."""

from src.invariants import (
    check_all_invariants,
    check_table_invariants,
    check_table_relations,
)

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


def test_fold_case_unique_catches_case_variant_duplicates():
    registry = {
        "t": {
            "table_name": "t", "status": "active",
            "columns": [("name", "string", False)],
            "invariants": [{"kind": "unique", "columns": ["name"], "fold_case": True}],
        }
    }
    data = {"t": [{"name": "Encounter"}, {"name": "ENCOUNTER"}]}
    violations = check_table_invariants("t", _fetch(data), registry=registry)
    assert len(violations) == 1 and "ENCOUNTER" in violations[0]

    # Without folding, the same data passes
    registry["t"]["invariants"] = [{"kind": "unique", "columns": ["name"]}]
    assert check_table_invariants("t", _fetch(data), registry=registry) == []


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


RELATION_REGISTRY = {
    "output_metric_logic": {
        "table_name": "output_metric_logic",
        "status": "active",
        "columns": [("metric_id", "string", False)],
        "invariants": [],
        "relations": [
            {"kind": "count_equals", "other_table": "graph_nodes",
             "other_where": {"layer": "canonical"}},
        ],
    },
    "graph_nodes": {
        "table_name": "graph_nodes",
        "status": "active",
        "columns": [("node_id", "string", False), ("layer", "string", False)],
        "invariants": [],
    },
}


def test_count_equals_relation_passes_when_counts_match():
    data = {
        "output_metric_logic": [{"metric_id": "a"}, {"metric_id": "b"}],
        "graph_nodes": [
            {"node_id": "c:a", "layer": "canonical"},
            {"node_id": "c:b", "layer": "canonical"},
            {"node_id": "t:x", "layer": "technical"},
        ],
    }
    violations = check_table_relations(
        "output_metric_logic", _fetch(data), lambda t: t in data,
        registry=RELATION_REGISTRY,
    )
    assert violations == []


def test_count_equals_relation_reports_mismatch():
    data = {
        "output_metric_logic": [{"metric_id": "a"}],
        "graph_nodes": [
            {"node_id": "c:a", "layer": "canonical"},
            {"node_id": "c:b", "layer": "canonical"},
        ],
    }
    violations = check_table_relations(
        "output_metric_logic", _fetch(data), lambda t: t in data,
        registry=RELATION_REGISTRY,
    )
    assert len(violations) == 1
    assert "1" in violations[0] and "2" in violations[0]


def test_relation_skipped_when_other_table_missing():
    data = {"output_metric_logic": [{"metric_id": "a"}]}
    violations = check_table_relations(
        "output_metric_logic", _fetch(data), lambda t: t in data,
        registry=RELATION_REGISTRY,
    )
    assert violations == []


def test_check_all_skips_planned_and_missing_tables():
    data = {"graph_nodes": CLEAN_DATA["graph_nodes"]}  # edges table absent
    violations = check_all_invariants(
        _fetch(data), lambda t: t in data, registry=REGISTRY
    )
    assert violations == {}  # planned ops_future and missing graph_edges skipped
