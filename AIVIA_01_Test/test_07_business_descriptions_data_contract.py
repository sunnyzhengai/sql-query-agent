"""Phase 07 contract tests
(AIVIA_01_Design/07_business_descriptions_data_contract.md,
APPROVED 2026-10-03).

Written test-first: RED until business_descriptions.py exposes
the gate, the prompt constructor, the effective ladder and
build07. DETERMINISTIC end to end — the fixtures below are the
dry run's RECORDED REAL model outputs (14 paid gpt-5-mini calls,
2026-10-03, verbatim in dryruns/phase_II_uses_phase_I.md);
recorded real speech replayed as data is not a fake call. The
live proposer path belongs to the build command only.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
DIR05 = REPO_ROOT / "AIVIA_01_Data" / "05_semantic_graph"
DIR06 = REPO_ROOT / "AIVIA_01_Data" / "06_technical_descriptions"
DIR02 = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"

sys.path.insert(0, str(CODE_DIR))
import business_descriptions as bd  # noqa: E402

LOTE = "Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_Detail_PBI"


def _scope_docket():
    """The real docket for the #caregiver_languages scope, read
    from the TRACKED 06 sheet (never hardcoded — the gate trusts
    stored rows, so the fixtures must too)."""
    rows = json.loads((DIR06 / "06_description_sheet.json")
                      .read_text())
    sent = next(r["sentence"] for r in rows if r["node_id"]
                .endswith(LOTE + "::scope/#caregiver_languages"))
    return sent


# The dry run's RECORDED REAL outputs (provenance: dryruns doc).
ROUND2_FIELD_FABRICATION = (
    "For each patient, Caregiver Languages shows the spoken "
    "languages recorded for that patient's caregiver contacts "
    "whose relationship either overlaps the report's configurable "
    "date window or has no dates entered. When multiple languages "
    "apply, the values combine into a single text list with ';' "
    "as the separator.")
ROUND4_SCOPE_BANNED_AND_CODE = (
    "It selects patient contacts where patient contact language "
    "is 1. It includes relationships with dates overlapping a "
    "configurable window or with no dates.")
ROUND5_FIELD_CLEAN = (
    "Caregiver Languages lists languages recorded for each "
    "patient's caregiver contact marked as spoken language. It "
    "includes caregiver contacts active during the report window "
    "or lacking relationship dates.")
ROUND5_FILE_CLEAN = (
    "Who's in it: Patients present in the combined monthly census "
    "and clinic monthly selections.\n"
    "Each row shows: demographics, caregiver languages, coverage "
    "and payor, age, and census context.\n"
    "Time window: a configurable date window\n"
    "Excludes: patients with an English-speaking caregiver; "
    "patients with no recorded caregiver language when the "
    "patient language is English")


# ------------------------------------------------ the gate (G-*)

def test_gate_kills_the_recorded_semicolon_fabrication():
    """THE PINNED REGRESSION: the round-2 fabrication that
    survived prompt rules dies here forever (G-1, token named)."""
    findings = bd.gate(ROUND2_FIELD_FABRICATION, _scope_docket(),
                       "field")
    assert findings
    assert any("separator" in f or "';'" in f for f in findings)


def test_gate_passes_the_round5_clean_field():
    assert bd.gate(ROUND5_FIELD_CLEAN, _scope_docket(),
                   "field") == []







def test_prompt_constructor_is_deterministic_and_example_free():
    p1 = bd.build_prompt("field", "DOCKET TEXT", [])
    p2 = bd.build_prompt("field", "DOCKET TEXT", [])
    assert p1 == p2
    assert "DOCKET TEXT" in p1
    # the prompt-examples-are-data law: no concrete sample
    # sentences ride in any prompt
    assert "Lucky" not in p1 and "caregiver" not in p1.lower()


def test_repair_prompt_carries_the_named_objections():
    p = bd.build_prompt("field", "DOCKET TEXT",
                        ["G-1: 'separator' has no stored basis"])
    assert "separator" in p


# --------------------------------- the effective ladder + build

def test_effective_ladder_blessed_beats_gate_passed_beats_floor():
    row = {"node_id": "n1", "audience_text": "proposed words",
           "status": "gate_passed"}
    registry = {"sentences": [{"node_id": "n1",
                               "blessed_text": "her words",
                               "ruling": "RULED"}], "names": []}
    assert bd.effective(row, registry) == "her words"
    assert bd.effective(row, {"sentences": [], "names": []}) \
        == "proposed words"
    floor_row = {"node_id": "n2", "audience_text": "the floor",
                 "status": "floor"}
    assert bd.effective(floor_row, {"sentences": [], "names": []}
                        ) == "the floor"


def test_live_harness_checkpoints_resumes_and_reports(tmp_path,
                                                      capsys):
    """The 2026-10-03 first-failure build (Echo Law): a run that
    dies mid-flight loses nothing — the checkpoint holds every
    completed node, the rerun resumes without re-paying, progress
    is printed per node. Deterministic stand-in proposer: tests
    the PLUMBING, never model speech."""
    out = tmp_path / "07"
    out.mkdir()
    calls = []

    class Boom(Exception):
        pass

    def dying_proposer(grain, docket_text, docket, registry):
        calls.append(grain)
        if len(calls) >= 5:
            raise Boom()
        return "stub", "gate_passed", [], 1

    try:
        bd.build07(DIR05, DIR06, out, DIR02, no_llm=False,
                   proposer=dying_proposer)
    except Boom:
        pass
    ck = json.loads((out / "07_live_checkpoint.json").read_text())
    assert len(ck) == 4  # the completed nodes survived the death

    calls.clear()

    def steady_proposer(grain, docket_text, docket, registry):
        calls.append(grain)
        return "stub", "gate_passed", [], 1

    bd.build07(DIR05, DIR06, out, DIR02, no_llm=False,
               proposer=steady_proposer)
    rows = json.loads((out / "07_business_sheet.json").read_text())
    assert len(rows) == 151
    assert len(calls) == 151 - 4   # resume never re-pays
    assert not (out / "07_live_checkpoint.json").exists()
    assert "[5/151]" in capsys.readouterr().out  # progress lines


def test_floor_rows_keep_the_rejected_card(tmp_path):
    """Her ruling 2026-10-03: a floor row carries the last
    REJECTED proposal so she can see what wanted saying."""
    out = tmp_path / "07"
    out.mkdir()

    def failing_proposer(grain, docket_text, docket, registry):
        return ("the rejected words", "floor",
                ["G-1: 'rejected' has no stored basis"], 3)

    rows = bd.build07(DIR05, DIR06, out, DIR02, no_llm=False,
                      proposer=failing_proposer, only_file=LOTE)
    r = rows[0]
    assert r["status"] == "floor"
    assert r["last_proposal"] == "the rejected words"
    assert r["audience_text"] != "the rejected words"  # floor ships


def test_api_failure_floors_the_node_never_crashes():
    """The re-propose crash find (2026-10-03): a timed-out call
    is a failed round, never a dead build."""
    def dying_caller(prompt):
        raise TimeoutError("boom")
    text, status, findings, used = bd._propose_loop(
        "field", "docket", "docket", {"names": [],
                                      "sentences": []},
        caller=dying_caller)
    assert status == "floor"
    assert any("call failed" in f for f in findings)
    assert used == bd.REPAIR_BUDGET


def test_dockets_carry_the_table_descriptions():
    """Her find 2026-10-03: the dictionary described CLARITY_ADT
    all along — the docket must carry it (and the whitelist
    grounds on it)."""
    fname = ("COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_"
             "TOTALS_SSRS")
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, fname)
    assert "master table for ADT event history" in docket["text"]
    # and the words become sayable: 'ADT', 'history' now ground
    findings = bd.gate("Rows are ADT event history records.",
                       docket, "scope")
    assert not any("'adt'" in f.lower() or "'history'" in f
                   for f in findings)



RUN7_FILE_CLEAN = (
    "One row is: one census ADT event for one patient at one "
    "effective date and time, representing where that patient "
    "was counted for inpatient census purposes.\n"
    "Who's in it: patients with a recorded patient identifier "
    "whose census event falls within the requested date range, "
    "existed in the data as of the requested as-of date, matched "
    "the separate service area and location selections, and were "
    "assigned to a unit other than CCMC EMERGENCY, CCMC IR "
    "IMAGING, CCMC CATH LAB, CCMC MAIN OR, CCMC SPA OR, CCMC PHP "
    "PSYCHIATRY, CCMC CARDIOVASCULAR OR, or DSC OR.\n"
    "Each row shows: the census event status, when it occurred, "
    "the patient and visit classification, the patient's assigned "
    "care location, and the related service area information.\n"
    "Time window: the report includes census events whose event "
    "time is from the start date through the end date inclusive, "
    "shown as the data stood at the end of the as-of date.\n"
    "Excludes: records without a patient identifier, records "
    "outside the selected service area or location filters, and "
    "events tied to the excluded units.")

TOTALS = "COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS"


def test_gate_v2_passes_the_recorded_run7_card():
    """The RECORDED run-7 card (gpt-5.4, 2026-10-03) is the
    quality bar: it must pass Gate v2 untouched."""
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, TOTALS)
    assert bd.gate(RUN7_FILE_CLEAN, docket, "file") == []


def test_gate_v2_template_and_register():
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, TOTALS)
    prose = "This dataset shows monthly census patients."
    f = bd.gate(prose, docket, "file")
    assert any("template" in x.lower() for x in f)
    f2 = bd.gate("It selects records with language 99.",
                 "nothing relevant", "scope")
    assert any("select" in x.lower() for x in f2)   # V-3
    assert any("99" in x for x in f2)               # V-1


def test_ungrounded_number_lands_a_sighting():
    bd.reset_sightings()
    bd.gate("The category is 777 here.", "no numbers stored",
            "scope")
    assert any(s["code"] == "777" for s in bd.code_sightings())


def test_domain_knowledge_is_free_estate_facts_are_not():
    """Her ruling: 'this is why we use LLM.' Domain phrasing
    passes with no docket basis; never-list claim words die on
    exact token."""
    ok = bd.gate("Represents where the patient was counted for "
                 "inpatient census purposes.", "irrelevant",
                 "scope")
    assert ok == []
    dead = bd.gate("The intended purpose is a formatted export.",
                   "irrelevant", "scope")
    assert any("'intended'" in x for x in dead)
    assert any("'purpose'" in x for x in dead)
    assert any("'formatted'" in x for x in dead)


def test_kinds_backstop_names_the_appendix():
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, TOTALS)
    listy = RUN7_FILE_CLEAN.replace(
        "the census event status, when it occurred, the patient "
        "and visit classification, the patient's assigned care "
        "location, and the related service area information",
        "a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p")
    f = bd.gate(listy, docket, "file")
    assert any("appendix" in x for x in f)


def test_must_say_the_gap_on_the_dynamic_file():
    fname = "Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_SSRS"
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, fname)
    no_gap = ("One row is: a census day count.\n"
              "Who's in it: monthly census records.\n"
              "Each row shows: census day counts.\n"
              "Time window: a configurable date window\n"
              "Excludes: none stated")
    f = bd.gate(no_gap, docket, "file")
    assert any("gap" in x.lower() for x in f)


def test_call_timeout_is_law():
    assert bd.CALL_TIMEOUT_S == 120




def test_single_file_build_scope(tmp_path):
    out = tmp_path / "07"
    out.mkdir()
    rows = bd.build07(DIR05, DIR06, out, DIR02, no_llm=True,
                      only_file=LOTE)
    assert rows
    assert all(r["node_id"].split("::")[1] == LOTE or
               r["node_id"] == f"file::{LOTE}" for r in rows)
    texts = [p.name for p in out.iterdir()
             if p.name.endswith(".txt")
             and not p.name.endswith(".facts.txt")]
    assert texts == [f"{LOTE}.txt"]
    assert (out / f"{LOTE}.facts.txt").exists()  # docket v2


def test_no_llm_build_conserves_and_registry_stays_untouched(
        tmp_path):
    out = tmp_path / "07"
    out.mkdir()
    reg = out / "07_blessing_registry.json"
    reg.write_text(json.dumps({"names": [], "sentences": []}))
    before = reg.read_bytes()
    bd.build07(DIR05, DIR06, out, DIR02, no_llm=True)
    rows = json.loads((out / "07_business_sheet.json").read_text())
    assert rows and all(r["status"] == "floor" for r in rows)
    # conservation: one row per docket node (file+scope+field)
    assert len(rows) == len({r["node_id"] for r in rows})
    assert {r["grain"] for r in rows} == {"file", "scope",
                                          "field"}
    assert reg.read_bytes() == before  # Sunny's hand only
    texts = [p for p in out.iterdir()
             if p.name.endswith(".txt")
             and not p.name.endswith(".facts.txt")]
    assert len(texts) == 8
    facts = [p for p in out.iterdir()
             if p.name.endswith(".facts.txt")]
    assert len(facts) == 8  # docket v2's tracked FACTS


def test_prompt_carries_s12_to_s14():
    """RULED 2026-10-04 (her six verbiage findings): relevance
    ranking, plain diction, prompts-as-choices, one home per
    fact — prompt law, zero lists."""
    p = bd.build_prompt("file", "DOCKET", [])
    assert "housekeeping" in p.lower() or "data-quality" in p.lower()
    assert "chosen when running the report" in p
    assert "means \"All\"" in p or "means 'All'" in p
    assert "plain connectors" in p.lower()
    assert "speaks once" in p.lower() or "one home" in p.lower()


# ------------- DOCKET v2 + the fact-voice layer (red first)

def test_facts_block_is_bound_truth_only():
    """The EMH-class impossibility: FACTS carries the eight
    bound department exclusions with meanings; code 0 appears
    ONLY as the multi-select All value, never as a department."""
    facts, items = bd.render_facts(DIR05, DIR06, DIR02, TOTALS)
    assert "CCMC EMERGENCY" in facts and "DSC OR" in facts
    assert "'Census' (6)" in facts or "Census" in facts
    assert "EMH OVERFLOW" not in facts
    assert items  # (fact_key, machine_fact) pairs for voicing


def test_v1_is_scoped_to_facts_not_context():
    docket = {"facts": "the category is 6 here",
              "text": "the category is 6 here\nCONTEXT: 999"}
    ok = bd.gate("The category 6 applies.", docket, "scope")
    assert not any("number 6" in f for f in ok)
    bad = bd.gate("The value 999 applies.", docket, "scope")
    assert any("999" in f for f in bad)  # present only in CONTEXT


def test_fact_voices_store_reuse_and_ladder(tmp_path):
    """One scoped call per NEW fact; unchanged facts never
    re-pay; blessed > proposed > machine."""
    store = tmp_path / "07_fact_voices.json"
    calls = []

    def voicer(fact):
        calls.append(fact)
        return "plain words for " + fact

    items = [("k1", "the category is 'Lucky' (7)"),
             ("k2", "the date is recorded")]
    v1 = bd.voice_facts(items, store, {"sentences": []},
                        voicer=voicer)
    assert len(calls) == 2 and v1["k1"].startswith("plain words")
    calls.clear()
    v2 = bd.voice_facts(items, store, {"sentences": []},
                        voicer=voicer)
    assert calls == []          # reuse: nothing re-paid
    assert v2 == v1
    registry = {"sentences": [{"fact_key": "k1",
                               "blessed_text": "her words",
                               "ruling": "RULED"}]}
    v3 = bd.voice_facts(items, store, registry, voicer=voicer)
    assert v3["k1"] == "her words"      # blessed wins


def test_fact_voice_gate_rejects_foreign_values(tmp_path):
    """A voice may only carry its own fact's values."""
    store = tmp_path / "07_fact_voices.json"

    def liar(fact):
        return "the category is 'Lucky' (8)"  # 8 is not the fact

    v = bd.voice_facts([("k1", "the category is 'Lucky' (7)")],
                       store, {"sentences": []}, voicer=liar)
    assert v["k1"] == "the category is 'Lucky' (7)"  # machine
    #                 fact stands when the voice fails its gate


