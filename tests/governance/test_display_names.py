"""Tests for business-friendly metric names (input_metric_names -> graph)."""

from scripts.extract_pbix_sources import (
    build_metric_name_records,
    friendly_name_from_report,
)
from scripts.seed_sample_data import (
    SAMPLE_DICT_COLUMNS,
    SAMPLE_DICT_TABLES,
    SAMPLE_SQL_SOURCES,
)
from src.governance.display_names import apply_business_names
from src.graph.builder import GraphBuilder
from src.parser.sql_parser import parse_sql
from src.steps.build_graph import build_graph_step
from src.steps.parse import parse_step


def builder_with(*metric_ids):
    b = GraphBuilder()
    for mid in metric_ids:
        b.add_canonical_node(mid, mid.split(".")[-1])
    return b


class TestApply:
    def test_qualified_match_case_insensitive(self):
        b = builder_with("reporting.USP_ED_Sepsis")
        applied, skipped = apply_business_names(b, [
            {"metric_id": "REPORTING.usp_ed_sepsis",
             "business_name": "ED Sepsis Screening", "source": "manual"},
        ])
        assert (applied, skipped) == (1, [])
        node = b.nodes["canonical:reporting.USP_ED_Sepsis"]
        assert node.properties["business_name"] == "ED Sepsis Screening"
        assert node.properties["business_name_source"] == "manual"

    def test_unambiguous_bare_name_resolves(self):
        b = builder_with("reporting.USP_IP_SepsisDetails")
        applied, skipped = apply_business_names(b, [
            {"metric_id": "USP_IP_SepsisDetails", "business_name": "Sepsis Details"},
        ])
        assert (applied, skipped) == (1, [])

    def test_ambiguous_bare_name_skipped_never_guessed(self):
        b = builder_with("reporting.USP_ED_Sepsis", "reports.USP_ED_Sepsis")
        applied, skipped = apply_business_names(b, [
            {"metric_id": "USP_ED_Sepsis", "business_name": "ED Sepsis"},
        ])
        assert applied == 0
        assert len(skipped) == 1 and "2 schemas" in skipped[0]
        for node in b.nodes.values():
            assert "business_name" not in node.properties

    def test_unknown_metric_reported(self):
        b = builder_with("reporting.USP_ED_Sepsis")
        applied, skipped = apply_business_names(b, [
            {"metric_id": "dbo.NOPE", "business_name": "Ghost"},
        ])
        assert applied == 0 and "no such metric" in skipped[0]


class TestPipelineFlow:
    def test_business_name_flows_to_metric_logic_and_export(self):
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        target = parse_out.parse_results[0]["metric_id"]
        out = build_graph_step(
            parse_out.parse_results,
            list(SAMPLE_DICT_TABLES), list(SAMPLE_DICT_COLUMNS),
            metric_name_records=[
                {"metric_id": target, "business_name": "Friendly Name",
                 "source": "pbi_report", "report_name": "Ops_Dashboard",
                 "report_url": "https://app.powerbi.com/links/x"},
            ],
        )
        assert out.business_names_applied == 1

        from src.steps.export import export_step
        from src.steps.metric_logic import metric_logic_step

        logic_rows = metric_logic_step(out.nodes_rows, out.edges_rows)
        by_id = {r["metric_id"]: r for r in logic_rows}
        assert by_id[target]["business_name"] == "Friendly Name"
        assert by_id[target]["report_name"] == "Ops_Dashboard"
        assert by_id[target]["report_url"] == "https://app.powerbi.com/links/x"
        assert all(r["business_name"] is None for m, r in by_id.items() if m != target)

        tables = export_step(out.nodes_rows, out.edges_rows)
        canonical = {r["metricId"]: r for r in tables["graph_canonical"]}
        assert canonical[target]["businessName"] == "Friendly Name"
        assert canonical[target]["reportUrl"] == "https://app.powerbi.com/links/x"

    def test_local_retrieval_matches_business_name(self):
        from src.agent_backend import retrieve_metric_rows
        rows = [
            {"metric_id": "reporting.USP_X1", "metric_name": "USP_X1",
             "business_name": "Door To Needle Time", "source_tables": ""},
            {"metric_id": "reporting.USP_X2", "metric_name": "USP_X2",
             "business_name": None, "source_tables": ""},
        ]
        hits = retrieve_metric_rows("what is our door to needle time?", rows)
        assert [h["metric_id"] for h in hits] == ["reporting.USP_X1"]


class TestPbixEmission:
    def test_friendly_name_from_report(self):
        assert friendly_name_from_report("IP_Sepsis-Compliance_Dashboard") == \
            "IP Sepsis Compliance Dashboard"

    def test_one_record_per_source_first_report_wins(self):
        results = [
            {"report_name": "Sepsis_Dashboard", "sql_source": "EXEC USP_A"},
            {"report_name": "Ops_Review", "sql_source": "EXEC USP_A"},
            {"report_name": "Ops_Review", "sql_source": "FROM reporting.V_B"},
            {"report_name": "NoSource", "sql_source": None},
            {"report_name": "RawSql", "sql_source": "SQL: SELECT * FROM x JOIN y"},
        ]
        records = build_metric_name_records(results)
        assert len(records) == 2  # raw-SQL fragment skipped, not guessed
        a = next(r for r in records if r["metric_id"] == "USP_A")
        assert a["business_name"] == "Sepsis Dashboard"
        assert a["report_name"] == "Sepsis_Dashboard; Ops_Review"
        assert a["source"] == "pbi_report"
        assert any(r["metric_id"] == "reporting.V_B" for r in records)
