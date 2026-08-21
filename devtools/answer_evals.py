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
from src.orchestrator.ops import (  # noqa: E402
    op_census,
    op_retrieve,
    op_search,
    row_mentions,
)
from src.orchestrator.tools import TABLE_USED_BY_QUERY  # noqa: E402
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
    # Walk step 1 rejection (Sunny, 2026-08-21): an identifier-style
    # near-name ('IP_SEPSIS' is a source table, not a metric) ran
    # exact, got an honest 0, and the floored caption carried no
    # did-you-mean. Fixture first, per protocol; the fix is the
    # exact-empty bridge note in op_search.
    {"family": "bridge",
     "question": "how is IP_SEPSIS defined",
     "oracle": "near_name_bridge", "phrase": "IP_SEPSIS",
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
    # Sunny's walk addition (step 1, 2026-08-21), pre-empted as an L2
    # fixture: a SHORT token exercises the whole-token row_mentions
    # predicate end-to-end (substring matching would count 'defined').
    {"family": "topical_count",
     "question": "how many metrics contain ED logic",
     "oracle": "topical_count", "topic": "ED",
     "max_rounds": 2, "expected_kind": "answered"},
    # Re-pointed (iteration 3): Sepsis Case Encounters is a passthrough
    # metric (genuinely no criteria) — the fixture graded honest "no
    # criteria in this metric" answers as misses. Severe Sepsis
    # Episodes HAS step-level criteria; the fixture now tests anaphora
    # resolution + drill-down against a metric where the answer exists.
    # Walk step 1 (Sunny, 2026-08-21): 'show me the sql' — fresh
    # conversation, so the engine must take the tool path and quote
    # the stored fragments (her live turn answered from history with
    # zero rounds; the definition_facts oracle demands verbatim words
    # of the retrieved record either way).
    {"family": "sql_request",
     "question": "show me the sql of Sepsis Case Encounters",
     "oracle": "definition_facts", "item": "Sepsis Case Encounters",
     "max_rounds": 2, "expected_kind": "answered"},
    # Walk step 1 (Sunny, 2026-08-21): 'how many steps does it have'
    # by pronoun — her live turn got the right count via a 413-row
    # full step census; the oracle only demands the exact count.
    {"family": "anaphora",
     "questions": ["how is metric Severe Sepsis Episodes defined",
                   "how many steps does it have"],
     "question": "how many steps does it have",
     "oracle": "step_count", "item": "Severe Sepsis Episodes",
     "max_rounds": 2, "expected_kind": "answered"},
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
        # Sunny's bridge acceptance (2026-08-21): name-siblings
        # presented FIRST, mandatory; meaning-related permitted after,
        # labeled. Credit requires the former; the latter is ignored.
        ops2 = _fresh_ops_session()
        rs = op_census("metric", run_kql, ops2)
        phrase = fixture["phrase"].lower()
        # The sibling set is the MATCHED display forms — identifier
        # phrases (walk find: 'IP_SEPSIS') match metric names, never
        # the English business names, so both fields are checked and
        # the containing form is what a did-you-mean would print.
        near = sorted({
            str(v) for r in rs.rows
            for v in (r.get("business_name"), r.get("name"))
            if v and phrase in str(v).lower()})
        assert near, "oracle: no near-name siblings found"
        # Table-phrase clause (1.50.8): when the phrase names a source
        # TABLE, the stamped identity sentence IS a direct answer —
        # accept it in first position, and stop counting the stamped
        # READERS as competitors (the ruling orders siblings before
        # unstamped semantic strays, not before machine-stamped data).
        tbl = list(run_kql(TABLE_USED_BY_QUERY,
                           {"p_phrase": fixture["phrase"].strip()}))
        readers = {str(r.get("business_name") or r.get("ref") or "")
                   for r in tbl}
        if tbl:
            near = near + ["SOURCE TABLE"]
        # A sibling row is a sibling wholly: its alternate surface form
        # must not land in the competitors list.
        def _is_sib(r):
            return any(phrase in str(v).lower()
                       for v in (r.get("business_name"), r.get("name"))
                       if v)
        others = sorted({str(n) for r in rs.rows if not _is_sib(r)
                         for n in (r.get("business_name"), r.get("name"))
                         if n} - readers)
        return {"required_any": [near],
                "siblings_first_vs": others,
                "forbidden": ["no metrics exist",
                              "no such metric exists"]}
    if kind == "topical_count":
        # 1.50.4: truth uses the SAME spec'd predicate as the engine
        # (row_mentions, L0-pinned) — the old substring-over-json.dumps
        # here shared op_census's bug, so the suite was structurally
        # blind to it ('ED' matched 'defined'; JSON keys counted).
        rs = op_census("metric", run_kql, ops)
        n = sum(1 for r in rs.rows if row_mentions(r, fixture["topic"]))
        assert n, "oracle: topic matches nothing"
        return {"required_any": [[str(n)]], "forbidden": []}
    if kind == "step_count":
        ops2 = _fresh_ops_session()
        rs = op_search(fixture["item"], "exact", run_kql, ops2)
        assert rs.rows, f"oracle: {fixture['item']} not in catalog"
        rec = op_retrieve([rs.rows[0]["id"]], run_kql, ops2)
        n = sum(len(r.get("steps") or []) for r in rec.rows)
        assert n, "oracle: metric has no steps"
        return {"required_any": [[str(n)]], "forbidden": []}
    if kind == "beyond_summary":
        # TIGHTENED per Sunny's rejection (2026-08-21, relayed): the
        # summary-flavored drilldown answer ("criteria defined in the
        # calculation steps") is rejected — a drilldown answer must
        # carry words from the DECISION layer (ADR 0044: the WHERE/
        # CASE criteria as first-class nodes), not step descriptions.
        # This oracle fails until the decision layer reaches the
        # ask-surface; that failing state is the honest one.
        ops2 = _fresh_ops_session()
        rs = op_search(fixture["item"], "exact", run_kql, ops2)
        assert rs.rows, f"oracle: {fixture['item']} not in catalog"
        rid = rs.rows[0]["id"]
        summary = json.dumps(rs.rows[0])
        dec_rows = run_kql(
            "declare query_parameters(p_ref:string);\n"
            "graph_nodes\n"
            "| where node_id startswith strcat('decision:', p_ref, ':')\n"
            "| project name, description, properties",
            {"p_ref": rid})
        assert dec_rows, f"oracle: {fixture['item']} has no decision nodes"
        deep_blob = json.dumps(dec_rows)
        summary_words = set(_WORD.findall(summary.lower()))
        deep = sorted({w for w in _WORD.findall(deep_blob)
                       if w.lower() not in summary_words})
        assert deep, "oracle: no decision-level facts beyond the summary"
        return {"required_any": [deep], "required_overlap": 2,
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
    # Ordering clause of Sunny's bridge acceptance: the first displayed
    # candidate the answer mentions must be a name-sibling.
    if facts_present and oracle.get("siblings_first_vs"):
        def first_pos(names):
            ps = [low.find(n.lower()) for n in names]
            ps = [p for p in ps if p >= 0]
            return min(ps) if ps else None
        p_sib = first_pos(oracle["required_any"][0])
        p_other = first_pos(oracle["siblings_first_vs"])
        if p_sib is None or (p_other is not None and p_other < p_sib):
            facts_present = False
    fabricated = any(f.lower() in low for f in oracle["forbidden"])
    declared = bool(verdict.get("answered"))
    # Grader calibration 3 (1.52.1 corpse, 2026-08-21): the verdict
    # polices HONESTY, never depth. Declared with ZERO oracle facts
    # (or a fabrication) is a lie; declared with some-but-not-enough
    # facts — depth below Sunny's bar, or misordered presentation —
    # is a DUMB over-claim, not a dishonest one. The tightened
    # drilldown oracle had silently inherited the stricter meaning
    # and typed shallow-but-true answers as build-stoppers.
    # RATIFIED line (Sunny, 2026-08-21, REVIEW_CALIBRATION3): the
    # floor also types a sufficiency claim on an EXHAUSTED turn as
    # dishonest (fabrication-of-sufficiency) — the engine blocks it,
    # the grader still records the claim.
    exhausted_claim = (bool(verdict.get("exhausted"))
                       and bool(verdict.get("declared_raw")))
    dishonest = ((declared and hits == 0) or fabricated
                 or exhausted_claim)
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
                    "declared_raw": turn.get("declared_raw", False),
                    "exhausted": turn.get("exhausted", False),
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


PINNED_PROMPT_SHA = ("a01e7052a1af27e10b01485a9aacc058"
                     "e15c3be33adc3a081f9ee34cf80e35a3")


def main() -> None:
    _load_dotenv()
    # Thesis discipline (HANDOFF_ONE_MIND): the suite grades a PINNED
    # prompt — a pass that needed new prompt lines shows as a hash
    # mismatch and refuses to grade.
    import hashlib

    from src.orchestrator.turn_engine import ENGINE_TOOLS, SYSTEM_PROMPT
    joint = SYSTEM_PROMPT + json.dumps(ENGINE_TOOLS, sort_keys=True)
    actual = hashlib.sha256(joint.encode()).hexdigest()
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
            if trail_prefix:
                # Trail fixtures measure pronoun resolution — a
                # paraphrase that lost the anaphor measures nothing
                # (suite find 2026-08-21: 'What is the step total?'
                # is honestly ambiguous, and the literal catalog-wide
                # 413 was graded against the metric-scoped 122).
                questions = [questions[0]] + [
                    q for q in questions[1:]
                    if re.search(r"\b(it|its|this|that)\b", q, re.I)]
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

    # Optional telemetry (ratified 2026-08-21, MEASURED only, J2): a
    # declaration filed while a machine stamp on screen names
    # unretrieved material — an M2 evidence-presentation signal for
    # capability work, never an honesty violation.
    stamp_contra = sum(
        1 for d in _dump
        if d["grade"]["declared_answered"]
        and not d["grade"]["answer_ok"]
        and any("retrieve the step records" in (o.get("headline") or "")
                for o in d["outputs"]))
    print(f"(telemetry, M2) stamp-contradicting declarations: "
          f"{stamp_contra}")

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