# ---------- the name ladder (ruled 2026-10-04; red first)

DIR03 = REPO_ROOT / "AIVIA_01_Data" / "03_chat_bot"


def test_name_ladder_source_and_order(tmp_path):
    """ONE naming asset (03); ladder: sunny > blessed > first
    synonym."""
    names = bd.load_names(DIR03, {"names": []})
    assert names[("column", "CLARITY_ADT.EVENT_TYPE_C")] \
        == "event type"
    assert names[("table", "CLARITY_ADT")] == "adt"
    reg = {"names": [{"object_name": "CLARITY_ADT",
                      "blessed_name": "ADT events",
                      "ruling": "RULED"}]}
    names2 = bd.load_names(DIR03, reg)
    assert names2[("table", "CLARITY_ADT")] == "ADT events"


def test_facts_speak_short_names():
    """Her find: 'The event record category' must become 'The
    event type' in FACTS — via the asset, with 06 untouched."""
    facts, _ = bd.render_facts(DIR05, DIR06, DIR02, TOTALS)
    assert "event type is 'Census' (6)" in facts
    assert "event record category is 'Census' (6)" not in facts
    assert "(CLARITY_ADT)" in facts  # sources: short (NAME) — desc
    # and the 06 floor keeps its dictionary words
    six = json.loads((DIR06 / "06_description_sheet.json")
                     .read_text())
    fl = next(r["sentence"] for r in six
              if r["node_id"] == f"file::{TOTALS}")
    assert "the event record category" in fl


