"""Lineage-exact report matching + publish-log projection (ADR 0040).

The name-similarity matcher is gone; these tests pin the replacement:
a workspace report gets a description ONLY via report_to_canonical
lineage, and every ambiguous case is a skip with a reason.
"""

from __future__ import annotations

from src.adapters.base import PublishStatus
from src.adapters.fabric_pbi import (
    BulkUpdateResult,
    PBIReport,
    UpdateResult,
    match_reports_by_lineage,
    to_publish_results,
)

NODES = [
    {"node_id": "report:SEPSIS COMPLIANCE DASHBOARD", "layer": "report",
     "name": "Sepsis Compliance Dashboard"},
    {"node_id": "report:SEPSIS OPS OVERVIEW", "layer": "report",
     "name": "Sepsis Ops Overview"},
    {"node_id": "canonical:reporting.USP_IP_SepsisDates", "layer": "canonical",
     "name": "USP_IP_SepsisDates", "description": "Tracks sepsis screening dates."},
    {"node_id": "canonical:reporting.USP_IP_SepsisDetails", "layer": "canonical",
     "name": "USP_IP_SepsisDetails", "description": "Details."},
]

EDGES = [
    {"source_id": "report:SEPSIS COMPLIANCE DASHBOARD",
     "target_id": "canonical:reporting.USP_IP_SepsisDates",
     "edge_type": "report_to_canonical"},
    # the overview report links to TWO metrics -> ambiguous, must skip
    {"source_id": "report:SEPSIS OPS OVERVIEW",
     "target_id": "canonical:reporting.USP_IP_SepsisDates",
     "edge_type": "report_to_canonical"},
    {"source_id": "report:SEPSIS OPS OVERVIEW",
     "target_id": "canonical:reporting.USP_IP_SepsisDetails",
     "edge_type": "report_to_canonical"},
]


def test_exact_lineage_match_publishes_metric_description():
    reports = [PBIReport(report_id="r1", name="Sepsis Compliance Dashboard")]
    updates, skipped = match_reports_by_lineage(reports, NODES, EDGES)
    assert len(updates) == 1 and not skipped
    assert updates[0]["description"] == "Tracks sepsis screening dates."
    assert updates[0]["matched_metric"] == "reporting.USP_IP_SepsisDates"


def test_multi_metric_report_is_skipped_not_guessed():
    reports = [PBIReport(report_id="r2", name="Sepsis Ops Overview")]
    updates, skipped = match_reports_by_lineage(reports, NODES, EDGES)
    assert updates == []
    assert len(skipped) == 1 and "2 metrics" in skipped[0]


def test_unknown_report_is_skipped_with_remediation():
    reports = [PBIReport(report_id="r3", name="Some Other Dashboard")]
    updates, skipped = match_reports_by_lineage(reports, NODES, EDGES)
    assert updates == []
    assert "run 12 first" in skipped[0]


def test_match_is_case_insensitive_but_exact():
    reports = [PBIReport(report_id="r1", name="SEPSIS COMPLIANCE DASHBOARD")]
    updates, _ = match_reports_by_lineage(reports, NODES, EDGES)
    assert len(updates) == 1
    # similarity is NOT enough
    reports = [PBIReport(report_id="r1", name="Sepsis Compliance")]
    updates, skipped = match_reports_by_lineage(reports, NODES, EDGES)
    assert updates == [] and skipped


def test_to_publish_results_projects_statuses():
    bulk = BulkUpdateResult()
    bulk.add(UpdateResult(report_id="a", report_name="A", status="success", message="ok"))
    bulk.add(UpdateResult(report_id="b", report_name="B", status="failed", message="HTTP 403"))
    results = to_publish_results(bulk)
    assert [r.status for r in results] == [PublishStatus.SUCCESS, PublishStatus.FAILED]
    assert results[0].asset_id == "a"
