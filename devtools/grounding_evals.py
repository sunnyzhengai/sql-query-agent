"""Grounding evals — the flow contract for the agent, executable.

The agent's contract (ADR 0005): answers come ONLY from the certified
tables; beyond them it refuses. This harness turns that into scored cases
generated from the data itself:

  retrieval cases - one per metric: "How is X calculated?" must mention
                    the metric's own source tables (grounded), and
  refusal cases   - fabricated metrics: the agent must refuse, not invent.

Runs against ANY AgentBackend — Fabric agent, local LLM stand-in, or a
replay cassette (deterministic, free, CI-friendly).

Usage:
  python devtools/grounding_evals.py                 # recorded fixtures + local LLM
  python devtools/grounding_evals.py --sample        # bundled sample corpus
  python devtools/grounding_evals.py --record        # record cassette while running live
  python devtools/grounding_evals.py --replay        # cassette only, no API calls
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _load_dotenv() -> None:
    """Load KEY=VALUE lines from the repo-root .env (gitignored) into the
    environment, without overriding anything already set."""
    import os

    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

from src.agent_backend import AgentBackend, ReplayBackend, is_refusal  # noqa: E402
from src.parser.identity import fold_identifier  # noqa: E402

CASSETTE = PROJECT_ROOT / "tests" / "fixtures" / "agent_cassette.jsonl"

REFUSAL_PROBES = [
    "How is the metric FAKE_METRIC_THAT_DOES_NOT_EXIST calculated?",
    "What is the average unicorn readmission velocity?",
]


@dataclass
class EvalCase:
    kind: str                 # "retrieval" | "refusal"
    question: str
    must_mention: "list[str]"  # folded terms the answer must contain (retrieval)


@dataclass
class EvalResult:
    case: EvalCase
    answer: str
    passed: bool
    reason: str


def build_eval_cases(metric_rows: "list[dict[str, Any]]", max_retrieval: int = 10) -> "list[EvalCase]":
    cases = []
    for row in metric_rows[:max_retrieval]:
        tables = [t.strip() for t in (row.get("source_tables") or "").split(",") if t.strip()]
        if not tables:
            continue
        cases.append(EvalCase(
            kind="retrieval",
            question=f"How is the metric {row['metric_id']} calculated, and which tables does it use?",
            must_mention=[fold_identifier(tables[0])],
        ))
    for probe in REFUSAL_PROBES:
        cases.append(EvalCase(kind="refusal", question=probe, must_mention=[]))
    return cases


def run_evals(backend: AgentBackend, cases: "list[EvalCase]") -> "list[EvalResult]":
    results = []
    for case in cases:
        answer = backend.answer(case.question)
        folded_answer = fold_identifier(answer)

        if case.kind == "refusal":
            passed = is_refusal(answer)
            reason = "refused as required" if passed else "INVENTED an answer for a fake metric"
        else:
            missing = [t for t in case.must_mention if t not in folded_answer]
            hallucinated_refusal = is_refusal(answer)
            passed = not missing and not hallucinated_refusal
            if hallucinated_refusal:
                reason = "refused a question the certified data CAN answer"
            elif missing:
                reason = f"answer does not mention required source table(s): {missing}"
            else:
                reason = "grounded"
        results.append(EvalResult(case, answer, passed, reason))
    return results


def print_report(results: "list[EvalResult]") -> bool:
    passed = sum(1 for r in results if r.passed)
    print(f"\nGROUNDING EVALS: {passed}/{len(results)} passed")
    for r in results:
        symbol = "+" if r.passed else "X"
        print(f"  [{symbol}] ({r.case.kind}) {r.case.question[:70]}")
        if not r.passed:
            print(f"        {r.reason}")
            print(f"        answer: {r.answer[:120]}...")
    return passed == len(results)


def _load_metric_rows() -> "list[dict[str, Any]]":
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_pipeline_local", PROJECT_ROOT / "scripts" / "run_pipeline_local.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    if "--sample" in sys.argv:
        parse_results, tables, columns = runner.load_sample()
    else:
        parse_results, tables, columns = runner.load_recorded()

    from src.steps.build_graph import build_graph_step
    from src.steps.metric_logic import metric_logic_step

    graph = build_graph_step(parse_results, tables, columns)
    return metric_logic_step(graph.nodes_rows, graph.edges_rows)


def main() -> None:
    metric_rows = _load_metric_rows()
    cases = build_eval_cases(metric_rows)
    print(f"Metrics: {len(metric_rows)}  Eval cases: {len(cases)} "
          f"({sum(1 for c in cases if c.kind == 'retrieval')} retrieval, "
          f"{sum(1 for c in cases if c.kind == 'refusal')} refusal)")

    if "--replay" in sys.argv:
        backend: AgentBackend = ReplayBackend(CASSETTE, mode="replay")
    else:
        from devtools.local_llm import LocalLLMBackend

        live = LocalLLMBackend(metric_rows)
        backend = (
            ReplayBackend(CASSETTE, backend=live, mode="auto")
            if "--record" in sys.argv else live
        )

    ok = print_report(run_evals(backend, cases))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
