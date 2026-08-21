"""The audit's pure logic (the store-facing main() is measured live,
not tested here — L2 stratum)."""

from devtools.reachability_audit import (
    transform_residual_offenders,
    undeclared_payloads,
)


class TestUndeclaredPayloads:
    def test_current_store_shape_is_fully_declared(self):
        out = undeclared_payloads(
            ["canonical", "transform", "tech", "decision", "report",
             "measure"],
            ["canonical_to_transform", "step_to_decision",
             "report_to_measure"],
            ["metric", "step", "report", "measure"])
        assert out == []

    def test_new_layer_without_a_row_is_named(self):
        out = undeclared_payloads(["canonical", "annotation"], [], [])
        assert out == ["node prefix 'annotation' (layer None)"]

    def test_new_edge_type_without_a_row_is_named(self):
        out = undeclared_payloads([], ["metric_to_kpi"], [])
        assert out == ["edge type 'metric_to_kpi'"]

    def test_new_catalog_kind_without_a_row_is_named(self):
        assert undeclared_payloads([], [], ["kpi"]) == [
            "catalog kind 'kpi'"]


class TestTransformResidual:
    def test_final_select_terminals_are_the_sanctioned_residual(self):
        assert transform_residual_offenders(
            ["__final_select__", "__final_select__"]) == []

    def test_a_real_step_outside_the_catalog_is_an_offender(self):
        assert transform_residual_offenders(
            ["__final_select__", "Scores"]) == ["Scores"]
