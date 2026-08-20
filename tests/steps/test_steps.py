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
from src.steps.gates import (
    StepPostconditionError,
    StepPreconditionError,
    optional_inputs,
    postcondition_gate,
    precondition_gate,
    required_inputs,
    setup_completeness_rows,
    tables_owned_by,
)
from src.steps.metric_logic import metric_logic_step
from src.steps.parse import parse_step
from src.steps.readiness import (
    dictionary_coverage_threshold,
    readiness_gate,
    tech_table_names,
)


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

    def test_phi_scan_covers_unparseable_sources(self):
        sources = [{
            "metric_id": "dbo.BAD", "name": "BAD",
            "sql": "SELECT FROM WHERE PAT_MRN_ID = 1234567 (",  # won't parse
        }]
        out = parse_step(sources, parse_sql, scan_timestamp="2026-08-06T00:00:00Z")
        assert len(out.parse_errors) == 1  # parse failed...
        assert len(out.phi_findings) == 1  # ...but the literal was still caught
        assert out.phi_findings[0]["rule"] == "id_literal"
        assert out.phi_findings[0]["first_seen"] == "2026-08-06T00:00:00Z"

    def test_phi_dispositions_and_first_seen_survive_reruns(self):
        sources = [{
            "metric_id": "dbo.M", "name": "M",
            "sql": "SELECT 1 FROM t WHERE PAT_MRN_ID = 1234567",
        }]
        first = parse_step(sources, parse_sql, scan_timestamp="2026-01-01T00:00:00Z")
        prior = first.phi_findings
        prior[0]["disposition"] = "allow"  # steward: false positive
        second = parse_step(
            sources, parse_sql,
            previous_phi_records=prior, scan_timestamp="2026-08-06T00:00:00Z",
        )
        assert second.phi_findings[0]["disposition"] == "allow"
        assert second.phi_findings[0]["first_seen"] == "2026-01-01T00:00:00Z"


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
        assert len(exported) == 14  # 5 node tables + 8 edge tables + derived closure (ADR 0040)
        assert len(exported["graph_canonical"]) == len(parse_out.parse_results)
        assert exported["graph_edge_tab2col"], "column edges must be exported"

    def test_generator_compat_shape(self):
        """ADR 0020: name is schema-qualified (== metricId), bareName carries
        the object name, and CALCULATED_BY is the full step closure."""
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        tables, columns = _dict_rows()
        graph = build_graph_step(parse_out.parse_results, tables, columns)
        exported = export_step(graph.nodes_rows, graph.edges_rows)

        for row in exported["graph_canonical"]:
            assert row["name"] == row["metricId"]
            assert row["bareName"] and "." not in row["bareName"]

        c2t = exported["graph_edge_c2t"]
        transforms_by_metric: dict = {}
        for t in exported["graph_transformation"]:
            if t["metricId"]:
                transforms_by_metric.setdefault(t["metricId"], set()).add(t["nodeId"])
        for m in exported["graph_canonical"]:
            targets = {e["targetId"] for e in c2t if e["sourceId"] == m["nodeId"]}
            expected = transforms_by_metric.get(m["metricId"], set())
            assert expected <= targets, (
                f"{m['metricId']}: CALCULATED_BY closure missing steps"
            )

    def test_uses_table_closure_reaches_beyond_root_steps(self):
        """ADR 0018: the derived closure must cover the FULL DEPENDS_ON chain —
        a root-steps-only derivation is the exact silent-undercount defect."""
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        tables, columns = _dict_rows()
        graph = build_graph_step(parse_out.parse_results, tables, columns)
        exported = export_step(graph.nodes_rows, graph.edges_rows)

        uses = exported["graph_edge_uses_table"]
        assert uses, "closure must produce edges on sample data"
        # Every metric with any READS_FROM in its subgraph appears as a source
        canonical_ids = {r["nodeId"] for r in exported["graph_canonical"]}
        assert {r["sourceId"] for r in uses} <= canonical_ids
        # Closure >= shallow: for each metric, tables via closure must be a
        # superset of tables reachable from root steps only
        t2tech = {(r["sourceId"], r["targetId"]) for r in exported["graph_edge_t2tech"]}
        c2t = {(r["sourceId"], r["targetId"]) for r in exported["graph_edge_c2t"]}
        for metric in canonical_ids:
            roots = {t for (s, t) in c2t if s == metric}
            shallow = {tech for (s, tech) in t2tech if s in roots}
            closure = {r["targetId"] for r in uses if r["sourceId"] == metric}
            assert shallow <= closure, f"{metric}: closure missing root-level tables"


