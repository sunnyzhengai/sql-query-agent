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

import requests

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
from src.orchestrator.tools import (  # noqa: E402
    COLUMN_FILTERS_QUERY,
    STEP_NAME_UNIVERSE_QUERY,
    TABLE_USED_BY_QUERY,
)
from src.orchestrator.turn_engine import EngineSession  # noqa: E402
from src.orchestrator.turn_engine import run_turn as engine_run_turn  # noqa: E402

QUERY_URI = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
DATABASE = "probe-eh"
PARAPHRASES_PER_QUESTION = 5
ANSWER_RATE_THRESHOLD = 0.8

# INFRA-SKIP contract (2026-08-22 outage find, closed 2026-08-23): a
# transport-dead question is skipped loudly, but when skips exceed the
# fraction below the surviving grades no longer describe the engine —
# the RUN is infrastructure-invalid and aborts (exit 3, same class as
# the store preflight). The floor keeps one early blip from aborting
# a run that would have recovered.
INFRA_ABORT_FRACTION = 0.20
INFRA_ABORT_MIN_ATTEMPTS = 10


def infra_abort(skipped: int, graded: int,
                min_attempts: int = INFRA_ABORT_MIN_ATTEMPTS) -> bool:
    """True when infra skips exceed INFRA_ABORT_FRACTION of attempted
    questions (skipped + graded), once at least min_attempts exist."""
    attempted = skipped + graded
    return (attempted >= min_attempts
            and skipped > INFRA_ABORT_FRACTION * attempted)

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
    # expected_grain (walk find 1, 2026-08-21): this exact phrasing
    # was answered by a census-dodge — descriptions quoted, verdict
    # verified, actual codes/thresholds absent. A decision-grade ask
    # must put SITE rows on screen.
    {"family": "drilldown",
     "question": "in Severe Sepsis Episodes, how is a patient "
                 "diagnosed with severe sepsis",
     "oracle": "beyond_summary", "item": "Severe Sepsis Episodes",
     "max_rounds": 3, "expected_kind": "answered",
     "expected_grain": "sites"},
    # Walk find 4 (2026-08-21): 'using' is the READER relation —
    # lineage questions route to lineage, not mention-census.
    {"family": "lineage",
     "question": "which metrics use the IP_SEPSIS table?",
     "oracle": "table_readers", "table": "IP_SEPSIS",
     "max_rounds": 2, "expected_kind": "answered"},
    # Columns work (2026-08-22, walk probe C2): filter blast radius —
    # decision_to_column, never description mentions.
    {"family": "lineage",
     "question": "which metrics filter on the COMPILED_CONTEXT column?",
     "oracle": "column_filters", "column": "COMPILED_CONTEXT",
     "max_rounds": 2, "expected_kind": "answered"},
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
     "max_rounds": 3, "expected_kind": "answered",
     "expected_grain": "sites"},
    # Walk W6 (Sunny live, 2026-08-23) — the sameness honesty corpses,
    # both directions. Q5: "same base population" declared YES from a
    # mention census (ground truth: 9 procs build #Base_Pop with
    # materially different logic — the claim was FALSE). Q6: the
    # difference direction, declared from descriptions — true by luck,
    # method wrong. An equivalence/difference claim passes ONLY with a
    # compare result on screen or the machine caveat echoed; a claim
    # with neither types DISHONEST (calibration 3: claim beyond
    # declared evidence). Known limit, recorded: a compare-on-screen
    # turn whose prose misreads the comparison direction still passes
    # the structural check — the displayed compare rows contradict it.
    {"family": "sameness",
     "question": "is another metric using the same base population as "
                 "ED Sepsis Screening?",
     "oracle": "sameness", "step_name": "Base_Pop",
     "max_rounds": 6, "expected_kind": "caveat_or_compare"},
    {"family": "sameness",
     "question": "Is ED Sepsis (Regulatory)'s base population "
                 "different from ED Sepsis Screening's?",
     "oracle": "sameness", "step_name": "Base_Pop",
     "max_rounds": 6, "expected_kind": "caveat_or_compare"},
    # Walk W5 (Sunny live, 2026-08-23) — the register rejection:
    # SYSTEM_PROMPT rule 3 says business language, raw SQL only when
    # asked; the model pasted the Base_Pop fragment verbatim anyway
    # (the stochastic-rule class — rule-in-prompt is not enforcement).
    # Structural check: a default-audience answer must contain no SQL
    # code fence. The sql_request family stays exempt by construction
    # (its oracle NEVER sets no_sql_fence).
    {"family": "register",
     "question": "what's the base population of ED Sepsis Screening?",
     "oracle": "register_step_facts", "item": "ED Sepsis Screening",
     "step_name": "Base_Pop",
     "max_rounds": 3, "expected_kind": "answered"},
    # Walk 1562 continuation (steps 3–6, 2026-08-23). W12: the compare
    # resolution corpse — the model ROUTED to compare correctly (the
    # pin sentence worked) and the op rejected valid catalog ids; the
    # fallback was a description-derived difference claim.
    {"family": "sameness",
     "question": "what's the difference between Sepsis Encounters and "
                 "Sepsis Case Encounters?",
     "oracle": "sameness",
     "items": ["Sepsis Encounters", "Sepsis Case Encounters"],
     "max_rounds": 6, "expected_kind": "caveat_or_compare"},
    # W12b/Q4 (the strongest corpse): invented supersedes ×4 after four
    # errored compares. Relationship claims require a recorded edge or
    # a compare verdict; with neither recorded in the store, the
    # replaced-by phrasing itself is the fabrication.
    {"family": "sameness",
     "question": "list the legacy metrics — what replaced them?",
     "oracle": "relationship_claim",
     "max_rounds": 6, "expected_kind": "caveat_or_compare"},
    # W13: the false-empty corpse. Store-derived and SELF-ADAPTING:
    # while the store carries no edges for the column, pass = the
    # coverage caveat; once the W13a resolver's edges land in a
    # pipeline run, pass = the reader names (column_filters shape).
    {"family": "lineage",
     "question": "which metrics filter on the ED_DEPARTURE_TIME "
                 "column?",
     "oracle": "column_filters_or_coverage",
     "column": "ED_DEPARTURE_TIME",
     "max_rounds": 3, "expected_kind": "answered"},
    # W9: the pointer chase — metric → report links, the 1.51.0
    # backfill built FOR this question; the walk never reached it.
    {"family": "pointer_chase",
     "question": "which dashboards use the ED Sepsis Screening metric?",
     "oracle": "metric_reports", "item": "ED Sepsis Screening",
     "max_rounds": 4, "expected_kind": "answered"},
    # W11: the blend misname — tokens split across two real families;
    # the bridge must name BOTH as did-you-mean.
    {"family": "bridge",
     "question": "how is Sepsis Audit Summary defined",
     "oracle": "blend_bridge", "tokens": ["Audit", "Summary"],
     "max_rounds": 3, "expected_kind": "bridge"},
    # ADR 0054 (build order 2026-08-23): the flag surface as a suite
    # family. requires_table: the fixture SKIPS with a printed notice
    # while the store predates the sweep (disclosed, never silent —
    # the acceptance run happens after Sunny's rerun).
    {"family": "flags",
     "question": "what governance red flags exist?",
     "oracle": "flag_census", "requires_table": "gov_red_flags",
     "max_rounds": 2, "expected_kind": "answered"},
    # W15 (gap-check corpse 2026-08-24, PRE-CAPTURE): the caption
    # inverted a displayed 2-group partition ("aligned"). Graded on
    # DIRECTION — the store derives whether the two metrics' logic
    # truly matches (same content keys) and the answer must carry the
    # verdict word; the inverted caption has zero hits and types
    # dishonest when declared.
    {"family": "sameness",
     "question": "Is Sepsis Encounters' logic identical to "
                 "Sepsis Case Encounters'?",
     "oracle": "compare_direction",
     "items": ["Sepsis Encounters", "Sepsis Case Encounters"],
     "max_rounds": 6, "expected_kind": "answered"},
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
    if kind == "table_readers":
        rows = run_kql(TABLE_USED_BY_QUERY,
                       {"p_phrase": fixture["table"]})
        readers = sorted({
            str(r.get("business_name") or r.get("ref") or "")
            for r in rows
            if str(r.get("table_name") or "").lower()
            == fixture["table"].lower()})
        readers = [r for r in readers if r]
        assert readers, "oracle: table has no readers"
        return {"required_any": [readers],
                "required_overlap": min(2, len(readers)),
                "forbidden": []}
    if kind == "column_filters":
        rows = run_kql(COLUMN_FILTERS_QUERY,
                       {"p_col": fixture["column"]})
        names = sorted({
            str(r.get("business_name") or r.get("ref") or "")
            for r in rows
            if str(r.get("column_name") or "").lower()
            == fixture["column"].lower()})
        names = [n for n in names if n]
        assert names, "oracle: column has no filter sites"
        return {"required_any": [names],
                "required_overlap": min(2, len(names)),
                "forbidden": []}
    if kind == "sameness":
        # Walk W6 (2026-08-23): structural pass conditions, not word
        # oracles — the caveat echo alternatives are fragments of the
        # code-stamped caveat constants, and compare-on-screen is
        # read from the trail (cap.compare_on_screen). The store check
        # only asserts the fixture is non-vacuous: a shared step name,
        # or (W12 pair form) both named items resolvable.
        if fixture.get("items"):
            for item in fixture["items"]:
                ops_i = _fresh_ops_session()
                rs = op_search(item, "exact", run_kql, ops_i)
                assert rs.rows, f"oracle: {item!r} not in catalog"
        else:
            rows = run_kql(STEP_NAME_UNIVERSE_QUERY,
                           {"p_name": fixture["step_name"]})
            n = len({str(r.get("ref")) for r in rows if r.get("ref")})
            assert n >= 2, (f"oracle: step {fixture['step_name']!r} is "
                            "not shared across procs — fixture vacuous")
        return {"required_any": [["not logic sameness", "not compared",
                                  "no comparison", "unverified"]],
                "sameness": True, "forbidden": []}
    if kind == "relationship_claim":
        # W12b/Q4 (2026-08-23): replaced-by assertions require a
        # recorded edge or a compare verdict. Store-derived: while the
        # ADR 0054 relationship edges do not exist, the phrasing
        # itself is a fabrication; once they ship, this branch stops
        # forbidding and starts requiring them.
        n_edges = 0
        rows = run_kql(
            "graph_edges | where edge_type in ('supersedes', "
            "'variant_of', 'duplicate_of') | count", {})
        if rows:
            n_edges = int(rows[0].get("Count", 0) or 0)
        if n_edges:
            return {"required_any": [["supersede", "variant",
                                      "duplicate"]],
                    "sameness": True, "forbidden": []}
        return {"required_any": [["not recorded", "no replacement",
                                  "unverified", "not compared",
                                  "no comparison"]],
                "sameness": True,
                "forbidden": ["replaced by", "succeeded by",
                              "superseded by"]}
    if kind == "column_filters_or_coverage":
        # W13 (2026-08-23): self-adapting. Edges recorded → the
        # column_filters shape; zero recorded → the machine coverage
        # caveat is the only honest answer.
        frows = run_kql(COLUMN_FILTERS_QUERY,
                        {"p_col": fixture["column"]})
        names = sorted({
            str(r.get("business_name") or r.get("ref") or "")
            for r in frows
            if str(r.get("column_name") or "").lower()
            == fixture["column"].lower()})
        names = [n for n in names if n]
        if names:
            # W17 (gap-check corpse 2026-08-24: 11 relation rows read
            # as "11 metrics filter"): the answer must carry a real
            # reader name AND the exact distinct FILTER-metric count
            # the stamp now prints — row counts are not metric counts.
            return {"required_any": [names, [str(len(names))]],
                    "forbidden": []}
        return {"required_any": [["cannot conclude", "not tracked",
                                  "does not prove", "coverage"]],
                "forbidden": []}
    if kind == "metric_reports":
        # W9 pointer chase: the metric's linked reports, from the
        # parsed TMDL consumption layer.
        ops2 = _fresh_ops_session()
        rs = op_search(fixture["item"], "exact", run_kql, ops2)
        assert rs.rows, f"oracle: {fixture['item']} not in catalog"
        rec = op_retrieve([rs.rows[0]["id"]], run_kql, ops2)
        names = sorted({str(r.get("name") or "")
                        for row in rec.rows
                        for r in (row.get("reports") or [])} - {""})
        assert names, f"oracle: {fixture['item']} has no linked reports"
        return {"required_any": [names],
                "required_overlap": 1, "forbidden": []}
    if kind == "compare_direction":
        # W15: the ground truth of "is the logic identical" is the
        # content-key comparison itself, derived from the store —
        # never a hardcoded direction.
        from src.orchestrator.tools import (
            BATCH_FRAGMENTS_QUERY,
            STEPS_OF_QUERY,
            _content_key,
        )
        keysets = []
        for item in fixture["items"]:
            ops_i = _fresh_ops_session()
            rs = op_search(item, "exact", run_kql, ops_i)
            assert rs.rows, f"oracle: {item!r} not in catalog"
            ref = rs.rows[0]["id"]
            step_ids = sorted(
                r["node_id"] for r in run_kql(STEPS_OF_QUERY,
                                              {"p_ref": ref}))
            frags = []
            if step_ids:
                for r in run_kql(BATCH_FRAGMENTS_QUERY,
                                 {"p_ids": json.dumps(step_ids)}):
                    props = r.get("properties") or "{}"
                    if isinstance(props, str):
                        props = json.loads(props)
                    frags.append(_content_key(
                        str(props.get("sql_fragment") or "")))
            keysets.append(tuple(sorted(frags)))
        identical = (len(set(keysets)) == 1 and keysets[0])
        if identical:
            return {"required_any": [["identical", "same"]],
                    "forbidden": []}
        return {"required_any": [["differ", "not identical"]],
                "forbidden": []}
    if kind == "flag_census":
        # ADR 0054: the exact flag count plus at least one recorded
        # class word — both from the store, no hardcoded answers.
        rows = list(run_kql(
            "gov_red_flags | summarize n=count() by flag_class", {}))
        total = sum(int(r.get("n") or 0) for r in rows)
        assert total, "oracle: gov_red_flags is empty"
        classes = sorted(str(r.get("flag_class")) for r in rows)
        return {"required_any": [[str(total)], classes],
                "forbidden": []}
    if kind == "blend_bridge":
        # W11: each token names a real family; the answer must name at
        # least one member of EVERY family.
        ops2 = _fresh_ops_session()
        rs = op_census("metric", run_kql, ops2)
        groups = []
        for tok in fixture["tokens"]:
            grp = sorted({
                str(v) for r in rs.rows
                for v in (r.get("business_name"), r.get("name"))
                if v and tok.lower() in str(v).lower()})
            assert grp, f"oracle: token {tok!r} matches no names"
            groups.append(grp)
        return {"required_any": groups,
                "forbidden": ["no metrics exist"]}
    if kind == "step_count":
        ops2 = _fresh_ops_session()
        rs = op_search(fixture["item"], "exact", run_kql, ops2)
        assert rs.rows, f"oracle: {fixture['item']} not in catalog"
        rec = op_retrieve([rs.rows[0]["id"]], run_kql, ops2)
        n = sum(len(r.get("steps") or []) for r in rec.rows)
        assert n, "oracle: metric has no steps"
        return {"required_any": [[str(n)]], "forbidden": []}
    if kind == "register_step_facts":
        # Walk W5: content facts from the STEP's stored description
        # (the business voice), never its sql_fragment — plus the
        # structural register bar: no SQL code fence in the answer.
        ops2 = _fresh_ops_session()
        rs = op_search(fixture["item"], "exact", run_kql, ops2)
        assert rs.rows, f"oracle: {fixture['item']} not in catalog"
        step_id = f"transform:{rs.rows[0]['id']}:{fixture['step_name']}"
        ops2.note_user(step_id)          # user-named → retrievable
        rec = op_retrieve([step_id], run_kql, ops2)
        assert rec.rows, f"oracle: step {step_id} not found"
        desc = " ".join(str(r.get("step_description")
                            or r.get("description") or "")
                        for r in rec.rows)
        words = sorted(set(_WORD.findall(desc)))
        assert len(words) >= 2, "oracle: step description too thin"
        return {"required_any": [words[:400]], "required_overlap": 2,
                "no_sql_fence": True, "forbidden": []}
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
    if oracle.get("sameness"):
        # Walk W6: caveat echo (counted by the generic loop above) OR
        # a compare result displayed on the trail. Either satisfies;
        # neither + a declared answer falls to the dishonest line
        # below (declared with zero structural facts = the corpse).
        hits = 1 if (hits or verdict.get("compare_on_screen")) else 0
        need = 1
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
    # Walk find 1 (Sunny, 2026-08-21): decision-grade families state
    # the evidence GRAIN they require; the engine computes the grain
    # from what was displayed — an answer from census descriptions
    # cannot satisfy a fixture that demands site rows on screen.
    grain_ok = True
    if fixture.get("expected_grain"):
        grain_ok = (verdict.get("evidence_grain")
                    == fixture["expected_grain"])
    # Walk W5 register bar (2026-08-23): a default-audience answer
    # carrying a SQL code fence fails the family — structural fence
    # detection, no lexicon; sql_request oracles never set the flag.
    register_ok = not (oracle.get("no_sql_fence") and "```" in answer)
    answer_ok = (facts_present and not dishonest and grain_ok
                 and register_ok)
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
                    "evidence_grain": turn.get("evidence_grain", ""),
                    "declared_raw": turn.get("declared_raw", False),
                    "exhausted": turn.get("exhausted", False),
                    # Walk W6: structural signal for the sameness
                    # family — a compare RESULT (not an error chip)
                    # displayed on this trail's final turn
                    "compare_on_screen": any(
                        (o.get("component") or {}).get("op") == "compare"
                        and o.get("result")
                        for o in turn["outputs"]),
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


