"""Tests for the pure pipeline step functions (src/steps/).

The final test runs the ENTIRE pipeline 02→05 through the step functions on
sample data — the offline execution slice 1 exists to enable.
"""

import pytest

from scripts.seed_sample_data import (
    SAMPLE_DICT_COLUMNS,
    SAMPLE_DICT_TABLES,
    SAMPLE_SQL_SOURCES,
)
from src.parser.sql_parser import parse_sql
from src.steps.build_graph import build_graph_step
from src.steps.export import export_step
from src.steps.gates import StepPostconditionError, postcondition_gate, tables_owned_by
from src.steps.metric_logic import metric_logic_step
from src.steps.parse import parse_step
from src.steps.readiness import readiness_gate


def _dict_rows():
    return list(SAMPLE_DICT_TABLES), list(SAMPLE_DICT_COLUMNS)


class TestParseStep:
    def test_every_source_gets_exactly_one_outcome(self):
        sources = SAMPLE_SQL_SOURCES + [
            {"metric_id": "dbo.BROKEN", "name": "BROKEN", "sql": ""},
        ]
        out = parse_step(sources, parse_sql)
        assert len(out.parse_results) + len(out.parse_errors) == len(sources)
        assert {e["metric_id"] for e in out.parse_errors} == {"dbo.BROKEN"}
        assert out.parse_errors[0]["error_category"]  # classified, not raw

    def test_error_log_records_failures_with_run_summary(self):
        sources = [{"metric_id": "dbo.BAD", "name": "BAD", "sql": ""}]
        out = parse_step(sources, parse_sql, previous_success_ids=["dbo.BAD"])
        assert out.error_log.current_run[0].status == "regressed"
        assert out.run_summary["regressions"] == 1


class TestBuildGraphStep:
    def test_relations_hold_on_sample_data(self):
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        tables, columns = _dict_rows()
        out = build_graph_step(parse_out.parse_results, tables, columns)
        assert out.node_count == len(out.nodes_rows)
        canonical = [r for r in out.nodes_rows if r["layer"] == "canonical"]
        assert len(canonical) == len(parse_out.parse_results)

    def test_steward_records_are_applied(self):
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        tables, columns = _dict_rows()
        metric_id = parse_out.parse_results[0]["metric_id"]
        out = build_graph_step(
            parse_out.parse_results, tables, columns,
            steward_records=[{"metric_id": metric_id, "metric_name": metric_id,
                              "steward_name": "Dr. Smith"}],
        )
        assert out.stewards_applied == 1


class TestMetricLogicStep:
    def test_one_row_per_canonical_node(self):
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        tables, columns = _dict_rows()
        graph = build_graph_step(parse_out.parse_results, tables, columns)
        rows = metric_logic_step(graph.nodes_rows, graph.edges_rows)
        assert len(rows) == len(parse_out.parse_results)
        assert all(r["metric_id"] for r in rows)


class TestExportStep:
    def test_export_partitions_nodes_and_edges(self):
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        tables, columns = _dict_rows()
        graph = build_graph_step(parse_out.parse_results, tables, columns)
        exported = export_step(graph.nodes_rows, graph.edges_rows)
        assert len(exported) == 9  # 4 node tables + 5 edge tables
        assert len(exported["graph_canonical"]) == len(parse_out.parse_results)
        assert exported["graph_edge_tab2col"], "column edges must be exported"


class TestPostconditionGate:
    def test_gate_checks_owned_tables_and_passes_clean_state(self):
        assert set(tables_owned_by("02_parse")) == {
            "ops_parse_results", "ops_parse_errors", "ops_parse_successes",
            "ops_error_log",
        }
        state = {"ops_parse_successes": [{"metric_id": "a", "name": "a",
                                          "cte_count": 1, "table_count": 1,
                                          "line_count": 1}]}
        def fetch(t, cols):
            return [{c: r.get(c) for c in cols} for r in state[t]]
        checked = postcondition_gate("02_parse", fetch, lambda t: t in state)
        assert checked == ["ops_parse_successes"]

    def test_gate_enforces_cross_table_relations(self):
        """04's gate must catch metric_logic drifting from the canonical count."""
        state = {
            "output_metric_logic": [
                {"metric_id": "dbo.A", "metric_name": "A", "description": None,
                 "steward": None, "developer": None, "transform_count": 1,
                 "calculation_logic": "x", "source_tables": "t",
                 "table_descriptions": None},
            ],
            "graph_nodes": [
                {"node_id": "canonical:dbo.A", "layer": "canonical", "name": "A",
                 "description": None, "properties": "{}"},
                {"node_id": "canonical:dbo.B", "layer": "canonical", "name": "B",
                 "description": None, "properties": "{}"},
            ],
            "input_sql_sources": [
                {"metric_id": "dbo.A", "name": "A", "sql": "s", "steward": None,
                 "developer": None, "source_type": "procedure", "source_schema": "dbo"},
            ],
        }
        def fetch(t, cols):
            return [{c: r.get(c) for c in cols} for r in state[t]]
        with pytest.raises(StepPostconditionError, match="relation violated"):
            postcondition_gate("04_build_metric_logic", fetch, lambda t: t in state)

    def test_gate_raises_on_contract_violation(self):
        state = {"ops_parse_successes": [
            {"metric_id": "a", "name": "a", "cte_count": 1, "table_count": 1, "line_count": 1},
            {"metric_id": "a", "name": "a", "cte_count": 1, "table_count": 1, "line_count": 1},
        ]}
        def fetch(t, cols):
            return [{c: r.get(c) for c in cols} for r in state[t]]
        with pytest.raises(StepPostconditionError, match="unique"):
            postcondition_gate("02_parse", fetch, lambda t: t in state)


class TestReadinessGate:
    def test_blocking_threshold_blocks(self):
        result = readiness_gate(
            {"parse_rate": (0.5, 0.9, True)}, {}, {}, False)
        assert result.blocked and any("BLOCKED" in line for line in result.lines)

    def test_ambiguity_blocks_unless_acknowledged(self):
        ambiguous = {"ENCOUNTER": ["REPORTING", "STAGING"]}
        assert readiness_gate({}, {}, ambiguous, False).blocked
        assert not readiness_gate({}, {}, ambiguous, True).blocked

    def test_clean_inputs_are_ready(self):
        result = readiness_gate({"parse_rate": (0.99, 0.9, True)}, {}, {}, False)
        assert not result.blocked


def test_full_pipeline_runs_offline_through_step_functions():
    """Slice 1's purpose: 02→05 executable with no Spark, no Fabric."""
    tables, columns = _dict_rows()

    parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
    graph = build_graph_step(parse_out.parse_results, tables, columns)
    metric_rows = metric_logic_step(graph.nodes_rows, graph.edges_rows)
    exported = export_step(graph.nodes_rows, graph.edges_rows)

    # End-to-end relational sanity: sources -> metrics, all layers present
    assert len(metric_rows) == len(SAMPLE_SQL_SOURCES) - len(parse_out.parse_errors)
    assert all(r["calculation_logic"] for r in metric_rows)
    layers = {r["layer"] for r in graph.nodes_rows}
    assert {"canonical", "transformation", "technical"} <= layers
    assert sum(len(v) for v in exported.values()) > 0