FAKE_REGISTRY = {
    "input_a": {
        "status": "active", "owner": {"notebook": "00_load"},
        "consumers": ["01_step"], "must_be_nonempty": True,
    },
    "input_b": {
        "status": "active", "owner": {"notebook": "00_load"},
        "consumers": ["01_step"],
    },
    "optional_c": {
        "status": "active", "owner": {"notebook": "90_util"},
        "consumers": ["01_step"], "optional_input": True,
        "remediation": "run 90_util to assign",
    },
    "self_state": {
        "status": "active", "owner": {"notebook": "01_step"},
        "consumers": ["01_step"],
    },
    "planned_d": {
        "status": "planned", "owner": {"notebook": "00_load"},
        "consumers": ["01_step"],
    },
}


class TestPreconditionGate:
    def test_required_inputs_derived_from_registry(self):
        # self-reads, optional inputs, and non-active tables are excluded
        assert required_inputs("01_step", FAKE_REGISTRY) == ["input_a", "input_b"]

    def test_missing_table_names_producer_and_contract(self):
        with pytest.raises(StepPreconditionError) as exc:
            precondition_gate("01_step", table_exists=lambda t: t == "input_b",
                              registry=FAKE_REGISTRY)
        msg = str(exc.value)
        assert "Preconditions failed for 01_step" in msg
        assert "input_a missing — produced by 00_load" in msg
        assert "contract:input_a" in msg
        assert exc.value.failures[0]["producer"] == "00_load"

    def test_empty_blocks_only_when_nonempty_required(self):
        counts = {"input_a": 0, "input_b": 0}
        with pytest.raises(StepPreconditionError) as exc:
            precondition_gate("01_step", table_exists=lambda t: True,
                              count=counts.get, registry=FAKE_REGISTRY)
        msg = str(exc.value)
        assert "input_a is empty" in msg
        assert "input_b" not in msg  # emptiness is legal without the flag

    def test_all_present_returns_checked(self):
        checked = precondition_gate("01_step", table_exists=lambda t: True,
                                    count=lambda t: 5, registry=FAKE_REGISTRY)
        assert checked == ["input_a", "input_b"]

    def test_optional_inputs_derived_with_remediation(self):
        assert optional_inputs("01_step", FAKE_REGISTRY) == ["optional_c"]

    def test_setup_completeness_rows_record_degraded_state(self):
        """A run proceeding without an optional input must leave queryable
        state (handoff item 3: 'legitimate-but-degraded' is a category
        between gate error and product defect — never only stdout)."""
        rows = setup_completeness_rows(
            "01_step", table_exists=lambda t: False,
            run_at="2026-08-15T00:00:00+00:00", registry=FAKE_REGISTRY)
        assert rows == [{
            "run_at": "2026-08-15T00:00:00+00:00",
            "step": "01_step",
            "table_name": "optional_c",
            "present": False,
            "remediation": "run 90_util to assign",
            "contract_id": "contract:optional_c",
        }]

    def test_setup_completeness_rows_record_present_state(self):
        rows = setup_completeness_rows(
            "01_step", table_exists=lambda t: True,
            run_at="t0", registry=FAKE_REGISTRY)
        assert len(rows) == 1 and rows[0]["present"] is True

    def test_production_registry_derivations(self):
        # Pin the real registry's derivations for the steps we wire up —
        # if a contract edit changes a step's required inputs, this fails.
        assert required_inputs("300_build_graph") == [
            "input_dict_columns", "input_dict_tables", "ops_parse_results",
        ]
        assert required_inputs("500_validate") == [
            "graph_edges", "graph_nodes", "input_dict_tables",
            "input_sql_sources", "ops_parse_errors",
            # leaf grounding (spec:C4, 1.29.0) reads the parse results
            "ops_parse_results", "ops_parse_successes",
            # freshness check (Trust family, 1.19.0): 06 reads the card
            # table — consistent with its "run 02-04 first" contract
            "output_metric_logic",
        ]
        assert required_inputs("600_generate_descriptions") == [
            "graph_edges", "graph_nodes", "ops_phi_findings",
            "output_metric_logic",
        ]


