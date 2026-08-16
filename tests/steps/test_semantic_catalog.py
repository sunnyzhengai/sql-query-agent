"""Tests for the semantic catalog build step (ADR 0030 L3)."""

import json

from scripts.seed_sample_data import (
    SAMPLE_DICT_COLUMNS,
    SAMPLE_DICT_TABLES,
    SAMPLE_SQL_SOURCES,
)
from src.parser.sql_parser import parse_sql
from src.schemas import SEMANTIC_CATALOG
from src.steps.build_graph import build_graph_step
from src.steps.parse import parse_step
from src.steps.semantic_catalog import build_semantic_catalog


def sample_graph(**kwargs):
    parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
    return build_graph_step(
        parse_out.parse_results, list(SAMPLE_DICT_TABLES),
        list(SAMPLE_DICT_COLUMNS), **kwargs
    )


class TestBuild:
    def test_every_metric_and_named_step_has_a_row(self):
        g = sample_graph()
        out = build_semantic_catalog(g.nodes_rows)
        kinds = {}
        for r in out.rows:
            kinds.setdefault(r["kind"], 0)
            kinds[r["kind"]] += 1
        assert kinds["metric"] == out.metric_count > 0
        assert kinds.get("step", 0) == out.step_count
        assert all(not r["name"].startswith("__") for r in out.rows)

    def test_step_search_text_has_no_identity_leak(self):
        """Live find 2026-08-13: metric_id in step search_text made
        every step of USP_ED_Sepsis match 'ED sepsis' regardless of
        content — steps must match on their OWN definition only."""
        g = sample_graph()
        out = build_semantic_catalog(g.nodes_rows)
        steps = [r for r in out.rows if r["kind"] == "step"]
        assert steps
        for r in steps:
            assert r["ref"] not in r["search_text"]
            assert r["ref"] in r["display_text"]   # provenance still shown

    def test_business_name_and_report_flow_into_search_text(self):
        g = sample_graph(metric_name_records=[{
            "metric_id": SAMPLE_SQL_SOURCES[0]["metric_id"],
            "business_name": "Friendly Name",
            "report_name": "Ops Dashboard",
            "source": "manual",
        }])
        out = build_semantic_catalog(g.nodes_rows)
        row = next(r for r in out.rows
                   if r["ref"] == SAMPLE_SQL_SOURCES[0]["metric_id"]
                   and r["kind"] == "metric")
        assert "Friendly Name" in row["search_text"]
        assert "Ops Dashboard" in row["search_text"]
        assert row["display_text"].startswith("Friendly Name")

    def test_terms_ride_with_linked_refs_in_search_text(self):
        g = sample_graph()
        out = build_semantic_catalog(
            g.nodes_rows,
            term_records=[{"term_id": "t1", "name": "Cancelled Appointment",
                           "definition": "Appointments marked cancelled.",
                           "status": "emergent"}],
            term_links=[{"term_id": "t1", "node_ref": "dbo.M1",
                         "node_kind": "metric", "role": "defines"}],
        )
        term_rows = [r for r in out.rows if r["kind"] == "term"]
        assert len(term_rows) == 1 == out.term_count
        assert "dbo.M1" in term_rows[0]["search_text"]
        assert "emergent term" in term_rows[0]["display_text"]

    def test_rows_match_contract_columns_plus_nothing(self):
        g = sample_graph()
        out = build_semantic_catalog(g.nodes_rows)
        contract_cols = {c[0] for c in SEMANTIC_CATALOG["columns"]}
        assert set(out.rows[0].keys()) == contract_cols

    def test_rows_are_json_serializable_and_ids_unique(self):
        g = sample_graph()
        out = build_semantic_catalog(g.nodes_rows)
        json.dumps(out.rows)
        ids = [r["node_id"] for r in out.rows]
        assert len(ids) == len(set(ids))


class TestConsumptionKinds:
    """Reports and measures are searchable (ADR 0040)."""

    def _rows(self):
        import json
        return [
            {"node_id": "report:SEPSIS DASH", "layer": "report",
             "name": "Sepsis Dash", "description": "Screening compliance.",
             "properties": json.dumps({})},
            {"node_id": "measure:SEPSIS DASH:T[Rate]", "layer": "measure",
             "name": "Rate", "description": "Share compliant.",
             "properties": json.dumps({"report_name": "Sepsis Dash"})},
        ]

    def test_report_and_measure_rows_emitted(self):
        from src.steps.semantic_catalog import build_semantic_catalog
        out = build_semantic_catalog(self._rows())
        kinds = {r["kind"] for r in out.rows}
        assert kinds == {"report", "measure"}
        assert out.report_count == 1 and out.measure_count == 1

    def test_measure_search_text_excludes_report_identity(self):
        # identity-leak lesson (2026-08-13): a measure matches on ITS
        # definition; its report's name must not score it
        from src.steps.semantic_catalog import build_semantic_catalog
        out = build_semantic_catalog(self._rows())
        measure = next(r for r in out.rows if r["kind"] == "measure")
        assert "Sepsis Dash" not in measure["search_text"]
        assert "Sepsis Dash" in measure["display_text"]
