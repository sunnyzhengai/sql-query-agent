"""The conversation suite — Floor 2 of ADR 0050: measure the mind.

Drives the SAME orchestrator entry the web UI calls (propose_turn →
execute_confirmed → continue_rounds → caption_turn; one engine, no
test-only path) against the live Eventhouse catalog, and grades each
turn mechanically:

- required_facts: literal values that must appear in the answer,
  DERIVED FROM THE STORE at run time (descriptions, counts, decision
  literals) — never hand-written prose expectations;
- typed-verdict cross-check: answered:true without the required facts
  is DISHONEST (build-stopper, not a metric); answered:false on an
  answerable fixture is DUMB (the rate to drive down);
- bounds: rounds used ≤ fixture's max_rounds.

Seed fixtures = the four real corpses (2026-08-20 dumb-trail).

Usage:
    python devtools/answer_evals.py            # full run (live, cents)
    python devtools/answer_evals.py --smoke    # canonical questions only

Requires: az CLI logged in; capacity active; OPENAI key in .env.
Readiness rule (ADR 0050): manual web-UI testing resumes only when
answer rate >= 0.8 per fixture family and honesty rate == 1.0.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.grounding_evals import _load_dotenv  # noqa: E402
from devtools.local_llm import chat_completion  # noqa: E402
from src.orchestrator.agent import azure_chat_api  # noqa: E402
from src.orchestrator.kusto import KustoClient, az_cli_token_provider  # noqa: E402
from src.orchestrator.ops import op_census, op_retrieve, op_search  # noqa: E402
from src.orchestrator.turn_engine import EngineSession  # noqa: E402
from src.orchestrator.turn_engine import run_turn as engine_run_turn  # noqa: E402

QUERY_URI = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
DATABASE = "probe-eh"
PARAPHRASES_PER_QUESTION = 5
ANSWER_RATE_THRESHOLD = 0.8

FIXTURES = [
    {"family": "census",
     "question": "how many metrics are there",
     "oracle": "census_count", "max_rounds": 1,
     "expected_kind": "answered"},
    {"family": "definition",
     "question": "how is Sepsis Case Encounters defined",
     "oracle": "definition_facts", "item": "Sepsis Case Encounters",
     "max_rounds": 2, "expected_kind": "answered"},
    {"family": "bridge",
     "question": "how is Sepsis Case defined",
     "oracle": "near_name_bridge", "phrase": "Sepsis Case",
     "max_rounds": 2, "expected_kind": "bridge"},
    {"family": "drilldown",
     "question": "in Severe Sepsis Episodes, how is a patient "
                 "diagnosed with severe sepsis",
     "oracle": "beyond_summary", "item": "Severe Sepsis Episodes",
     "max_rounds": 3, "expected_kind": "answered"},
    # Corpses from the 2026-08-20 evening trail:
    {"family": "topical_count",
     "question": "how many metrics are about sepsis",
     "oracle": "topical_count", "topic": "sepsis",
     "max_rounds": 2, "expected_kind": "answered"},
    # Re-pointed (iteration 3): Sepsis Case Encounters is a passthrough
    # metric (genuinely no criteria) — the fixture graded honest "no
    # criteria in this metric" answers as misses. Severe Sepsis
    # Episodes HAS step-level criteria; the fixture now tests anaphora
    # resolution + drill-down against a metric where the answer exists.
    {"family": "anaphora",
     "questions": ["how is metric Severe Sepsis Episodes defined",
                   "in this metric, how is a patient diagnosed with "
                   "severe sepsis"],
     "question": "in this metric, how is a patient diagnosed with "
                 "severe sepsis",
     "oracle": "beyond_summary", "item": "Severe Sepsis Episodes",
     "max_rounds": 3, "expected_kind": "answered"},
]

_WORD = re.compile(r"[A-Za-z_]{6,}")


def _fresh_ops_session():
    from src.orchestrator.ops import OpsSession
    return OpsSession()


def build_oracle(fixture: dict, run_kql) -> dict:
    """Derive the grading key FROM THE STORE — the no-hardcoded-answers
    rule applied to grading. Returns {required_any (list of lists —
    each inner list is alternatives, one must appear), forbidden}."""
    ops = _fresh_ops_session()
    kind = fixture["oracle"]
    if kind == "census_count":
        rs = op_census("metric", run_kql, ops)
        return {"required_any": [[str(len(rs.rows))]], "forbidden": []}
    if kind == "definition_facts":
        rs = op_search(fixture["item"], "exact", run_kql, ops)
        assert rs.rows, f"oracle: {fixture['item']} not in catalog"
        rec = op_retrieve([rs.rows[0]["id"]], run_kql, ops)
        blob = json.dumps(rec.rows)
        words = sorted(set(_WORD.findall(blob)))[:400]
        # the answer must carry >=3 distinctive content words of the
        # stored record — checked as alternatives, counted by grader
        return {"required_any": [words], "required_overlap": 3,
                "forbidden": []}
    if kind == "near_name_bridge":
        ops2 = _fresh_ops_session()
        rs = op_census("metric", run_kql, ops2)
        phrase = fixture["phrase"].lower()
        near = [r["name"] for r in rs.rows
                if phrase in (r.get("business_name") or r["name"]).lower()
                ] + [r.get("business_name") for r in rs.rows
                     if r.get("business_name")
                     and phrase in r["business_name"].lower()]
        near = sorted({n for n in near if n})
        assert near, "oracle: no near-name siblings found"
        return {"required_any": [near],
                "forbidden": ["no metrics exist",
                              "no such metric exists"]}
    if kind == "topical_count":
        rs = op_census("metric", run_kql, ops)
        topic = fixture["topic"].lower()
        n = sum(1 for r in rs.rows if topic in json.dumps(r).lower())
        assert n, "oracle: topic matches nothing"
        return {"required_any": [[str(n)]], "forbidden": []}
    if kind == "beyond_summary":
        ops2 = _fresh_ops_session()
        rs = op_search(fixture["item"], "exact", run_kql, ops2)
        assert rs.rows, f"oracle: {fixture['item']} not in catalog"
        rid = rs.rows[0]["id"]
        summary = json.dumps(rs.rows[0])
        rec = op_retrieve([rid], run_kql, ops2)
        deep_blob = json.dumps(rec.rows)
        summary_words = set(_WORD.findall(summary.lower()))
        deep = sorted({w for w in _WORD.findall(deep_blob)
                       if w.lower() not in summary_words})
        assert deep, "oracle: no step-level facts beyond the summary"
        return {"required_any": [deep], "required_overlap": 1,
                "forbidden": []}
    raise ValueError(kind)


def grade(answer: str, verdict: dict, oracle: dict,
          rounds_used: int, fixture: dict) -> dict:
    low = answer.lower()
    hits = 0
    for group in oracle["required_any"]:
        if any(alt.lower() in low for alt in group):
            hits += 1
    need = oracle.get("required_overlap", len(oracle["required_any"]))
    if oracle.get("required_overlap"):
        hits = sum(1 for alt in oracle["required_any"][0]
                   if alt.lower() in low)
    facts_present = hits >= need
    fabricated = any(f.lower() in low for f in oracle["forbidden"])
    declared = bool(verdict.get("answered"))
    dishonest = (declared and not facts_present) or fabricated
    # Grader calibration 2 (iteration-3 finding): ALL families score on
    # facts, not on the declaration — four drilldown captions carried
    # the required criteria and were graded down solely for a humble
    # answered=false. "Grade on trace + data facts, never on prose
    # shapes" applies to the verdict flag too: it polices honesty
    # (declared without facts = DISHONEST), it never awards points.
    answer_ok = facts_present and not dishonest
    return {
        "facts_present": facts_present,
        "declared_answered": declared,
        "answer_ok": answer_ok,
        "dishonest": dishonest,                       # build-stopper
        "dumb": (not declared) and fixture["expected_kind"] == "answered",
        "within_rounds": rounds_used <= fixture["max_rounds"],
        "fact_hits": hits,
    }


def run_trail(questions: "list[str]", chat_api, run_kql) -> dict:
    """One shared ENGINE session across the trail (ADR 0051: anaphora
    is a property of memory — the same conversation carries every
    turn); graded on the FINAL turn."""
    session = EngineSession()
    result: dict = {}
    for question in questions:
        turn = engine_run_turn(session, question, chat_api, run_kql)
        result = {
            "outputs": turn["outputs"],
            "loop": {"rounds": list(range(turn["rounds"])),
                     "status_line": (f"one mind: {turn['rounds']} tool "
                                     "round(s)")},
            "cap": {"caption": turn["answer"],
                    "answered": turn["answered"],
                    "missing_op": turn["missing_op"],
                    "caption_corrected": turn["caption_corrected"],
                    "caption_violations": turn["caption_violations"]},
        }
    return result


def paraphrases(question: str, n: int) -> "list[str]":
    text = chat_completion(
        "You produce terse paraphrase lists.",
        f"Give {n} distinct natural paraphrases of this question, one "
        f"per line, no numbering:\n{question}")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[:n]


PINNED_PROMPT_SHA = ("20781efb5545aebce28e7a1c402c5a09"
                     "684403f29048f5302a8d5ea3de9114b9")


def main() -> None:
    _load_dotenv()
    # Thesis discipline (HANDOFF_ONE_MIND): the suite grades a PINNED
    # prompt — a pass that needed new prompt lines shows as a hash
    # mismatch and refuses to grade.
    import hashlib

    from src.orchestrator.turn_engine import SYSTEM_PROMPT
    actual = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()
    if actual != PINNED_PROMPT_SHA:
        print(f"[X] prompt hash {actual[:12]}… != pinned "
              f"{PINNED_PROMPT_SHA[:12]}… — the engine prompt changed; "
              "update the pin CONSCIOUSLY and note it in the Round-4 "
              "RESULTS log before grading.")
        raise SystemExit(4)
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="canonical questions only, no paraphrases")
    args = ap.parse_args()

    client = KustoClient(QUERY_URI, DATABASE,
                         az_cli_token_provider(QUERY_URI))
    run_kql = client.run
    try:                                        # preflight, clean exit
        run_kql("semantic_catalog | count", {})
    except Exception as e:                      # noqa: BLE001
        print(f"[X] store unreachable ({type(e).__name__}) — resume the "
              "Fabric capacity, wait ~2 min, retry. Nothing was graded.")
        raise SystemExit(3)
    chat_api = azure_chat_api()

    families: "dict[str, list[dict]]" = {}
    _dump: "list[dict]" = []
    stop_build = False
    for fixture in FIXTURES:
        try:
            oracle = build_oracle(fixture, run_kql)
        except AssertionError:
            raise
        except Exception as e:                  # noqa: BLE001 — infra
            print(f"[X] store dropped mid-run ({type(e).__name__}) — "
                  "capacity is flapping; resume it and retry. Partial "
                  "grades discarded.")
            raise SystemExit(3)
        trail_prefix = fixture.get("questions", [fixture["question"]])[:-1]
        questions = [fixture["question"]]
        if not args.smoke:
            questions += paraphrases(fixture["question"],
                                     PARAPHRASES_PER_QUESTION)
        for q in questions:
            turn = run_trail(trail_prefix + [q], chat_api, run_kql)
            g = grade(turn["cap"].get("caption", ""), turn["cap"], oracle,
                      len(turn["loop"]["rounds"]), fixture)
            g["question"] = q
            families.setdefault(fixture["family"], []).append(g)
            _dump.append({"family": fixture["family"], "question": q,
                          "grade": g, "caption": turn["cap"],
                          "loop": {"rounds": len(turn["loop"]["rounds"]),
                                   "status": turn["loop"]["status_line"]},
                          "outputs": [
                              {"component": o.get("component"),
                               "error": o.get("error"),
                               "headline": (o.get("result") or {}).get(
                                   "headline"),
                               "rows": len((o.get("result") or {}).get(
                                   "rows") or [])}
                              for o in turn["outputs"]]})
            flag = ("DISHONEST" if g["dishonest"] else
                    "dumb" if g["dumb"] else "ok")
            print(f"[{fixture['family']}] {flag:9s} facts={g['fact_hits']} "
                  f"rounds<= {g['within_rounds']} :: {q[:60]}")
            if g["dishonest"]:
                stop_build = True

    dump_path = PROJECT_ROOT / "data" / "output" / "answer_evals_last.jsonl"
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    dump_path.write_text("\n".join(json.dumps(d) for d in _dump))
    print(f"\n(transcripts: {dump_path})")

    print("\n=== scorecard ===")
    all_pass = True
    for family, grades in families.items():
        n = len(grades)
        answer_rate = sum(1 for g in grades if g["answer_ok"]) / n
        honesty = 1.0 - sum(1 for g in grades if g["dishonest"]) / n
        ok = answer_rate >= ANSWER_RATE_THRESHOLD and honesty == 1.0
        all_pass &= ok
        print(f"{family:12s} answer_rate={answer_rate:.2f} "
              f"honesty={honesty:.2f} n={n} "
              f"{'PASS' if ok else 'BELOW THRESHOLD'}")
    if stop_build:
        print("\n[X] DISHONEST turn observed — build-stopper, not a metric.")
        raise SystemExit(2)
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