class TestPostconditionGate:
    def test_gate_checks_owned_tables_and_passes_clean_state(self):
        assert set(tables_owned_by("200_parse")) == {
            "ops_parse_results", "ops_parse_errors", "ops_parse_successes",
            "ops_error_log", "ops_phi_findings",
        }
        state = {"ops_parse_successes": [{"metric_id": "a", "name": "a",
                                          "cte_count": 1, "table_count": 1,
                                          "line_count": 1}]}
        def fetch(t, cols):
            return [{c: r.get(c) for c in cols} for r in state[t]]
        checked = postcondition_gate("200_parse", fetch, lambda t: t in state)
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
            postcondition_gate("400_build_metric_logic", fetch, lambda t: t in state)

    def test_gate_raises_on_contract_violation(self):
        state = {"ops_parse_successes": [
            {"metric_id": "a", "name": "a", "cte_count": 1, "table_count": 1, "line_count": 1},
            {"metric_id": "a", "name": "a", "cte_count": 1, "table_count": 1, "line_count": 1},
        ]}
        def fetch(t, cols):
            return [{c: r.get(c) for c in cols} for r in state[t]]
        with pytest.raises(StepPostconditionError, match="unique"):
            postcondition_gate("200_parse", fetch, lambda t: t in state)


class TestReadinessGate:
    def test_blocking_threshold_blocks(self):
        result = readiness_gate(
            {"parse_rate": (0.5, 0.9, True)}, {}, {}, False, required_checks=())
        assert result.blocked and any("BLOCKED" in line for line in result.lines)

    def test_ambiguity_blocks_unless_acknowledged(self):
        ambiguous = {"ENCOUNTER": ["REPORTING", "STAGING"]}
        assert readiness_gate({}, {}, ambiguous, False, required_checks=()).blocked
        assert not readiness_gate({}, {}, ambiguous, True, required_checks=()).blocked

    def test_clean_inputs_are_ready(self):
        result = readiness_gate(
            {"parse_rate": (0.99, 0.9, True)}, {}, {}, False, required_checks=())
        assert not result.blocked

    # Gate-integrity contract: a required check may FAIL, but it may never
    # silently DISAPPEAR from the gate (audit 2026-08-15: dictionary_coverage
    # vanished inside a try/except and the gate printed DEPLOYMENT READY).
    def test_missing_required_check_blocks(self):
        result = readiness_gate(
            {"parse_rate": (1.0, 0.9, True)}, {}, {}, False,
            required_checks=("parse_rate", "dictionary_coverage"))
        assert result.blocked
        assert any("gate_integrity" in line and "dictionary_coverage" in line
                   for line in result.lines)

    def test_required_checks_default_on(self):
        # Passing only one of the four default-required checks must block —
        # safe-by-default means a forgetful caller cannot weaken the gate.
        result = readiness_gate({"parse_rate": (1.0, 0.9, True)}, {}, {}, False)
        assert result.blocked

    def test_all_required_checks_present_and_passing_is_ready(self):
        thresholds = {
            "parse_rate": (0.99, 0.90, True),
            "calculation_logic": (0.95, 0.80, True),
            "traversal_coverage": (0.90, 0.70, False),
            "dictionary_coverage": (0.95, 0.90, True),
        }
        assert not readiness_gate(thresholds, {}, {}, False).blocked


