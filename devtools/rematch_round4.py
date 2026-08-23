"""Rematch Round 4 — homegrown orchestrator vs the (refreshed) Fabric
Data Agent, one scripted run, oracle-scored (HANDOFF_REMATCH_ROUND4_GOAL).

Protocol (the standing rematch discipline): fixed questions, run ONCE,
scored against oracles derived from the store, recorded beside rounds
1–3. Never casual chat. Both surfaces get the SAME questions; the
homegrown side runs the exact web-UI entry (propose → execute →
auto-continue → answer); the Fabric side runs via the MCP adapter.

Scoring per family:
    answer   required facts present (same oracles as answer_evals)
    honesty  homegrown: typed-verdict cross-check (answered without
             facts = dishonest); Fabric: forbidden-claim scan only
             (no typed verdict exists on that surface — measured with
             a coarser ruler, stated on the scorecard)
    latency  wall seconds per turn; p50 reported

Usage:
    python devtools/rematch_round4.py           # the round (one run)

Requires: az CLI logged in; capacity active; OPENAI key in .env;
org_config.yaml fabric_graph.workspace_id/data_agent_id; the Fabric
agent republished AFTER the 1.44.0 pipeline rerun (pre-flight checks
refuse to run against a stale surface).
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.answer_evals import (  # noqa: E402
    DATABASE,
    FIXTURES,
    QUERY_URI,
    build_oracle,
    grade,
    run_trail,
)
from devtools.grounding_evals import _load_dotenv  # noqa: E402
from src.adapters.fabric_agent import FabricAgentClient  # noqa: E402
from src.config import load_config  # noqa: E402
from src.orchestrator.agent import azure_chat_api  # noqa: E402
from src.orchestrator.kusto import KustoClient, az_cli_token_provider  # noqa: E402
from src.orchestrator.ops import OpsSession, op_retrieve, op_search  # noqa: E402

FABRIC_RESOURCE = "https://api.fabric.microsoft.com"
SCORECARD = PROJECT_ROOT / "internal" / "docs" / "REMATCH_ROUND4_SCORECARD.md"
RAW_LOG = PROJECT_ROOT / "internal" / "docs" / "REMATCH_ROUND4_RAW.jsonl"

# The historical count-oracle family (rounds 2/3 class), derived live.
EXTRA_FIXTURES = [
    {"family": "step_count",
     "question": "how many calculation steps does Severe Sepsis Episodes "
                 "have",
     "oracle": "step_count", "item": "Severe Sepsis Episodes",
     "max_rounds": 2, "expected_kind": "answered"},
]


def build_extra_oracle(fixture: dict, run_kql) -> dict:
    ops = OpsSession()
    rs = op_search(fixture["item"], "exact", run_kql, ops)
    assert rs.rows, f"oracle: {fixture['item']} not in catalog"
    rec = op_retrieve([rs.rows[0]["id"]], run_kql, ops)
    steps = (rec.rows[0] or {}).get("steps") or []
    assert steps, "oracle: metric has no steps"
    return {"required_any": [[str(len(steps))]], "forbidden": []}


def characterize(answer: str, oracle: dict) -> dict:
    """Machine fact accounting for the scorecard: which oracle
    alternatives the answer carries and which it lacks. The Round-4
    lesson: the hand-written miss characterization contradicted the
    machine table — prose may annotate these lines, never replace them.
    """
    low = (answer or "").lower()
    if oracle.get("required_overlap"):
        alts = oracle["required_any"][0]
        hit = [a for a in alts if a.lower() in low]
        return {"need": oracle["required_overlap"], "hits": len(hit),
                "total": len(alts), "hit": hit,
                "missed": [a for a in alts if a not in hit]}
    hit, missed = [], []
    for group in oracle["required_any"]:
        found = next((a for a in group if a.lower() in low), None)
        (hit.append(found) if found else missed.append(group[0]))
    total = len(oracle["required_any"])
    return {"need": total, "hits": len(hit), "total": total,
            "hit": hit, "missed": missed}


def grade_fabric(answer: str, oracle: dict, fixture: dict) -> dict:
    low = (answer or "").lower()
    facts = characterize(answer, oracle)
    fabricated = any(f.lower() in low for f in oracle["forbidden"])
    return {"facts_present": facts["hits"] >= facts["need"],
            "dishonest": fabricated, "fact_hits": facts["hits"],
            "facts": facts}


def main() -> None:
    _load_dotenv()
    client = KustoClient(QUERY_URI, DATABASE,
                         az_cli_token_provider(QUERY_URI))
    run_kql = client.run
    run_kql("semantic_catalog | count", {})           # store preflight
    chat_api = azure_chat_api()

    cfg = load_config()
    fabric = FabricAgentClient(
        workspace_id=cfg.fabric_graph.workspace_id,
        agent_id=cfg.fabric_graph.data_agent_id,
        token_provider=az_cli_token_provider(FABRIC_RESOURCE),
    )

    all_fixtures = FIXTURES + EXTRA_FIXTURES
    rows = []
    RAW_LOG.write_text("")            # fresh raw log for this run
    for fixture in all_fixtures:
        if fixture in EXTRA_FIXTURES:
            oracle = build_extra_oracle(fixture, run_kql)
        else:
            oracle = build_oracle(fixture, run_kql)
        trail = fixture.get("questions", [fixture["question"]])

        t0 = time.monotonic()
        turn = run_trail(trail, chat_api, run_kql)
        home_s = time.monotonic() - t0
        g_home = grade(turn["cap"].get("caption", ""), turn["cap"], oracle,
                       len(turn["loop"]["rounds"]), fixture)

        t0 = time.monotonic()
        fabric_answers = []
        for q in trail:                     # Fabric has no session; ask all
            resp = fabric.query(q)
            fabric_answers.append(resp.answer if resp.status == "success"
                                  else f"[{resp.status}] {resp.error}")
        fabric_s = time.monotonic() - t0
        g_fab = grade_fabric(fabric_answers[-1], oracle, fixture)
        # reporting-only for the homegrown side (its PASS/miss is
        # grade()'s, typed verdict included) — same accounting ruler
        home_caption = turn["cap"].get("caption") or ""
        c_home = characterize(home_caption, oracle)

        rows.append({
            "family": fixture["family"], "question": fixture["question"],
            "home": g_home, "home_s": round(home_s, 2),
            "home_facts": c_home,
            "fabric": g_fab, "fabric_s": round(fabric_s, 2),
            "fabric_answer": fabric_answers[-1][:400],
            "home_answer": home_caption[:400],
        })
        # full evidence beside the scorecard — the truncated verbatim
        # section can no longer be the only record of what was said
        with RAW_LOG.open("a") as fh:
            fh.write(json.dumps({
                "family": fixture["family"],
                "question": fixture["question"],
                "oracle": oracle,
                "home": {"answer": home_caption, "grade": g_home,
                         "facts": c_home, "s": round(home_s, 2)},
                "fabric": {"answers": fabric_answers, "grade": g_fab,
                           "s": round(fabric_s, 2)},
            }, default=str) + "\n")
        print(f"[{fixture['family']}] home="
              f"{'ok' if g_home['facts_present'] else 'miss'}"
              f"{'/DISHONEST' if g_home['dishonest'] else ''} "
              f"({rows[-1]['home_s']}s)  fabric="
              f"{'ok' if g_fab['facts_present'] else 'miss'}"
              f"{'/FABRICATED' if g_fab['dishonest'] else ''} "
              f"({rows[-1]['fabric_s']}s)")

    home_p50 = statistics.median(r["home_s"] for r in rows)
    fab_p50 = statistics.median(r["fabric_s"] for r in rows)
    SCORECARD.write_text("\n".join(scorecard_lines(rows, home_p50, fab_p50)))
    print(f"\nWrote {SCORECARD}")
    print(f"Latency p50: homegrown {home_p50}s vs fabric {fab_p50}s")


def scorecard_lines(rows: "list[dict]", home_p50: float,
                    fab_p50: float) -> "list[str]":
    """The scorecard, machine-emitted end to end. Prose elsewhere (goal
    file, relays) annotates these lines — it never free-writes a miss
    list, and any 'X is not in the catalog' claim carries its grep
    receipt (the Round-4 record-audit rule)."""
    lines = [
        "# Rematch Round 4 — homegrown orchestrator vs Fabric Data Agent",
        "",
        "Protocol: fixed questions, ONE run, oracles derived from the "
        "store (HANDOFF_REMATCH_ROUND4_GOAL). Homegrown honesty is "
        "typed-verdict cross-checked; Fabric honesty is forbidden-claim "
        "scanned only (no typed verdict exists on that surface). Facts "
        "bars are oracle thresholds — overlap oracles PASS on partial "
        "name overlap; per-row hit accounting is machine-emitted below "
        "and in full in REMATCH_ROUND4_RAW.jsonl.",
        "",
        f"Latency p50: homegrown {home_p50}s · fabric {fab_p50}s",
        "",
        "| family | homegrown | s | fabric | s | verdict |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        h = ("PASS" if r["home"]["facts_present"] else "miss") + (
            " DISHONEST" if r["home"]["dishonest"] else "")
        f = ("PASS" if r["fabric"]["facts_present"] else "miss") + (
            " FABRICATED" if r["fabric"]["dishonest"] else "")
        verdict = ("homegrown" if (r["home"]["facts_present"],
                                   not r["home"]["dishonest"])
                   >= (r["fabric"]["facts_present"],
                       not r["fabric"]["dishonest"]) else "fabric")
        lines.append(f"| {r['family']} | {h} | {r['home_s']} | {f} | "
                     f"{r['fabric_s']} | {verdict} |")

    # Machine-emitted characterization: every miss, and every PASS
    # earned on partial overlap of a small name-set oracle. Prose in
    # the goal file annotates THESE lines — it never free-writes a
    # miss list (the Round-4 record-audit rule).
    lines += ["", "## Misses and partial passes (machine-emitted)", ""]
    for r in rows:
        for side in ("home", "fabric"):
            g = r[side]
            facts = r["home_facts"] if side == "home" else g.get("facts")
            if not facts:
                continue
            tag = None
            if not g["facts_present"]:
                tag = "miss"
            elif facts["hits"] < facts["total"] and facts["total"] <= 10:
                tag = "PASS on partial overlap"
            if tag is None:
                continue
            carried = ", ".join(facts["hit"][:8]) or "none"
            absent = ", ".join(facts["missed"][:8]) or "none"
            lines.append(
                f"- {side} {tag} — {r['family']} — "
                f"\"{r['question']}\": hits {facts['hits']}/"
                f"{facts['need']} needed of {facts['total']}; "
                f"carried: [{carried}]; absent: [{absent}]")
    lines += ["", "## Answers (verbatim, truncated 400 — full text in "
              "REMATCH_ROUND4_RAW.jsonl)", ""]
    for r in rows:
        lines += [f"### {r['family']} — {r['question']}",
                  f"- homegrown: {r['home_answer']}",
                  f"- fabric: {r['fabric_answer']}", ""]
    return lines


if __name__ == "__main__":
    main()
