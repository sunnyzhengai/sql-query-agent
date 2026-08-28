"""ADR 0060 §6 — the gating experiment: CURRENT (LLM-routed turn
engine) vs PROPOSED (parse-traverse prototype) over the shape
corpus's planted-oracle questions.

Metrics (the ADR's five):
  1 route consistency   identical plan across paraphrases of one
                        intent (PROPOSED plans are comparable
                        op-sequences; CURRENT routes are its tool
                        call sequence)
  2 oracle correctness  the planted truth appears in displayed
                        results (DIFFERS + E11.80; 10/10 cousins;
                        grain CONFLICT)
  3 floor collapse      CURRENT: caption_corrected count;
                        PROPOSED: structurally zero (no author)
  4 detour load         rows displayed vs rows in the primary basis
  5 refusal honesty     the unmappable question fails closed with
                        the vocabulary offer, zero guessed routes

Parser tier: FRONTIER for the pilot (ruled §7.3) via
SQA_PARSE_MODEL (default gpt-4o); the engine keeps its usual tier.
Store: the SHAPES estate (run with the workbench store lever or
SQA_KUSTO_DB=semantic_catalog_shapes).

Sunny's walk paraphrases join the set when review extracts them to
internal/docs/WALK_PARAPHRASES.txt (one per line, '#' comments) —
absence is DISCLOSED in the report, never silent.

Usage: python3.11 devtools/parse_experiment.py
Writes: internal/docs/PARSE_EXPERIMENT.md
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.answer_evals import DATABASE, QUERY_URI, _load_dotenv  # noqa: E402
from src.orchestrator.agent import azure_chat_api  # noqa: E402
from src.orchestrator.kusto import (  # noqa: E402
    KustoClient,
    az_cli_token_provider,
)
from src.orchestrator.ops import OpsSession  # noqa: E402
from src.orchestrator.parse_plan import run_parse_traverse  # noqa: E402
from src.orchestrator.turn_engine import EngineSession  # noqa: E402
from src.orchestrator.turn_engine import run_turn as engine_run_turn  # noqa: E402

OUT = PROJECT_ROOT / "internal" / "docs" / "PARSE_EXPERIMENT.md"
PARAPHRASES = PROJECT_ROOT / "internal" / "docs" / "WALK_PARAPHRASES.txt"

# intent -> (questions..., oracle tokens any-of per group)
QUESTIONS = [
    {"intent": "u9_codeset_sameness",
     "asks": ["Are the two Diabetic Cohort (Coded) definitions the "
              "same?",
              "Is Diabetic Cohort (Coded) defined the same way "
              "everywhere?"],
     "oracle": [["DIFFERS", "2 group"], ["E11.80"]]},
    {"intent": "u6_cousin_flags",
     "asks": ["What governance red flags exist for Diabetic "
              "Patients?",
              "Any issues or conflicts with Diabetic Patients?"],
     "oracle": [["cousin_conflict"], ["10"]]},
    {"intent": "u12_grain",
     "asks": ["Are the two High ED Utilizers definitions the same?"],
     "oracle": [["grain_shift", "DIFFERS", "CONFLICT"]]},
    {"intent": "billing_vs_composite",
     "asks": ["How is Diabetic Patients (Billing) different from "
              "Diabetes Registry (Composite)?"],
     "oracle": [["DIFFERS", "group"]]},
    {"intent": "refusal",
     "asks": ["write me a poem about the warehouse"],
     "oracle": [["__REFUSED__"]]},
]


def load_walk_paraphrases() -> "list[str]":
    if not PARAPHRASES.exists():
        return []
    return [ln.strip() for ln in PARAPHRASES.read_text().splitlines()
            if ln.strip() and not ln.startswith("#")]


def _blob(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def hits(payload_blob: str, oracle) -> "tuple[int, int]":
    got = sum(1 for grp in oracle
              if any(tok.lower() in payload_blob.lower()
                     for tok in grp))
    return got, len(oracle)


def run_proposed(q: str, parser_api, run_kql) -> dict:
    out = run_parse_traverse(q, parser_api, run_kql, OpsSession())
    plan_sig = "→".join(s["op"] for s in out["plan"]) or "(refused)"
    return {"route": plan_sig, "refused": out["refused"],
            "blob": _blob(out), "rows_shown": sum(
                len(r.get("rows") or []) for r in out["results"]),
            "confirm": out["confirm"]}


def run_current(q: str, chat_api, run_kql) -> dict:
    s = EngineSession()
    turn = engine_run_turn(s, q, chat_api, run_kql)
    route = "→".join(
        (o.get("component") or {}).get("op", "?")
        for o in turn["outputs"])
    shown = sum(len((o.get("result") or {}).get("rows") or [])
                for o in turn["outputs"])
    primary = sum(
        len((o.get("result") or {}).get("rows") or [])
        for o in turn["outputs"]
        if (o.get("result") or {}).get("ref") not in
        set(turn.get("folded_refs") or []))
    return {"route": route,
            "refused": None if turn["answered"] else
            (turn.get("missing_op") or "not answered"),
            "blob": _blob({"caption": turn["answer"],
                           "outputs": turn["outputs"]}),
            "rows_shown": shown, "rows_primary": primary,
            "floored": bool(turn.get("caption_corrected"))}


def main() -> None:
    _load_dotenv()
    db = (os.environ.get("SQA_KUSTO_DB")
          or os.environ.get("KUSTO_DB") or DATABASE)
    client = KustoClient(QUERY_URI, db,
                         az_cli_token_provider(QUERY_URI))
    run_kql = client.run
    print(f"store: {db}")
    engine_api = azure_chat_api()
    prev = os.environ.get("SQA_LLM_MODEL")
    os.environ["SQA_LLM_MODEL"] = os.environ.get(
        "SQA_PARSE_MODEL", "gpt-4o")          # frontier pilot (§7.3)
    parser_api = azure_chat_api()
    if prev is None:
        os.environ.pop("SQA_LLM_MODEL", None)
    else:
        os.environ["SQA_LLM_MODEL"] = prev

    L = ["# ADR 0060 experiment — CURRENT vs PROPOSED "
         "(the measurement that gates the build)", ""]
    walk = load_walk_paraphrases()
    L.append(f"Walk paraphrases: {len(walk)} loaded"
             + ("" if walk else " — NOT YET EXTRACTED by review "
                "(disclosed; the corpus half runs regardless)"))
    L.append("")
    score = {"proposed_oracle": 0, "current_oracle": 0, "total": 0,
             "proposed_consistent": 0, "current_consistent": 0,
             "intents_multi": 0, "current_floors": 0}
    for spec in QUESTIONS:
        L.append(f"## {spec['intent']}")
        routes_p, routes_c = set(), set()
        for q in spec["asks"]:
            p = run_proposed(q, parser_api, run_kql)
            c = run_current(q, engine_api, run_kql)
            routes_p.add(p["route"])
            routes_c.add(c["route"])
            if spec["oracle"] == [["__REFUSED__"]]:
                p_ok = bool(p["refused"])
                c_ok = bool(c["refused"])
            else:
                p_ok = hits(p["blob"], spec["oracle"])[0] == len(
                    spec["oracle"])
                c_ok = hits(c["blob"], spec["oracle"])[0] == len(
                    spec["oracle"])
            score["total"] += 1
            score["proposed_oracle"] += int(p_ok)
            score["current_oracle"] += int(c_ok)
            score["current_floors"] += int(c.get("floored", False))
            L.append(f"- Q: {q}")
            L.append(f"  - PROPOSED: plan `{p['route']}` — "
                     f"{'ORACLE MET' if p_ok else 'oracle MISSED'}"
                     + (f"; refused: {p['refused'][:80]}"
                        if p["refused"] else "")
                     + f"; rows {p['rows_shown']}")
            L.append(f"  - CURRENT:  route `{c['route']}` — "
                     f"{'ORACLE MET' if c_ok else 'oracle MISSED'}"
                     + ("; FLOORED" if c.get("floored") else "")
                     + f"; rows {c['rows_shown']} "
                     f"(primary {c.get('rows_primary', '?')})")
        if len(spec["asks"]) > 1:
            score["intents_multi"] += 1
            score["proposed_consistent"] += int(len(routes_p) == 1)
            score["current_consistent"] += int(len(routes_c) == 1)
        L.append("")
    L += [
        "## Scorecard (the ADR's five metrics)",
        "",
        f"1. Route consistency (multi-ask intents): PROPOSED "
        f"{score['proposed_consistent']}/{score['intents_multi']}, "
        f"CURRENT {score['current_consistent']}/"
        f"{score['intents_multi']}",
        f"2. Oracle correctness: PROPOSED {score['proposed_oracle']}/"
        f"{score['total']}, CURRENT {score['current_oracle']}/"
        f"{score['total']}",
        f"3. Floor collapse: PROPOSED 0 (no author, by construction)"
        f", CURRENT {score['current_floors']}",
        "4. Detour load: per-question rows above (PROPOSED displays "
        "only the plan's rows; CURRENT primary vs shown per RW-3 "
        "folds)",
        "5. Refusal honesty: see the refusal intent above",
        "",
    ]
    OUT.write_text("\n".join(L))
    print(f"wrote {OUT}")
    print("\n".join(L[-10:]))


if __name__ == "__main__":
    main()
