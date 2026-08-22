"""The funnel view (family G): counts -> reasons, per run per stage."""

from src.governance.funnel import (
    FunnelStage,
    funnel_lines,
    funnel_rows,
    reasons_from_fallout,
)


class TestFunnelRows:
    def test_fell_off_and_reasons_rendered(self):
        rows = funnel_rows([FunnelStage(
            "200_parse", 100, 97,
            reasons={"parse_error": 3},
            derived_from="input_sql_sources -> ops_parse_successes")],
            run_at="t0")
        r = rows[0]
        assert r["fell_off"] == 3
        assert r["reasons"] == "parse_error:3"
        assert r["run_at"] == "t0"

    def test_unexplained_falloff_is_named_never_absorbed(self):
        """A fell-off count without matching fallout rows is itself a
        finding — the funnel says 'unexplained', loudly."""
        rows = funnel_rows([FunnelStage("03_graph", 50, 45,
                                        reasons={"no_transforms": 2})],
                           run_at="t")
        assert "unexplained:3" in rows[0]["reasons"]

    def test_clean_stage_has_no_reason_noise(self):
        rows = funnel_rows([FunnelStage("04_cards", 10, 10)], run_at="t")
        assert rows[0]["fell_off"] == 0 and rows[0]["reasons"] == ""

    def test_lines_show_the_arrow_shape(self):
        rows = funnel_rows([FunnelStage("200_parse", 100, 97,
                                        {"parse_error": 3})], run_at="t")
        lines = funnel_lines(rows)
        assert any("100 -> 97" in ln and "parse_error:3" in ln
                   for ln in lines)


class TestReasonsFromFallout:
    def test_latest_run_only_grouped_by_code(self):
        fallout = [
            {"stage": "060_partition_parse", "run_at": "t1",
             "reason_code": "non_sql_source:Excel.Workbook"},
            {"stage": "060_partition_parse", "run_at": "t2",
             "reason_code": "unrecognized_shape"},
            {"stage": "060_partition_parse", "run_at": "t2",
             "reason_code": "unrecognized_shape"},
            {"stage": "060_name_derivation", "run_at": "t2",
             "reason_code": "multi_report_consumer"},
        ]
        reasons = reasons_from_fallout(fallout, "060_partition_parse")
        assert reasons == {"unrecognized_shape": 2}  # t1 history excluded

    def test_absent_stage_is_empty(self):
        assert reasons_from_fallout([], "200_parse") == {}


class TestDrillHint:
    """Field find (Sunny, 2026-08-22): the funnel named the stage
    060_ingest_semantic_models; the fallout rows carried the sub-stage
    060_partition_parse — following the funnel's own string into
    ops_fallout found nothing. The printed line now carries the query
    that works."""

    def test_fell_off_line_carries_the_drill_query(self):
        from src.governance.funnel import FunnelStage, funnel_lines, funnel_rows
        rows = funnel_rows([FunnelStage(
            stage="060_ingest_semantic_models", in_count=11,
            out_count=10,
            reasons={"non_sql_source:Web.Contents": 1},
            derived_from="ops_fallout")], run_at="t")
        line = funnel_lines(rows)[1]
        assert "drill: ops_fallout WHERE stage LIKE '060_%'" in line

    def test_clean_stage_has_no_drill_noise(self):
        from src.governance.funnel import FunnelStage, funnel_lines, funnel_rows
        rows = funnel_rows([FunnelStage(
            stage="200_parse", in_count=28, out_count=28)], run_at="t")
        assert "drill:" not in funnel_lines(rows)[1]
