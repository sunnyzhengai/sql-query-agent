"""Live evaluation of the ADR 0035 agent — real Azure OpenAI (function
calling), real Eventhouse, multi-turn conversations.

Runs a fixed set of conversations covering the verb-scorecard questions,
follow-ups, anaphora, and refusals; records every turn (question,
answer, code-stamped basis, tool trace, latency) to markdown + JSONL
for human review. This measures the CONVERSATION (ADR 0035: you test
code, you measure models).

Run:  python3 devtools/agent_live_eval.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from devtools.grounding_evals import _load_dotenv  # noqa: E402
from src.orchestrator.agent import azure_chat_api, run_turn  # noqa: E402
from src.orchestrator.kusto import (  # noqa: E402
    KustoClient,
    az_cli_token_provider,
)
from src.orchestrator.tools import Session  # noqa: E402

QUERY_URI = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
DATABASE = "probe-eh"

# Each conversation: (id, expectation note, [turn, turn, ...])
CONVERSATIONS = [
    ("definition_and_followups",
     "definition answer grounded in facts; follow-ups use context, no re-search noise",
     ["how is ED sepsis screening calculated?",
      "show me its sql",
      "who owns it?",
      "what tables does it read from?"]),
    ("same_logic_q2",
     "computed verdict via check_same_logic, never an LLM impression",
     ["does ED Sepsis Screening use the same logic as ED Sepsis (Regulatory)?"]),
    ("variants_family",
     "find_by_name family -> check_same_logic partition (6 procs, 5 distinct)",
     ["are all definitions of Base_Pop_Severe_ED_Scores the same across our procedures?"]),
    ("pairwise_variant",
     "two named procs, one named step -> partition slice",
     ["is reporting.USP_ED_Sepsis using the same Base_Pop_Severe_ED_Scores "
      "logic as reports.USP_IP_SEPSIS?"]),
    ("same_developer_q3",
     "LLM assembles from two fact sets; honest about unrecorded ownership",
     ["were ED Sepsis Screening and ED Sepsis (Regulatory) written by the "
      "same developer?"]),
    ("shared_tables_q4",
     "LLM intersects two source_tables lists from facts",
     ["what tables do ED Sepsis Screening and ED Sepsis (Regulatory) share?"]),
    ("ambiguity_disclosure",
     "several sepsis metrics exist — must ask or state assumption, never silent",
     ["how is sepsis defined?"]),
    ("anaphora_compare",
     "'this' binds to prior answer via conversation context",
     ["how is ED Sepsis Screening calculated?",
      "how is this different from the inpatient sepsis overview?"]),
    ("lineage_refusal_q6",
     "no lineage tool exists — honest refusal, no fabricated downstream list",
     ["which metrics are downstream of the ADT table?"]),
    ("data_values_refusal",
     "definitions only — refuse actual patient counts",
     ["how many sepsis patients did we have yesterday?"]),
    ("nonsense_refusal",
     "nothing related — honest refusal",
     ["what is the average unicorn velocity for readmitted patients?"]),
    ("smalltalk",
     "no tools, no fabricated basis",
     ["hello, what can you do?"]),
]


def main() -> None:
    _load_dotenv()
    client = KustoClient(QUERY_URI, DATABASE,
                         az_cli_token_provider(QUERY_URI))
    chat_api = azure_chat_api()

    out_md = Path("docs/internal/AGENT_LIVE_RESULTS.md")
    out_jsonl = Path("docs/internal/agent_live_results.jsonl")
    md = ["# ADR 0035 Agent — Live Evaluation",
          "",
          f"Model: env SQA_LLM_MODEL | Eventhouse: {DATABASE} | "
          "multi-turn, real function calling.",
          ""]
    records = []

    for conv_id, expectation, turns in CONVERSATIONS:
        print(f"=== {conv_id}")
        history: "list[dict]" = []
        session = Session()
        md += [f"## {conv_id}", "", f"*Expectation:* {expectation}", ""]
        for question in turns:
            t0 = time.time()
            try:
                turn = run_turn(history, question, chat_api, client.run,
                                session)
                answer, basis, trace = turn.answer, turn.basis, turn.trace
            except Exception as e:                     # noqa: BLE001
                answer, basis, trace = f"(EXCEPTION: {e})", "-", []
            latency = time.time() - t0
            tools_line = " -> ".join(
                t["tool"] + ("(ERR)" if "error" in t["result"] else "")
                for t in trace) or "(none)"
            print(f"  you> {question}")
            print(f"  [{latency:.1f}s | tools: {tools_line}]")
            md += [f"**you>** {question}", "",
                   answer, "",
                   f"`Basis: {basis}`", "",
                   f"*({latency:.1f}s; tools: {tools_line})*", ""]
            records.append({
                "conversation": conv_id, "question": question,
                "answer": answer, "basis": basis,
                "tools": [t["tool"] for t in trace],
                "latency_s": round(latency, 2),
            })
        md.append("")

    out_md.write_text("\n".join(md))
    out_jsonl.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    print(f"\nwrote {out_md} and {out_jsonl}")


if __name__ == "__main__":
    main()
