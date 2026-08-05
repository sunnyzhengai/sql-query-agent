"""Ask the local GRAPH agent a question — resolve-then-traverse on your laptop.

Usage:
    python devtools/ask_graph.py "Which metrics read from the HOSPITAL_ENCOUNTERS table?"
    python devtools/ask_graph.py "How is reports.USP_Severe_Sepsis calculated?"

Resolution is one live LLM call (OPENAI_API_KEY in .env); traversal is
deterministic; the Basis line is computed by code from what actually ran.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.grounding_evals import _load_dotenv  # noqa: E402
from devtools.graph_agent import LocalGraphAgent  # noqa: E402
from devtools.local_llm import chat_completion  # noqa: E402
from src.graph.templates import GraphView  # noqa: E402
from src.steps.build_graph import build_graph_step  # noqa: E402
from src.steps.export import export_step  # noqa: E402

FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "recorded"


def _build_view() -> GraphView:
    spec = importlib.util.spec_from_file_location(
        "run_pipeline_local", PROJECT_ROOT / "scripts" / "run_pipeline_local.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    parse_results, tables, columns = mod.load_recorded(FIXTURES)
    graph = build_graph_step(parse_results, tables, columns)
    return GraphView(export_step(graph.nodes_rows, graph.edges_rows))


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print('Usage: python devtools/ask_graph.py "your question"')
        raise SystemExit(1)
    question = " ".join(args)

    _load_dotenv()
    agent = LocalGraphAgent(_build_view(), chat_completion)
    result = agent.answer(question)

    print(f"\nQ: {question}\n")
    print(result["text"])
    print(f"\n{result['basis']}")
    print(f"[plan: {result['plan'].get('intent')} | {result['plan'].get('note', '')}]")


if __name__ == "__main__":
    main()