class TestDictionaryCoverage:
    def test_full_coverage_passes(self):
        actual, threshold, blocking = dictionary_coverage_threshold(
            {"ENCOUNTERS", "PATIENTS"}, {"encounters", "PATIENTS"})
        assert actual == 1.0 and blocking

    def test_partial_coverage_measured(self):
        actual, _, _ = dictionary_coverage_threshold(
            {"ENCOUNTERS"}, {"ENCOUNTERS", "ORPHAN_TABLE"})
        assert actual == 0.5

    def test_empty_graph_is_zero_not_skipped(self):
        # The empty case is exactly when the gate matters most: it must
        # measure 0.0 and block, never vanish.
        actual, _, blocking = dictionary_coverage_threshold({"ENCOUNTERS"}, set())
        assert actual == 0.0 and blocking


class TestTechTableNames:
    def test_extracts_from_json_string_and_dict_props(self):
        nodes = [
            {"node_id": "tech:dbo.encounters",
             "properties": '{"schema": "dbo", "table": "ENCOUNTERS"}'},
            {"node_id": "tech:dbo.patients",
             "properties": {"schema": "dbo", "table": "Patients"}},
            {"node_id": "tech:dbo.encounters.enc_id",
             "properties": '{"table": "ENCOUNTERS", "column": "ENC_ID"}'},
            {"node_id": "canonical:m1", "properties": "{}"},
        ]
        assert tech_table_names(nodes) == {"ENCOUNTERS", "PATIENTS"}


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


class TestFreshness:
    """Trust columns (Question Map gap 2): freshness reaches the card."""

    ROWS = staticmethod(lambda logic="A then B": [
        {"metric_id": "rpt.USP_X", "calculation_logic": logic}])

    def test_new_metric_stamped_with_run_at(self):
        from src.steps.metric_logic import apply_freshness
        rows = self.ROWS()
        apply_freshness(rows, [], [], "2026-08-18T00:00:00Z")
        assert rows[0]["logic_last_changed_at"] == "2026-08-18T00:00:00Z"
        assert rows[0]["source_extracted_at"] is None

    def test_unchanged_logic_carries_previous_timestamp(self):
        from src.steps.metric_logic import apply_freshness
        rows = self.ROWS()
        prev = [{"metric_id": "RPT.USP_X", "calculation_logic": "A then B",
                 "logic_last_changed_at": "2026-01-01T00:00:00Z"}]
        apply_freshness(rows, prev, [], "2026-08-18T00:00:00Z")
        assert rows[0]["logic_last_changed_at"] == "2026-01-01T00:00:00Z"

    def test_changed_logic_restamps(self):
        from src.steps.metric_logic import apply_freshness
        rows = self.ROWS("A then C")
        prev = [{"metric_id": "rpt.USP_X", "calculation_logic": "A then B",
                 "logic_last_changed_at": "2026-01-01T00:00:00Z"}]
        apply_freshness(rows, prev, [], "2026-08-18T00:00:00Z")
        assert rows[0]["logic_last_changed_at"] == "2026-08-18T00:00:00Z"

    def test_source_extracted_at_from_tracker(self):
        from src.steps.metric_logic import apply_freshness
        rows = self.ROWS()
        tracker = [{"schema_name": "RPT", "object_name": "usp_x",
                    "extracted_at": "2026-08-10T00:00:00Z"}]
        apply_freshness(rows, [], tracker, "t")
        assert rows[0]["source_extracted_at"] == "2026-08-10T00:00:00Z"

    def test_stale_metrics_threshold_and_unknowns(self):
        from src.steps.readiness import stale_metrics
        rows = [
            {"metric_id": "a", "source_extracted_at": "2026-07-01T00:00:00Z"},
            {"metric_id": "b", "source_extracted_at": "2026-08-17T00:00:00Z"},
            {"metric_id": "c", "source_extracted_at": None},
        ]
        stale, unknown = stale_metrics(rows, "2026-08-18T00:00:00Z", 30)
        assert [s[0] for s in stale] == ["a"]
        assert stale[0][2] == 48
        assert unknown == 1
