"""Phase 11 tiered-seats contract tests
(AIVIA_01_Design/11_tiered_seats.md D1-D8 + its data contract,
drafted 2026-10-09; pseudo APPROVED same day).

Written test-first: RED until business_descriptions grows the two
seats, the escalation ladder, the run meter and AccountRefusal;
business_terms rides the same ladder; sqldesc_cli refuses an
empty ledger by name and lands the run scorecard.

DETERMINISTIC — no LLM, no network, no cost. Callers, voicers and
proposers are injected or monkeypatched; synthetic fixtures carry
invented names only (the estate boundary).
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
sys.path.insert(0, str(CODE_DIR))

import business_descriptions as bd  # noqa: E402
import business_terms as bt  # noqa: E402
import sqldesc_cli  # noqa: E402

LEDGER = "10_corpus_ledger_output.json"
LEDGER_OLD = "10_corpus_ledger.json"
SCORECARD = "14_run_scorecard_output.json"
SCORECARD_TXT = "14_run_scorecard_output.txt"

# The field fixtures of the standing 07 suite (the 17-tooltips
# find): a dict docket, a known-passing and known-failing text.
FIELD_DOCKET = {"facts": "FIELD: the room name", "text": "x"}
FIELD_PASS = "Shows the room name for each census event."
FIELD_FAIL = ("**Department**: the department.\n"
              "**Time window**: includes events.")
REG = {"names": [], "sentences": []}


# ------------------------------------------- D1: the two seats

def test_two_seats_and_price_card_pinned():
    assert bd._MODEL_LARGE == "gpt-5.4"
    assert bd._MODEL_SMALL == "gpt-5.4-mini"
    assert set(bd._PRICE_CARD) == {bd._MODEL_LARGE, bd._MODEL_SMALL}
    for card in bd._PRICE_CARD.values():
        assert set(card) == {"input_per_1m", "output_per_1m"}


def test_seat_map_by_grain():
    m = bd._SEAT_BY_GRAIN
    assert m["file"] == bd._MODEL_LARGE
    assert m["scope"] == bd._MODEL_LARGE
    assert m["term_card"] == bd._MODEL_SMALL
    assert m["field"] == bd._MODEL_SMALL


# ------------------------------- D3: the escalation ladder (07)

def test_field_card_escalates_on_round3_and_meter_counts():
    bd.reset_meter()
    seats = []

    def caller(prompt, seat):
        seats.append(seat)
        return FIELD_FAIL if len(seats) < 3 else FIELD_PASS

    text, status, findings, used = bd._propose_loop(
        "field", "DOCKET", FIELD_DOCKET, REG, caller=caller)
    assert status == "gate_passed" and used == 3
    assert seats == [bd._MODEL_SMALL, bd._MODEL_SMALL,
                     bd._MODEL_LARGE]
    m = bd.meter()
    assert m["escalations"] == {"fired": 1, "landed": 1}
    assert m["rounds"]["3"] == 1
    assert sum(m["causes"].values()) == 2  # two failed rounds


def test_file_card_stays_large_no_escalation():
    bd.reset_meter()
    seats = []

    def caller(prompt, seat):
        seats.append(seat)
        return "zzz."  # never a lawful file card

    text, status, findings, used = bd._propose_loop(
        "file", "DOCKET", {"facts": "x", "text": "x"}, REG,
        caller=caller)
    # 0.11.0: the exhausted card SHIPS (text exists) — findings
    # registered, never a block; the seat ladder is unchanged
    assert status == "gate_failed" and text == "zzz."
    assert findings                    # the register
    assert seats == [bd._MODEL_LARGE] * 3
    assert bd.meter()["escalations"] == {"fired": 0, "landed": 0}


def test_one_arg_caller_still_valid():
    """The standing suite injects caller(prompt) — the ladder
    must not break that contract."""
    text, status, findings, used = bd._propose_loop(
        "field", "DOCKET", FIELD_DOCKET, REG,
        caller=lambda prompt: FIELD_PASS)
    assert status == "gate_passed" and used == 1


def test_basis_gap_exits_round1_never_escalates():
    """0.10.0 amendment: a basis gap still never repairs and
    never escalates — but it SHIPS (number shown, question
    open) instead of blocking (D3 as amended 2026-10-10)."""
    bd.reset_meter()
    seats = []

    def caller(prompt, seat):
        seats.append(seat)
        return "The value 999 applies."  # 999 has no stored basis

    text, status, findings, used = bd._propose_loop(
        "field", "DOCKET", FIELD_DOCKET, REG, caller=caller)
    assert status == "gate_passed" and used == 1
    assert "999" in text               # shown, not blocked
    assert bd.last_questions()         # the open question
    assert seats == [bd._MODEL_SMALL]
    assert bd.meter()["escalations"]["fired"] == 0


def test_rows_record_the_actual_seat(tmp_path, monkeypatch):
    """D4: row model = the seat of the last attempt — SMALL for a
    round-1 field exit, LARGE for file/scope."""
    DIR05 = REPO_ROOT / "AIVIA_01_Data" / "05_semantic_graph"
    DIR06 = REPO_ROOT / "AIVIA_01_Data" / "06_technical_descriptions"
    DIR02 = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
    LOTE = ("Reporting_USP_CCMC_LOTE_Census_Interpreter_"
            "Services_Detail_PBI")
    monkeypatch.setattr(
        bd, "_openai_caller",
        lambda prompt, seat=None: "The value 999 applies.")
    out = tmp_path / "out07"
    out.mkdir()
    rows = bd.build07(DIR05, DIR06, out, DIR02, no_llm=False,
                      only_file=LOTE)
    by_grain = {}
    for r in rows:
        by_grain.setdefault(r["grain"], set()).add(r["model"])
    assert by_grain["file"] == {bd._MODEL_LARGE}
    assert by_grain.get("scope", {bd._MODEL_LARGE}) \
        == {bd._MODEL_LARGE}
    if "field" in by_grain:  # round-1 exits never escalate
        assert by_grain["field"] == {bd._MODEL_SMALL}


# --------------------------- D6b: the account refusal (the Echo)

def test_account_refusal_detection_is_precise():
    class AuthenticationError(Exception):
        pass

    class RateLimitError(Exception):
        pass

    with pytest.raises(bd.AccountRefusal) as e:
        bd._check_account_refusal(
            AuthenticationError("Error code: 401 - bad key"))
    assert "key" in str(e.value)
    with pytest.raises(bd.AccountRefusal) as e:
        bd._check_account_refusal(RateLimitError(
            "Error code: 429 - insufficient_quota: no credits"))
    assert "credit" in str(e.value)
    # a PLAIN rate limit stays a failed round, never a dead batch
    assert bd._check_account_refusal(
        RateLimitError("Rate limit exceeded, retry soon")) is None
    assert bd._check_account_refusal(RuntimeError("boom")) is None


def test_account_refusal_rises_through_the_loop():
    def caller(prompt, seat):
        raise bd.AccountRefusal("fix refusal")

    with pytest.raises(bd.AccountRefusal):
        bd._propose_loop("file", "DOCKET", {"facts": "x"}, REG,
                         caller=caller)


def test_account_refusal_rises_through_voices(tmp_path):
    def voicer(fact, seat):
        raise bd.AccountRefusal("fix refusal")

    with pytest.raises(bd.AccountRefusal):
        bd.voice_facts(
            [("k1", "the category is 'Lucky' (7)")],
            tmp_path / "07_business_descriptions_fact_voices_output.json",
            {"sentences": []}, voicer=voicer)


# ----------------------------------- D3: the voice retry ladder

def test_voice_small_then_one_large_retry(tmp_path):
    calls = []

    def voicer(fact, seat):
        calls.append(seat)
        if seat == bd._MODEL_SMALL:
            return "the category is 'Lucky' (8)"  # foreign value
        return "the category is 'Lucky' (7)"

    store = (tmp_path /
             "07_business_descriptions_fact_voices_output.json")
    v = bd.voice_facts([("k1", "the category is 'Lucky' (7)")],
                       store, {"sentences": []}, voicer=voicer)
    assert calls == [bd._MODEL_SMALL, bd._MODEL_LARGE]
    entry = json.loads(store.read_text())["k1"]
    assert entry["status"] == "proposed"
    assert entry["model"] == bd._MODEL_LARGE
    assert v["k1"] == "the category is 'Lucky' (7)"


def test_voice_one_arg_voicer_unchanged(tmp_path):
    """The standing 1-arg voicer contract: no retry, the machine
    fact stands when the voice fails its gate."""
    store = (tmp_path /
             "07_business_descriptions_fact_voices_output.json")
    v = bd.voice_facts(
        [("k1", "the category is 'Lucky' (7)")], store,
        {"sentences": []},
        voicer=lambda fact: "the category is 'Lucky' (8)")
    assert v["k1"] == "the category is 'Lucky' (7)"
    assert json.loads(store.read_text())["k1"]["status"] == "failed"


# ------------------------------------- the 09 arm of the ladder

def test_terms_spec_carries_round_and_seat_recorded():
    rounds_seen = []

    def proposer(spec):
        rounds_seen.append(spec.get("round"))
        return {"bt_name": "Fix",
                "business_description": "zzz not a lawful card",
                "_seat": bd._MODEL_SMALL}

    prop, status, findings, used, seat = bt._propose(
        proposer, "fix::scope/x", "fix docket")
    assert rounds_seen == [1, 2, 3]
    assert status == "gate_failed" and used == 3
    assert seat == bd._MODEL_SMALL


def test_term_proposer_seats_by_the_ladder(monkeypatch):
    seats = []
    monkeypatch.setattr(
        bd, "_openai_caller",
        lambda prompt, seat=None: seats.append(seat)
        or "NAME: Fix\nDefinition: a fix definition")
    out1 = bt._openai_proposer(
        {"node_id": "n", "docket": "d", "findings": [], "round": 1})
    out3 = bt._openai_proposer(
        {"node_id": "n", "docket": "d", "findings": [], "round": 3})
    assert seats == [bd._MODEL_SMALL, bd._MODEL_LARGE]
    assert out1["_seat"] == bd._MODEL_SMALL
    assert out3["_seat"] == bd._MODEL_LARGE


def test_account_refusal_rises_through_terms():
    def proposer(spec):
        raise bd.AccountRefusal("fix refusal")

    with pytest.raises(bd.AccountRefusal):
        bt._propose(proposer, "fix::scope/x", "fix docket")


# ------------------------------- D6a: the empty-ledger refusal

def _corpus(tmp_path, names=("fix_a.sql", "fix_b.sql", "fix_c.sql")):
    sql = tmp_path / "sql"
    sql.mkdir(exist_ok=True)
    for n in names:
        (sql / n).write_text(f"SELECT 1 -- {n}\n")
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    return sql, out


def _tmdl_one(tmp_path):
    d = (tmp_path / "tmdl" / "Fix Model.SemanticModel" /
         "definition" / "tables")
    d.mkdir(parents=True)
    (d / "T.tmdl").write_text(
        "table T\n\n\tcolumn Fix Col\n"
        "\t\tsourceColumn: Fix Col\n\n"
        "\tpartition p1 = m\n\t\tmode: import\n\t\tsource =\n"
        '\t\t\tlet q = Value.NativeQuery(db,\n'
        '\t\t\t"EXEC rpt.FIX_A") in q\n')
    return tmp_path / "tmdl"


def test_empty_ledger_refuses_by_name(tmp_path):
    sql, out = _corpus(tmp_path)
    (out / LEDGER).write_text("")
    with pytest.raises(ValueError) as e:
        sqldesc_cli.plan_corpus(sql, out)
    msg = str(e.value)
    assert LEDGER in msg and "empty or unreadable" in msg
    assert "JSONDecodeError" not in msg


def test_empty_old_ledger_refuses_not_bypassed(tmp_path):
    """The 2026-10-09 field find verbatim: a 0-byte OLD-name
    ledger must refuse by name, never die as a bare
    JSONDecodeError, never be silently skipped."""
    sql, out = _corpus(tmp_path)
    (out / LEDGER_OLD).write_text("")
    with pytest.raises(ValueError) as e:
        sqldesc_cli.plan_corpus(sql, out)
    assert LEDGER_OLD in str(e.value)
    assert "empty or unreadable" in str(e.value)


def test_unparseable_ledger_refuses_too(tmp_path):
    sql, out = _corpus(tmp_path)
    (out / LEDGER).write_text("not json at all {")
    with pytest.raises(ValueError) as e:
        sqldesc_cli.plan_corpus(sql, out)
    assert "empty or unreadable" in str(e.value)


# ----------------------------------- D8: the run scorecard

SC_KEYS = {"files", "status_counts", "failure_causes", "rounds",
           "escalations", "awaiting", "questions", "timings_s",
           "seats", "price_card", "_law"}
TIMING_KEYS = {"cards_file_scope", "cards_field", "fact_voices",
               "business_terms", "delivery_assembly", "total"}


def _described(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fix-dummy-key")
    monkeypatch.setattr(
        bd, "_openai_caller",
        lambda prompt, seat=None: "The value 999 applies.")
    sql, out = _corpus(tmp_path)
    tmdl = _tmdl_one(tmp_path)
    sqldesc_cli.build(tmdl, sql, out)
    sqldesc_cli.describe(tmdl, sql, out)
    return out


def test_scorecard_lands_shaped_and_conserved(tmp_path,
                                              monkeypatch):
    out = _described(tmp_path, monkeypatch)
    sc = json.loads((out / SCORECARD).read_text())
    assert set(sc) == SC_KEYS
    assert sc["files"]["described_this_run"] == 3
    assert sc["files"]["remaining"] == 0
    assert set(sc["timings_s"]) == TIMING_KEYS
    assert all(v >= 0 for v in sc["timings_s"].values())
    assert set(sc["rounds"]) == {"round_1", "round_2", "round_3"}
    # conservation: the sheet rows all counted, awaiting matches
    rows = json.loads((out / "07_business_descriptions" /
                       "07_business_descriptions_output.json")
                      .read_text())
    counted = sum(n for g in ("file", "scope", "field")
                  for n in sc["status_counts"].get(g, {}).values())
    assert counted == len(rows)
    awaiting_n = sum(
        sc["status_counts"].get(g, {}).get("awaiting_human", 0)
        for g in ("file", "scope", "field"))
    assert len(sc["awaiting"]) == awaiting_n
    # 0.11.0 (the uniform ship): every card has text, so NOTHING
    # awaits — the file cards exhaust on the five-line template
    # and ship as gate_failed with their findings registered;
    # the 999 basis gap ships with an open question
    assert sc["awaiting"] == []
    failed_n = sum(
        sc["status_counts"].get(g, {}).get("gate_failed", 0)
        for g in ("file", "scope", "field"))
    assert failed_n >= 1, "the template-exhausted file cards"
    shown_n = sum(
        sc["status_counts"].get(g, {})
        .get("delivered_with_questions", 0)
        for g in ("file", "scope", "field"))
    assert shown_n >= 1, "the 999 fixture must ship shown"
    qs = sc["questions"]
    assert set(qs) == {"open", "closed_this_run", "by_closure"}
    assert set(qs["by_closure"]) == {"comment", "answer",
                                     "dictionary", "show",
                                     "omit", "bless", "accept"}
    import csv
    with open(out / "07_business_descriptions" /
              bd.ANSWERS_NAME, newline="") as fh:
        open_rows = [r for r in csv.DictReader(fh)
                     if r["status"] == "open"]
    assert qs["open"] == len(open_rows) >= 1
    assert qs["closed_this_run"] == sum(qs["by_closure"].values())
    assert sc["escalations"]["fired"] >= sc["escalations"]["landed"]
    assert sc["failure_causes"] == sorted(
        sc["failure_causes"], key=lambda c: -c["count"])
    assert sc["price_card"] == bd._PRICE_CARD
    assert (out / SCORECARD_TXT).exists()


def test_scorecard_txt_is_the_honest_eye(tmp_path, monkeypatch):
    out = _described(tmp_path, monkeypatch)
    txt = (out / SCORECARD_TXT).read_text()
    assert "usd" in txt            # the money line always renders
    assert "round" in txt.lower()
    # 0.10.0: the questions block renders for her eye
    assert "questions" in txt.lower()
    assert "open" in txt.lower()
    # 0.11.0: nothing awaits (every card has text); the open
    # items' one home is the answers csv, counted here
    assert "gate_failed" in txt


def test_scorecard_txt_unpriced_renders_honest():
    """An unpriced seat says so — a dollar figure is never
    invented (the price-card law)."""
    sc = {"files": {"described_this_run": 0, "already_done": 0,
                    "remaining": 0},
          "status_counts": {}, "failure_causes": [],
          "rounds": {"round_1": 0, "round_2": 0, "round_3": 0},
          "escalations": {"fired": 0, "landed": 0},
          "awaiting": [],
          "questions": {"open": 0, "closed_this_run": 0,
                        "by_closure": {"comment": 0, "answer": 0,
                                       "dictionary": 0, "show": 0,
                                       "omit": 0, "bless": 0,
                                       "accept": 0}},
          "timings_s": {"total": 0.0},
          "seats": {"fix-seat": {"calls": 1, "input_tokens": 9,
                                 "output_tokens": 9, "usd": None}},
          "price_card": {}, "_law": "fix"}
    txt = sqldesc_cli._scorecard_txt(sc)
    assert "unpriced" in txt


def test_account_refusal_describe_records_nothing(tmp_path,
                                                  monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fix-dummy-key")
    sql, out = _corpus(tmp_path)
    tmdl = _tmdl_one(tmp_path)
    sqldesc_cli.build(tmdl, sql, out)

    def refusing(prompt, seat=None):
        raise bd.AccountRefusal("the seat refused the account "
                                "(fix): add credits")

    monkeypatch.setattr(bd, "_openai_caller", refusing)
    with pytest.raises(bd.AccountRefusal):
        sqldesc_cli.describe(tmdl, sql, out)
    assert not (out / LEDGER).exists()
    assert not (out / "12_ai_delivery_output.json").exists()
    assert not (out / SCORECARD).exists()
    assert not (out / "07_business_descriptions" /
                "07_business_descriptions_output.json").exists()
