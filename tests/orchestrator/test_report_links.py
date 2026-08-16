"""Consumption-layer tools (ADR 0040): list_report_links + report/measure
facts. Same discipline as the rest of the toolset: fixed queries, session
gating (no unsurfaced facts), deterministic links only."""

from __future__ import annotations

import json

import pytest

from src.orchestrator.assemble import NODE_FACTS_QUERY
from src.orchestrator.tools import (
    LINKS_OF_REPORT_QUERY,
    REPORTS_OF_METRIC_QUERY,
    Session,
    ToolError,
    get_facts,
    list_report_links,
)

REF = "reporting.USP_IP_SepsisDates"
REPORT_ID = "report:SEPSIS COMPLIANCE DASHBOARD"
MEASURE_ID = "measure:SEPSIS COMPLIANCE DASHBOARD:SEPSISDATA[Compliance Rate]"


def fake_kql(query, params):
    if query == REPORTS_OF_METRIC_QUERY:
        if params["p_id"] == f"canonical:{REF}":
            return [{"node_id": REPORT_ID, "name": "Sepsis Compliance Dashboard",
                     "description": "Tracks screening compliance."}]
        return []
    if query == LINKS_OF_REPORT_QUERY:
        if params["p_id"] == REPORT_ID:
            return [
                {"edge_type": "report_to_canonical",
                 "node_id": f"canonical:{REF}", "name": "USP_IP_SepsisDates"},
                {"edge_type": "report_to_measure",
                 "node_id": MEASURE_ID, "name": "Compliance Rate"},
                {"edge_type": "report_to_technical",
                 "node_id": "tech:DBO.ENCOUNTER", "name": "encounter"},
            ]
        return []
    if query == NODE_FACTS_QUERY:
        node_id = params["p_node_id"]
        if node_id == REPORT_ID:
            return [{"node_id": node_id, "name": "Sepsis Compliance Dashboard",
                     "description": "Tracks screening compliance.",
                     "properties": json.dumps({
                         "repo_name": "BI-Reports",
                         "semantic_model_path": "x.SemanticModel"})}]
        if node_id == MEASURE_ID:
            return [{"node_id": node_id, "name": "Compliance Rate",
                     "description": "Share of encounters compliant.",
                     "properties": json.dumps({
                         "dax_expression": "DIVIDE([a],[b])",
                         "expression_type": "measure",
                         "report_name": "Sepsis Compliance Dashboard",
                         "pbi_table": "SepsisData"})}]
        return []
    raise AssertionError(f"unexpected query: {query[:60]}")


def _session_with(*ids):
    s = Session()
    s.allow(ids)
    return s


def test_reports_of_metric():
    out = list_report_links(REF, fake_kql, _session_with(REF))
    assert out["count"] == 1
    assert out["reports"][0]["name"] == "Sepsis Compliance Dashboard"


def test_links_of_report_bucketed_by_edge_type():
    out = list_report_links(REPORT_ID, fake_kql, _session_with(REPORT_ID))
    assert [m["id"] for m in out["executes_metrics"]] == [REF]
    assert [m["name"] for m in out["measures"]] == ["Compliance Rate"]
    assert [t["id"] for t in out["reads_tables"]] == ["tech:DBO.ENCOUNTER"]


def test_unsurfaced_id_is_refused():
    with pytest.raises(ToolError):
        list_report_links(REF, fake_kql, Session())


def test_links_surface_ids_for_followup_reads():
    session = _session_with(REPORT_ID)
    list_report_links(REPORT_ID, fake_kql, session)
    # the surfaced measure id is now readable
    facts = get_facts(MEASURE_ID, fake_kql, session)
    assert facts["kind"] == "measure"
    assert facts["facts"]["dax_expression"] == "DIVIDE([a],[b])"
    assert "graph_nodes" in facts["basis"]


def test_report_facts_assembled():
    facts = get_facts(REPORT_ID, fake_kql, _session_with(REPORT_ID))
    assert facts["kind"] == "report"
    assert facts["facts"]["report_name"] == "Sepsis Compliance Dashboard"
    assert facts["facts"]["repo_name"] == "BI-Reports"


def test_empty_result_notes_absence_is_not_proof():
    out = list_report_links("reporting.USP_Other", fake_kql,
                            _session_with("reporting.USP_Other"))
    assert out["count"] == 0
    assert "not proof" in out["note"]
