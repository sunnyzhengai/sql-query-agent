"""Journey tables: metric-grain + report-grain, reconciliation-pinned.

The accuracy contract (HANDOFF_ADMIN_JOURNEY_DASHBOARD decision 4):
columns are joins over contract tables only, and the totals must
reconcile per stage — the dashboard cannot drift from the record.
"""

from src.governance.journey import metric_journey_rows, report_journey_rows

SOURCES = [
    {"metric_id": "rpt.USP_A", "source_type": "procedure", "source_schema": "rpt"},
    {"metric_id": "rpt.USP_B", "source_type": "procedure", "source_schema": "rpt"},
    {"metric_id": "etl.V_C", "source_type": "view", "source_schema": "etl"},
]
VALIDATION = [
    {"metric_id": "rpt.USP_A", "step2_parsed": True, "step3_canonical": True},
    {"metric_id": "rpt.USP_B", "step2_parsed": True, "step3_canonical": True},
    {"metric_id": "etl.V_C", "step2_parsed": False, "step3_canonical": False},
]
ERRORS = [{"metric_id": "etl.V_C", "error_category": "dynamic_sql"}]
CARDS = [
    {"metric_id": "rpt.USP_A", "calculation_logic": "step1..."},
    {"metric_id": "rpt.USP_B", "calculation_logic": "step1..."},
]
DESCRIPTIONS = [
    {"metric_name": "rpt.USP_A", "status": "ok"},
    {"metric_name": "rpt.USP_B", "status": "rejected"},
]
REPORT_SOURCES = [
    {"report_name": "ED Dashboard", "schema_name": "rpt", "sql_object": "USP_A",
     "workspace_name": "Clinical Analytics"},
    {"report_name": "ED Dashboard", "schema_name": "rpt", "sql_object": "USP_B",
     "workspace_name": "Clinical Analytics"},
    {"report_name": "Exec Overview", "schema_name": "rpt", "sql_object": "USP_A",
     "workspace_name": "Leadership"},
]
PUBLISH_LOG = [
    {"target": "collibra", "status": "success", "asset_id": "rpt.USP_A", "name": ""},
    {"target": "fabric_pbi", "status": "failed", "asset_id": "rpt.USP_A", "name": ""},
]


def _rows():
    return metric_journey_rows(
        "t0", SOURCES, VALIDATION, ERRORS, CARDS, DESCRIPTIONS,
        REPORT_SOURCES, PUBLISH_LOG)


class TestMetricJourney:
    def test_one_row_per_metric_always(self):
        rows = _rows()
        assert len(rows) == 3
        # USP_A feeds TWO reports -> one row, count 2 (grain rule)
        a = next(r for r in rows if r["metric_id"] == "rpt.USP_A")
        assert a["report_count"] == 2
        assert a["report_names"] == "ED Dashboard; Exec Overview"

    def test_reconciliation_loaded_equals_parsed_plus_errored(self):
        rows = _rows()
        loaded = sum(1 for r in rows if r["loaded"])
        parsed = sum(1 for r in rows if r["parsed"])
        errored = sum(1 for r in rows if r["error_type"])
        assert loaded == parsed + errored == 3

    def test_stage_columns_read_left_to_right(self):
        a = next(r for r in _rows() if r["metric_id"] == "rpt.USP_A")
        assert (a["loaded"], a["parsed"], a["in_graph"], a["card"]) == \
            (True, True, True, True)
        assert a["described_status"] == "ok"
        c = next(r for r in _rows() if r["metric_id"] == "etl.V_C")
        assert c["parsed"] is False and c["error_type"] == "dynamic_sql"
        assert c["card"] is False and c["described_status"] is None

    def test_unified_error_vocabulary_for_rejections(self):
        b = next(r for r in _rows() if r["metric_id"] == "rpt.USP_B")
        assert b["described_status"] == "rejected_by_agent"  # funnel's code

    def test_publish_flags_success_only(self):
        a = next(r for r in _rows() if r["metric_id"] == "rpt.USP_A")
        assert a["published_collibra"] is True
        assert a["published_pbi_writeback"] is False  # failed != published


class TestReportJourney:
    def test_report_grain_with_proc_list(self):
        rows = report_journey_rows("t0", REPORT_SOURCES,
                                   corpus_metric_ids={"rpt.USP_A", "rpt.USP_B"})
        assert len(rows) == 2
        ed = next(r for r in rows if r["report_name"] == "ED Dashboard")
        assert ed["proc_count"] == 2
        assert ed["proc_names"] == "rpt.USP_A; rpt.USP_B"
        assert ed["workspace_name"] == "Clinical Analytics"
        assert ed["tie_kind"] == "lineage_in_corpus"

    def test_outside_corpus_tie_is_named(self):
        rows = report_journey_rows(
            "t0",
            [{"report_name": "Lake Report", "schema_name": "dbo",
              "sql_object": "some_table", "workspace_name": "W"}],
            corpus_metric_ids={"rpt.USP_A"})
        assert rows[0]["tie_kind"] == "lineage_outside_corpus"
