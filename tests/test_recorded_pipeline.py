"""Replay recorded ScriptDom fixtures through the full offline pipeline.

Skips until fixtures are recorded (see tests/fixtures/recorded/README.md).
When present: re-verifies anonymization (defense in depth — the export
notebook already gated), then requires the pipeline to reach DEPLOYMENT
READY on production-parser truth.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from src.anonymization import get_scan_terms, load_crosswalk, scan_for_missed

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "recorded"
CROSSWALK = REPO_ROOT / "data" / "synthetic" / "crosswalk.json"

pytestmark = pytest.mark.skipif(
    not (FIXTURES / "parse_results.json").exists(),
    reason="no recorded fixtures yet — run the export notebook on Fabric",
)


def _runner():
    spec = importlib.util.spec_from_file_location(
        "run_pipeline_local", REPO_ROOT / "scripts" / "run_pipeline_local.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixtures_contain_no_proprietary_terms():
    terms = get_scan_terms(load_crosswalk(CROSSWALK))
    assert terms, "crosswalk must define _scan_terms"
    for fname in ("parse_results.json", "dict_tables.json", "dict_columns.json"):
        leaks = scan_for_missed((FIXTURES / fname).read_text(), terms)
        assert not leaks, f"{fname} leaked proprietary terms:\n" + "\n".join(leaks[:5])


def test_recorded_pipeline_reaches_deployment_ready():
    runner = _runner()
    parse_results, tables, columns = runner.load_recorded(FIXTURES)
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    assert len(parse_results) == manifest["parse_results"]

    blocked, lines = runner.run_pipeline(parse_results, tables, columns)
    report = "\n".join(lines)
    assert not blocked, f"recorded pipeline BLOCKED:\n{report}"


def _exported_from_recorded():
    from src.steps.build_graph import build_graph_step
    from src.steps.export import export_step

    runner = _runner()
    parse_results, tables, columns = runner.load_recorded(FIXTURES)
    graph = build_graph_step(parse_results, tables, columns)
    return export_step(graph.nodes_rows, graph.edges_rows)


def _table_node_ids(exported, table_name):
    return {
        r["nodeId"] for r in exported["graph_technical"]
        if r["tableName"].upper() == table_name and not r["columnName"]
    }


def test_uses_table_closure_matches_certified_answer_key():
    """Count oracle (ADR 0018): the derived closure must reproduce the
    REMATCH_SCORECARD answer-key numbers computed from these fixtures.
    A silent undercount here is the exact defect the closure exists to kill."""
    exported = _exported_from_recorded()
    uses = exported["graph_edge_uses_table"]

    def readers_of(table_name):
        targets = _table_node_ids(exported, table_name)
        assert targets, f"{table_name} table node missing from graph_technical"
        return {r["sourceId"] for r in uses if r["targetId"] in targets}

    assert len(readers_of("HOSPITAL_ENCOUNTERS")) == 13
    assert len(readers_of("MEDICATION_ORDERS")) == 7

    def tables_of(metric_id):
        return {
            r["targetId"] for r in uses
            if r["sourceId"] == f"canonical:{metric_id}"
        }

    assert len(tables_of("reports.USP_Severe_Sepsis")) == 32
    assert len(tables_of("reporting.USP_ED_Sepsis")) == 38
    assert len(tables_of("reports.USP_ED_Sepsis")) == 29

    # ADR 0020: CALCULATED_BY is the full step closure — the generator's
    # single-hop chain must see all 88 steps of Severe_Sepsis, not 1 root
    c2t = exported["graph_edge_c2t"]
    severe = "canonical:reports.USP_Severe_Sepsis"
    assert len({e["targetId"] for e in c2t if e["sourceId"] == severe}) == 88
