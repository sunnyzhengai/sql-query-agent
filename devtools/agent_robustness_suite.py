"""Agent-level robustness suite (ADR 0035: you test code, you MEASURE
models) — the readiness gate's successor measurement.

Canonical conversations x LLM paraphrases, run LIVE, graded
MECHANICALLY from the code-stamped trace wherever possible:

  right_tool   the trace contains the call the question class demands
               (same-logic questions MUST hit check_same_logic; family
               questions MUST gather via find_by_name; refusals MUST
               NOT read facts)
  grounded     every metric/step id the ANSWER mentions appears in a
               tool result of the conversation (no unsourced ids)
  latency      per turn

Only prose faithfulness is left un-graded here (LLM-judge later if
needed). Gate thresholds set from this baseline.

Run:  python3 devtools/agent_robustness_suite.py [--variants N]
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from devtools.grounding_evals import _load_dotenv  # noqa: E402
from devtools.local_llm import chat_completion  # noqa: E402
from src.orchestrator.agent import azure_chat_api, run_turn  # noqa: E402
from src.orchestrator.kusto import (  # noqa: E402
    KustoClient,
    az_cli_token_provider,
)
from src.orchestrator.tools import Session  # noqa: E402

QUERY_URI = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
DATABASE = "probe-eh"

PARAPHRASE_PROMPT = (
    "Rewrite the question below in {n} genuinely different ways a "
    "business analyst might phrase it. Keep the MEANING identical — "
    "same subjects, same ask. One per line, no numbering.\n\n{q}"
)

_ID_PATTERN = re.compile(
    r"\b(?:transform:[\w.]+:[\w]+|(?:reporting|reports)\.[\w]+)\b")

# Graders take (turns: list[Turn]) and return True/False.


def used_tool(name, min_ids=0):
    def grade(turns):
        for t in turns:
            for call in t.trace:
                if call["tool"] == name and "error" not in call["result"]:
                    if min_ids and len(call["args"].get("ids", [])) < min_ids:
                        continue
                    return True
        return False
    return grade


def read_no_facts(turns):
    """Refusal honesty: the conversation never read or verified items
    (search alone is fine — looking before refusing is good)."""
    for t in turns:
        for call in t.trace:
            if call["tool"] in ("get_facts", "list_steps",
                                "check_same_logic"):
                return False
    return True


def searched_before_answering(turns):
    return any(call["tool"] in ("search_catalog", "find_by_name")
               for t in turns for call in t.trace)


def grounded(turns):
    """Every id the answers mention appears in some tool result."""
    corpus = json.dumps([c["result"] for t in turns for c in t.trace])
    for t in turns:
        for mentioned in _ID_PATTERN.findall(t.answer):
            if mentioned not in corpus:
                return False
    return True


CANONICALS = [
    {"id": "definition", "graders": {"grounded": grounded,
                                     "searched": searched_before_answering},
     "turns": ["how is ED sepsis screening calculated?"]},
    {"id": "followup_sql", "graders": {"grounded": grounded},
     "turns": ["how is ED sepsis screening calculated?",
               "show me its sql"]},
    {"id": "same_logic", "graders": {
        "right_tool": used_tool("check_same_logic", min_ids=2),
        "grounded": grounded},
     "turns": ["does ED Sepsis Screening use the same logic as "
               "ED Sepsis (Regulatory)?"]},
    {"id": "variants_family", "graders": {
        "family_gathered": used_tool("find_by_name"),
        "right_tool": used_tool("check_same_logic", min_ids=2),
        "grounded": grounded},
     "turns": ["are all definitions of Base_Pop_Severe_ED_Scores the "
               "same across our procedures?"]},
    {"id": "pairwise_step", "graders": {
        "right_tool": used_tool("check_same_logic", min_ids=2),
        "grounded": grounded},
     "turns": ["is reporting.USP_ED_Sepsis using the same "
               "Base_Pop_Severe_ED_Scores logic as reports.USP_IP_SEPSIS?"]},
    {"id": "shared_tables", "graders": {"grounded": grounded},
     "turns": ["what tables do ED Sepsis Screening and "
               "ED Sepsis (Regulatory) share?"]},
    {"id": "concept_plurality", "graders": {
        "searched": searched_before_answering, "grounded": grounded},
     "turns": ["how is sepsis defined?"]},
    {"id": "uniqueness_verified", "graders": {
        "right_tool": used_tool("check_same_logic", min_ids=2),
        "grounded": grounded},
     "turns": ["how is ED sepsis defined?",
               "is there another metric that uses this definition?"]},
    {"id": "lineage_refusal", "graders": {"honest": read_no_facts},
     "turns": ["which metrics are downstream of the ADT table?"]},
    {"id": "data_values_refusal", "graders": {"honest": read_no_facts},
     "turns": ["how many sepsis patients did we have yesterday?"]},
]


def paraphrase(question, n):
    raw = chat_completion(
        "You rewrite questions faithfully.",
        PARAPHRASE_PROMPT.format(n=n, q=question))
    return [v.strip() for v in raw.splitlines() if v.strip()][:n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", type=int, default=5)
    args = ap.parse_args()
    _load_dotenv()
    client = KustoClient(QUERY_URI, DATABASE,
                         az_cli_token_provider(QUERY_URI))
    chat_api = azure_chat_api()

    report = {"canonicals": [], "totals": {}}
    latencies, all_checks = [], []

    for spec in CANONICALS:
        first = spec["turns"][0]
        variants = [first] + paraphrase(first, args.variants)
        runs = []
        for vi, opening in enumerate(variants):
            history, session, turns = [], Session(), []
            questions = [opening] + spec["turns"][1:]
            for q in questions:
                t0 = time.time()
                turns.append(run_turn(history, q, chat_api, client.run,
                                      session))
                latencies.append(time.time() - t0)
            checks = {name: g(turns) for name, g in spec["graders"].items()}
            all_checks.extend(checks.values())
            runs.append({
                "variant": vi, "opening": opening, "checks": checks,
                "answers": [t.answer for t in turns],
                "bases": [t.basis for t in turns],
            })
            flags = " ".join(f"{k}={'Y' if v else 'N'}"
                             for k, v in checks.items())
            print(f"[{spec['id']}] v{vi} {flags}")
        per_grader = {
            name: sum(r["checks"][name] for r in runs) / len(runs)
            for name in spec["graders"]}
        report["canonicals"].append({
            "id": spec["id"], "pass_rates": per_grader, "runs": runs})

    report["totals"] = {
        "conversations_run": sum(len(c["runs"]) for c in report["canonicals"]),
        "all_checks_pass_rate": round(
            sum(all_checks) / len(all_checks), 3) if all_checks else None,
        "latency_p50_s": round(statistics.median(latencies), 2),
        "latency_max_s": round(max(latencies), 2),
    }
    out = Path("internal/docs/agent_robustness_baseline.json")
    out.write_text(json.dumps(report, indent=1))
    print("\n=== TOTALS ===")
    for k, v in report["totals"].items():
        print(f"  {k}: {v}")
    for c in report["canonicals"]:
        rates = ", ".join(f"{k} {v:.0%}" for k, v in c["pass_rates"].items())
        print(f"  {c['id']}: {rates}")
    print(f"\nreport -> {out}")


if __name__ == "__main__":
    main()
