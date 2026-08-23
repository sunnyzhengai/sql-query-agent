"""Config verification for the Fabric lineage mitigation — NOT a rematch.

HANDOFF_FABRIC_LINEAGE_MITIGATION.md item 4: three fixed lineage
questions through the MCP adapter, N=3 runs each, checking that the
published SQL Intelligence Agent answers from the readers_of_table /
column_usage stored functions (parsed edges) instead of name
association. Round 4 stays closed (one-run protocol); this verifies
CONFIG, and its results append to the handoff file.

Oracles are derived live from the stored functions themselves — the
functions were verified against the homegrown op semantics first
(eventhouse_setup.kql section 4b probes), so their rows are the
store's truth. A run PASSES when every expected name is carried and
no cousin-family name is; the mitigation VERIFIES when all N runs of
every question pass (routing consistency is the point).

Usage: python3.11 devtools/verify_lineage_mitigation.py
Requires: az CLI logged in; capacity active; the agent REPUBLISHED
after the 2026-08-23 updateDefinition (MCP serves the published
version — draft-only state fails exactly like the unmitigated agent).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.answer_evals import DATABASE, QUERY_URI  # noqa: E402
from src.adapters.fabric_agent import FabricAgentClient  # noqa: E402
from src.config import load_config  # noqa: E402
from src.orchestrator.kusto import KustoClient, az_cli_token_provider  # noqa: E402

FABRIC_RESOURCE = "https://api.fabric.microsoft.com"
N_RUNS = 3

QUESTIONS = [
    {"key": "exact_table",
     "question": "which metrics use the IP_SEPSIS table?",
     "kql": "readers_of_table('IP_SEPSIS')",
     "expect_col": "business_name",
     # names from the OTHER family must not appear (the Round-4 disease)
     "forbid_kql": "readers_of_table('IP_SepsisEncounters')"},
    {"key": "cousin_trap",
     "question": "which metrics use the IP_SepsisEncounters table?",
     "kql": "readers_of_table('IP_SepsisEncounters')",
     "expect_col": "business_name",
     "forbid_kql": "readers_of_table('IP_SEPSIS')"},
    {"key": "column_filters",
     "question": "which metrics filter on the COMPILED_CONTEXT column?",
     "kql": "column_usage('COMPILED_CONTEXT') | where relation == 'filters'",
     "expect_col": "business_name",
     "forbid_kql": None},
]


def names(run_kql, query: str) -> "list[str]":
    return sorted({str(r.get("business_name") or "").strip()
                   for r in run_kql(query, {})} - {""})


def check(answer: str, expected: "list[str]",
          forbidden: "list[str]") -> dict:
    low = (answer or "").lower()
    carried = [n for n in expected if n.lower() in low]
    # a forbidden name that is ALSO expected is not a violation
    bad = [n for n in forbidden
           if n.lower() in low and n not in expected]
    return {"ok": len(carried) == len(expected) and not bad,
            "carried": carried,
            "absent": [n for n in expected if n not in carried],
            "cousin_leak": bad}


def main() -> None:
    store = KustoClient(QUERY_URI, DATABASE,
                        az_cli_token_provider(QUERY_URI))
    cfg = load_config()
    fabric = FabricAgentClient(
        workspace_id=cfg.fabric_graph.workspace_id,
        agent_id=cfg.fabric_graph.data_agent_id,
        token_provider=az_cli_token_provider(FABRIC_RESOURCE),
    )

    all_ok = True
    for q in QUESTIONS:
        expected = names(store.run, q["kql"])
        assert expected, f"oracle empty for {q['key']} — store problem"
        forbidden = (names(store.run, q["forbid_kql"])
                     if q["forbid_kql"] else [])
        for i in range(1, N_RUNS + 1):
            resp = fabric.query(q["question"])
            answer = (resp.answer if resp.status == "success"
                      else f"[{resp.status}] {resp.error}")
            r = check(answer, expected, forbidden)
            all_ok = all_ok and r["ok"]
            print(f"[{q['key']} run {i}/{N_RUNS}] "
                  f"{'PASS' if r['ok'] else 'FAIL'} "
                  f"carried {len(r['carried'])}/{len(expected)}"
                  + (f" absent={r['absent']}" if r["absent"] else "")
                  + (f" COUSIN_LEAK={r['cousin_leak']}"
                     if r["cousin_leak"] else ""))
            if not r["ok"]:
                print(f"    answer[:400]: {answer[:400]}")
    print("\nVERIFIED — all runs pass" if all_ok
          else "\nNOT VERIFIED — see failures above")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
