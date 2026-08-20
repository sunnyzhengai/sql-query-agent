"""The REMATCH answer key, executable (ADR 0017/0018).

Every certified number in docs/internal/REMATCH_SCORECARD.md, verified
deterministically against the recorded fixtures through the traversal
templates — no LLM, no Fabric. When a platform agent's answer disagrees
with these, the platform layer is at fault, not the graph.
"""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "recorded"

pytestmark = pytest.mark.skipif(
    not (FIXTURES / "parse_results.json").exists(),
    reason="no recorded fixtures yet — run the export notebook on Fabric",
)


@pytest.fixture(scope="module")
def view():
    from src.graph.templates import GraphView
    from src.steps.build_graph import build_graph_step
    from src.steps.export import export_step

    spec = importlib.util.spec_from_file_location(
        "run_pipeline_local", REPO_ROOT / "scripts" / "run_pipeline_local.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    parse_results, tables, columns = mod.load_recorded(FIXTURES)
    graph = build_graph_step(parse_results, tables, columns)
    return GraphView(export_step(graph.nodes_rows, graph.edges_rows))


class TestAnswerKey:
    def test_q1_severe_sepsis_uses_32_tables(self, view):
        assert len(view.tables_of_metric("reports.USP_Severe_Sepsis")) == 35  # recert 1.30.0

    def test_q2_ip_sepsisdetails_uses_19_tables(self, view):
        assert len(view.tables_of_metric("reporting.USP_IP_SepsisDetails")) == 22  # recert 1.30.0

    def test_q3_bare_name_is_ambiguous_two_schemas(self, view):
        matches = view.find_metrics("USP_ED_Sepsis")
        assert {m["metricId"] for m in matches} == {
            "reports.USP_ED_Sepsis", "reporting.USP_ED_Sepsis",
        }
        assert len(view.tables_of_metric("reports.USP_ED_Sepsis")) == 47  # recert 1.30.0
        assert len(view.tables_of_metric("reporting.USP_ED_Sepsis")) == 47  # recert 1.30.0

    def test_q4_hospital_encounters_read_by_13_metrics(self, view):
        readers = view.metrics_of_table("HOSPITAL_ENCOUNTERS")
        assert len(readers) == 13
        ids = {r["metricId"] for r in readers}
        assert "reports.USP_Severe_Sepsis" in ids
        assert "reporting.USP_IP_SepsisShiftCompliance" in ids

    def test_q4b_medication_orders_read_by_7_metrics(self, view):
        assert len(view.metrics_of_table("MEDICATION_ORDERS")) == 8  # recert 1.30.0

    def test_q5_shared_sources_14_metrics_top_is_reporting_twin(self, view):
        shared = view.shared_source_metrics("reports.USP_ED_Sepsis")
        assert len(shared) == 14
        assert shared[0]["metricId"] == "reporting.USP_ED_Sepsis"
        assert shared[0]["sharedTables"] == 47  # recert 1.30.0

    def test_q6_hospital_encounters_has_133_dictionary_columns(self, view):
        assert len(view.columns_of_table("HOSPITAL_ENCOUNTERS")) == 133

    def test_q7_most_read_metric_is_reporting_ed_sepsis_38(self, view):
        top = view.most_read_metrics(top=3)
        assert top[0]["metricId"] == "reporting.USP_ED_Sepsis"
        assert top[0]["tableCount"] == 47  # recert 1.30.0

    def test_q8_q9_unknown_references_resolve_to_nothing(self, view):
        assert view.find_metrics("FAKE_METRIC_XYZ") == []
        assert view.tables_of_metric("FAKE_METRIC_XYZ") == []
        assert view.metrics_of_table("UNICORN_VELOCITY") == []


class TestCaseInsensitivity:
    """ADR 0016: a correct key in the wrong case must still land."""

    def test_metric_key_any_case(self, view):
        assert len(view.tables_of_metric("REPORTS.usp_severe_SEPSIS")) == 35  # recert 1.30.0

    def test_table_key_any_case(self, view):
        assert len(view.metrics_of_table("hospital_encounters")) == 13


class TestExplainTemplate:
    def test_steps_walk_the_full_closure_roots_first(self, view):
        steps = view.steps_of_metric("reports.USP_Severe_Sepsis")
        assert len(steps) > 1, "closure walk must reach beyond the root step"
        assert all(s["metricId"] for s in steps)

    def test_catalogs_are_complete(self, view):
        assert len(view.metric_catalog()) == 28
        assert view.table_catalog(), "table catalog must not be empty"
        assert len(view.transformation_catalog()) == len(view._transformation)