def test_recordedness_speaks_the_ladder():
    """Her 'pat id' find (2026-10-04): the recordedness voice
    consults the name ladder — facts say 'patient id'."""
    facts, _ = bd.render_facts(DIR05, DIR06, DIR02, TOTALS)
    assert "The patient id is recorded." in facts
    assert "pat id is recorded" not in facts


def test_voice_prompt_carries_the_linkage_law():
    p = bd._VOICE_PROMPT
    assert "linked" in p and "identifier" in p


def _filter_lines(facts):
    out, on = [], False
    for ln in facts.splitlines():
        if ln.startswith("WHO-IS-IN"):
            on = True
            continue
        if ln.startswith("ATTACHMENTS"):
            break
        if on and ln.strip().startswith("- "):
            out.append(ln.strip()[2:])
    return out


def test_facts_shape_matches_the_sql():
    """Her 13-vs-9 find: one line per TOP-LEVEL clause — the OR
    composes, EXISTS inlines, sub-scope leaves never double."""
    facts, _ = bd.render_facts(DIR05, DIR06, DIR02, TOTALS)
    lines = _filter_lines(facts)
    assert len(lines) == 9, lines
    # the cancel OR-group is ONE line, shape preserved
    orl = [ln for ln in lines
           if " or " in ln and "'Canceled' (2)" in ln]
    assert len(orl) == 1
    assert not any(ln.strip() == "The event subtype is 'Canceled' "
                   "(2)." for ln in lines)
    # EXISTS inlines its sub-selection detail
    ex = [ln for ln in lines
          if "STRING_SPLIT(@ServiceArea" in ln]
    assert len(ex) == 1 and "'0'" in ex[0]
    assert "separately defined selection" not in facts


def test_field_docket_v2_named_and_inheriting(tmp_path):
    """Field docket v2 (2026-10-04): the named defining phrase +
    the owning file's shaped filters."""
    out = tmp_path / "07"
    out.mkdir()
    rows = bd.build07(DIR05, DIR06, out, DIR02, no_llm=True,
                      only_file=TOTALS)
    fields = [r for r in rows if r["grain"] == "field"]
    assert len(fields) == 17
    # the per-field facts are built and gate-scoped
    facts = bd.render_field_facts(
        DIR05, DIR06, DIR02, TOTALS,
        fields[0]["node_id"],
        f"file::{TOTALS}::scope/delivery")
    assert "FIELD:" in facts
    assert "The event type is 'Census' (6)." in facts  # inherited
    assert "event record category" not in facts  # named, not raw
