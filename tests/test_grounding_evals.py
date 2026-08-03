"""Tests for the grounding-eval harness (the agent's executable flow contract)."""

from pathlib import Path

import pytest

from devtools.grounding_evals import EvalCase, build_eval_cases, run_evals
from src.agent_backend import ReplayBackend

REPO_ROOT = Path(__file__).resolve().parent.parent

ROWS = [
    {"metric_id": "reporting.USP_ED_SEPSIS", "metric_name": "USP_ED_SEPSIS",
     "calculation_logic": "logic", "source_tables": "encounter, department",
     "table_descriptions": "d"},
]


class GroundedBackend:
    def answer(self, question):
        if "FAKE_METRIC" in question or "unicorn" in question:
            return "I don't have that information in the certified knowledge base."
        return "USP_ED_SEPSIS reads the ENCOUNTER and DEPARTMENT tables."

    def describe_metric(self, row):
        return "desc"


class HallucinatingBackend:
    def answer(self, question):
        return "It is calculated from the QUANTUM_FLUX table using warp math."

    def describe_metric(self, row):
        return "desc"


class OverRefusingBackend:
    def answer(self, question):
        return "I couldn't find anything about that."

    def describe_metric(self, row):
        return "desc"


def test_cases_are_generated_from_the_data():
    cases = build_eval_cases(ROWS)
    kinds = [c.kind for c in cases]
    assert kinds.count("retrieval") == 1 and kinds.count("refusal") == 2
    assert cases[0].must_mention == ["ENCOUNTER"]


def test_grounded_backend_passes_everything():
    results = run_evals(GroundedBackend(), build_eval_cases(ROWS))
    assert all(r.passed for r in results)


def test_hallucination_fails_both_ways():
    results = run_evals(HallucinatingBackend(), build_eval_cases(ROWS))
    retrieval = [r for r in results if r.case.kind == "retrieval"]
    refusal = [r for r in results if r.case.kind == "refusal"]
    assert all(not r.passed for r in retrieval)  # wrong tables mentioned
    assert all(not r.passed for r in refusal)    # invented answer for fake metric


def test_over_refusal_fails_retrieval_cases():
    results = run_evals(OverRefusingBackend(), build_eval_cases(ROWS))
    retrieval = [r for r in results if r.case.kind == "retrieval"]
    assert all(not r.passed for r in retrieval)
    assert all("refused a question" in r.reason for r in retrieval)


CASSETTE = REPO_ROOT / "tests" / "fixtures" / "agent_cassette.jsonl"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "recorded"


@pytest.mark.skipif(
    not CASSETTE.exists() or not (FIXTURES / "parse_results.json").exists(),
    reason="no recorded agent cassette/fixtures yet",
)
def test_recorded_agent_passes_grounding_evals():
    """CI replay: the recorded agent conversation must satisfy the contract."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_pipeline_local", REPO_ROOT / "scripts" / "run_pipeline_local.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    from src.steps.build_graph import build_graph_step
    from src.steps.metric_logic import metric_logic_step

    parse_results, tables, columns = runner.load_recorded()
    graph = build_graph_step(parse_results, tables, columns)
    metric_rows = metric_logic_step(graph.nodes_rows, graph.edges_rows)

    results = run_evals(ReplayBackend(CASSETTE, mode="replay"),
                        build_eval_cases(metric_rows))
    failed = [r for r in results if not r.passed]
    assert not failed, f"{len(failed)} eval failures: {[r.reason for r in failed]}"