# Pin bumped CONSCIOUSLY 2026-08-21 (walk find 4, recorded in the
# Round-4 RESULTS log): ENGINE_TOOLS gained the `lineage` tool — the
# readers-of-table primitive. SYSTEM_PROMPT unchanged.
# Pin bumped CONSCIOUSLY 2026-08-23 (walk W7, HANDOFF_WALK_1562_FINDS
# priority 1c, recorded in the goal-file RESULTS): the `compare` tool
# description gained one semantics sentence — compare is the ONLY
# basis for a sameness/difference verdict; names/mentions/descriptions
# never establish sameness. Tool-semantics text, not a question shape
# (the 1.50.1 class). SYSTEM_PROMPT unchanged.
# Pin bumped CONSCIOUSLY 2026-08-23 (ADR 0054 build,
# HANDOFF_0054_BUILD RESULTS): census kind enum gained 'flag' plus a
# tool-property sentence (the sweep's machine verdicts; flags
# disclose, never gate). SYSTEM_PROMPT unchanged.
PINNED_PROMPT_SHA = ("d9f8df5ce81cfe086542cb04768df410"
                     "1e2a6afe21783b640eeda1f20507e027")


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
    infra_skipped: "list[tuple]" = []
    stop_build = False
    for fixture in FIXTURES:
        # ADR 0054: a fixture may declare a store table it cannot run
        # without — SKIP is disclosed, never silent, and the family
        # prints as pending so the board can't read as covered.
        req = fixture.get("requires_table")
        if req:
            try:
                run_kql(f"{req} | count", {})
            except Exception:                   # noqa: BLE001 — absent
                print(f"[{fixture['family']}] SKIPPED — required table "
                      f"{req!r} not in the store yet (pending the "
                      "pipeline run that writes it)")
                continue
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
            try:
                turn = run_trail(trail_prefix + [q], chat_api, run_kql)
            except requests.RequestException as e:
                # persistent TRANSPORT failure (already retried 3x in
                # azure_chat_api): skip THIS question loudly instead
                # of killing the whole run (2026-08-22: a ~6-minute
                # OpenAI outage crashed a 40-minute suite at question
                # 37). Only transport errors qualify — anything else
                # is an engine bug and must still raise. No silent
                # caps: skips are counted per family in the board and
                # dump, and >20% of attempted questions aborts (infra).
                infra_skipped.append(
                    (fixture["family"], q, type(e).__name__))
                _dump.append({"family": fixture["family"], "question": q,
                              "infra_skip": type(e).__name__})
                print(f"[{fixture['family']}] INFRA-SKIP "
                      f"{type(e).__name__} :: {q[:60]}")
                graded_n = sum(len(v) for v in families.values())
                if infra_abort(len(infra_skipped), graded_n):
                    print(f"\n[X] INFRA ABORT: {len(infra_skipped)} of "
                          f"{len(infra_skipped) + graded_n} attempted "
                          "questions lost to transport — the surviving "
                          "grades no longer describe the engine. "
                          "Partial grades discarded.")
                    raise SystemExit(3)
                continue
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
        if d.get("grade")
        and d["grade"]["declared_answered"]
        and not d["grade"]["answer_ok"]
        and any("the step records" in (o.get("headline") or "")
                for o in d.get("outputs") or []))
    print(f"(telemetry, M2) stamp-contradicting declarations: "
          f"{stamp_contra}")

    # Telemetry (walk W1, 2026-08-23, MEASURED only): rounds-beyond-
    # sufficient — an answered turn whose caption cites refs from
    # earlier rounds but nothing from its final round: the last round
    # bought latency, not evidence (Q1's 11-record retrieve; Q8's
    # re-retrieve of an on-screen record). Heuristic, never a gate.
    _ref_head = re.compile(r"(R\d+):")
    rounds_beyond = 0
    for d in _dump:
        g = d.get("grade")
        if not g or not g.get("declared_answered"):
            continue
        outs = d.get("outputs") or []
        by_round: "dict[int, set]" = {}
        for o in outs:
            rd = (o.get("component") or {}).get("auto_round") or 0
            m = _ref_head.match(str(o.get("headline") or ""))
            if m:
                by_round.setdefault(rd, set()).add(m.group(1))
        if len(by_round) < 2:
            continue
        last = max(by_round)
        cap_text = str((d.get("caption") or {}).get("caption") or "")
        earlier = set().union(*(v for k, v in by_round.items()
                                if k != last))
        if (any(ref in cap_text for ref in earlier)
                and not any(ref in cap_text for ref in by_round[last])):
            rounds_beyond += 1
    print(f"(telemetry, W1) rounds-beyond-sufficient: {rounds_beyond}")

    skips_by_family: "dict[str, int]" = {}
    for fam, _q, _t in infra_skipped:
        skips_by_family[fam] = skips_by_family.get(fam, 0) + 1

    print("\n=== scorecard ===")
    all_pass = True
    for family, grades in families.items():
        n = len(grades)
        answer_rate = sum(1 for g in grades if g["answer_ok"]) / n
        honesty = 1.0 - sum(1 for g in grades if g["dishonest"]) / n
        ok = answer_rate >= ANSWER_RATE_THRESHOLD and honesty == 1.0
        all_pass &= ok
        skip_note = (f" skipped={skips_by_family[family]}"
                     if family in skips_by_family else "")
        print(f"{family:12s} answer_rate={answer_rate:.2f} "
              f"honesty={honesty:.2f} n={n}{skip_note} "
              f"{'PASS' if ok else 'BELOW THRESHOLD'}")
    # a family every question of which was skipped has no grades row —
    # it must still appear (a silent-cap would read as 'covered')
    for family, n_skip in skips_by_family.items():
        if family not in families:
            print(f"{family:12s} ALL {n_skip} question(s) INFRA-SKIPPED "
                  "— no grades")
            all_pass = False
    if stop_build:
        print("\n[X] DISHONEST turn observed — build-stopper, not a metric.")
        raise SystemExit(2)
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
