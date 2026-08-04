"""Ask the local agent stand-in a question — your certified data, your laptop.

Usage:
    python devtools/ask.py "How is the metric reporting.USP_IP_SepsisDates calculated?"
    python devtools/ask.py --sample "What tables does dbo.ER_LOS use?"

Grounded exactly like the Data Agent: retrieves matching metric_logic rows
from the recorded fixtures and answers ONLY from them (refuses beyond them).
Live LLM call — needs OPENAI_API_KEY in .env; costs fractions of a cent.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.grounding_evals import _load_metric_rows  # noqa: E402  (loads .env)
from src.agent_backend import retrieve_metric_rows  # noqa: E402


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print('Usage: python devtools/ask.py "your question about a metric"')
        raise SystemExit(1)
    question = " ".join(args)

    metric_rows = _load_metric_rows()
    grounded_in = retrieve_metric_rows(question, metric_rows)

    from devtools.local_llm import LocalLLMBackend

    backend = LocalLLMBackend(metric_rows)
    answer = backend.answer(question)

    print(f"\nQ: {question}\n")
    print(answer)
    if grounded_in:
        print(f"\n[grounded in: {', '.join(r['metric_id'] for r in grounded_in)}]")
    else:
        print("\n[no certified metric matched this question]")


if __name__ == "__main__":
    main()
