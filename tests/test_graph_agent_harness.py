"""Harness tests for the local graph agent (scripted resolver, no LLM).

Validates the deterministic half of resolve-then-traverse: intent dispatch,
multi-anchor ambiguity handling, refusal, and the honest-by-construction
Basis footer. Resolution quality itself is exercised live via
devtools/ask_graph.py (needs a key), not in CI.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from devtools.graph_agent import LocalGraphAgent

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


def scripted(plan: dict):
    return lambda system, user: json.dumps(plan)


def test_reverse_lookup_answers_the_headline_question(view):
    agent = LocalGraphAgent(view, scripted({
        "intent": "metrics_of_table",
        "anchors": [{"type": "table", "key": "HOSPITAL_ENCOUNTERS"}],
    }))
    result = agent.answer("Which metrics read from the HOSPITAL_ENCOUNTERS table?")
    assert "13 metrics read HOSPITAL_ENCOUNTERS" in result["text"]
    assert result["basis"] == "Basis: metrics_of_table('HOSPITAL_ENCOUNTERS') -> 13 rows"


def test_ambiguous_bare_name_answers_for_both_schemas(view):
    agent = LocalGraphAgent(view, scripted({
        "intent": "tables_of_metric",
        "anchors": [
            {"type": "metric", "key": "reports.USP_ED_Sepsis"},
            {"type": "metric", "key": "reporting.USP_ED_Sepsis"},
        ],
    }))
    result = agent.answer("Which tables does USP_ED_Sepsis use?")
    assert "matched 2 certified items" in result["text"]
    assert "uses 29 tables" in result["text"]
    assert "uses 38 tables" in result["text"]


def test_explain_metric_walks_closure_not_roots(view):
    agent = LocalGraphAgent(view, scripted({
        "intent": "explain_metric",
        "anchors": [{"type": "metric", "key": "reports.USP_Severe_Sepsis"}],
    }))
    result = agent.answer("How is reports.USP_Severe_Sepsis calculated?")
    assert "32 tables" in result["text"]  # the shallow pattern found 0
    assert "steps_of_metric" in result["basis"]


def test_refusal_when_resolution_finds_nothing(view):
    agent = LocalGraphAgent(view, scripted({"intent": "refuse", "anchors": []}))
    result = agent.answer("What is the average unicorn readmission velocity?")
    assert result["text"] == "I don't have that in the certified knowledge base."
    assert "0 anchors" in result["basis"]


def test_basis_reports_zero_rows_honestly(view):
    agent = LocalGraphAgent(view, scripted({
        "intent": "metrics_of_table",
        "anchors": [{"type": "table", "key": "NO_SUCH_TABLE"}],
    }))
    result = agent.answer("Which metrics read NO_SUCH_TABLE?")
    assert "nothing found" in result["text"]
    assert "-> 0 rows" in result["basis"]
