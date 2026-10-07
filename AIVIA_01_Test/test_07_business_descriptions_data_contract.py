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


def test_gate_v2_and_the_run7_card_history():
    """The RECORDED run-7 card was the 10-03 quality bar; the
    10-04 LINE-OWNERSHIP LAW deliberately supersedes it — the
    old card now fails EXACTLY that one named check ("a unit
    other than ..." in Who's in it) and nothing else."""
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, TOTALS)
    f = bd.gate(RUN7_FILE_CLEAN, docket, "file")
    assert len(f) == 1 and "ownership" in f[0]


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


# RETIRED test_prompt_carries_s15_and_linkage_diction — 2026-10-04 at
# section-H acceptance (contract G): the S15 prompt lock moved to the
# checker (test_walk_g1/g3/g5 make the class mechanical); the prompt
# text keeps the law.


def test_whos_in_it_window_reference_never_asof():
    """RULED 2026-10-04 (her read of the regenerated census
    card): on Who's in it, the window reference names the
    reporting period ONLY — as-of behavior has one home, the
    Time window line."""
    p = bd.build_prompt("file", "DOCKET", [])
    assert "name the reporting period only" in p.lower()
    assert "as-of behavior never appears" in p.lower()


# RETIRED test_prompt_carries_s16_to_s18_and_selection_diction —
# 2026-10-04 at section-H acceptance (contract G): the S16-S18 prompt
# locks moved to the checker (test_walk_g1/g7 + the walk tone law);
# the prompt text keeps the laws.


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


# RETIRED test_field_docket_v2_named_and_inheriting — 2026-10-04 at
# section-H acceptance (contract G): Law A's inheriting field docket
# superseded by the room law (brief Q6); fields fly blind, lock
# replaced by test_walk_g6_population_fact_on_a_field_fails.


def test_field_shape_gate():
    """The 17-tooltips find: fields are one plain paragraph —
    no markdown mini-cards."""
    docket = {"facts": "FIELD: the room name", "text": "x"}
    bad = ("**Department**: the department.\n"
           "**Time window**: includes events.")
    f = bd.gate(bad, docket, "field")
    assert any("plain paragraph" in x for x in f)
    ok = bd.gate("Shows the room name for each census event.",
                 docket, "field")
    assert ok == []


def test_field_prompt_carries_one_home():
    p = bd.build_prompt("field", "DOCKET", [])
    assert "context" in p.lower()
    assert "card" in p.lower()


def test_prompt_carries_the_clinician_tone():
    """Her ruling 2026-10-04: a VOICE, not grammar rules — 'speak
    in a clinician's tone, instead of telling it about
    grammar'."""
    p = bd.build_prompt("file", "D", [])
    assert "clinician" in p
    assert "concrete verbs" not in p  # the grammar nudge retired
    assert "clinician" in bd._VOICE_PROMPT


def test_line_ownership_negatives_live_in_excludes():
    """Her 'reads weird' find: Who's in it is positive-only."""
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, TOTALS)
    bad = ("One row is: a census event.\n"
           "Who's in it: patients, other than those in CCMC "
           "MAIN OR, not linked to a record.\n"
           "Each row shows: event details.\n"
           "Time window: a configurable window\n"
           "Excludes: the listed departments")
    f = bd.gate(bad, docket, "file")
    assert any("Excludes" in x and "ownership" in x.lower()
               for x in f)
    good = bad.replace(
        "Who's in it: patients, other than those in CCMC "
        "MAIN OR, not linked to a record.",
        "Who's in it: patients with a census event in the "
        "chosen window.")
    assert not any("ownership" in x.lower()
                   for x in bd.gate(good, docket, "file"))


# ====================================================================
# THE WALK REOPEN TEST PLAN (documented 2026-10-04, the day all nine
# brief questions were ruled — Brief_07_Graph_Grounded_Proposer.md;
# contract: THE WALK CONTRACT section G, stamped same day).
#
# These are DOCUMENTED INTENT, not yet code: per the standing law
# the executable tests land RED, verbatim pytest output shown,
# IMMEDIATELY AFTER Sunny approves the pseudo code and BEFORE the
# first line of real walk code. Each lock below seeds a defect and
# must FAIL until the walk build makes it pass.
#
#   G.1 seeded memory-invention — a sentence carrying a value absent
#       from its room ("admission, discharge, transfer" on the
#       subtype field) -> the checker fails it, named finding.
#   G.2 seeded omission — 7 of the census file's 8 excluded
#       departments on the Excludes line -> class-1 value
#       conservation fails, both-directions.
#   G.3 paraphrased name — a column spoken outside its ladder name
#       ("the effective moment" for event effective time) -> name
#       violation.
#   G.4 filler KEEPS — a keeps-sentence on a condition-less scope
#       (the location split) -> scope shape fails (honest silence).
#   G.5 foreign condition — the date window spoken in the
#       service-area scope's text -> ownership fails.
#   G.6 population fact in a field room's output — any excluded
#       department named on a field sentence -> room violation.
#   G.7 plumbing climb — a class-3 value (the marker 1, STRING_SPLIT,
#       the All-code 0 as mechanism) on the card -> class-3 fails.
#
# RETIREMENTS — EXECUTED 2026-10-04 at Sunny's section-H
# acceptance ("accepted, run the cutover"): the inheriting
# field-docket lock and the S15/S16-S18 prompt locks are
# tombstoned below; their classes live on as walk G-locks.
# ====================================================================


# ------------------- THE WALK G-LOCKS (landed RED 2026-10-04 at
# pseudo approval; green only when business_walk.py's code lands
# under its approved comments. Room shape pinned per THE WALK
# CONTRACT A/E: speakable = the four match lists; context never
# grounds; must_say = the rung's obligations. check(text, room,
# grain) -> list of named finding strings, same as the gate.)

CENSUS = "COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS"
DIR03 = REPO_ROOT / "AIVIA_01_Data" / "03_chat_bot"

EIGHT_DEPTS = ["CCMC EMERGENCY", "CCMC IR IMAGING", "CCMC CATH LAB",
               "CCMC MAIN OR", "CCMC SPA OR", "CCMC PHP PSYCHIATRY",
               "CCMC CARDIOVASCULAR OR", "DSC OR"]


def _room(short=(), values=(), params=(), blessed=(), ctx="",
          must=()):
    return {"speakable": {"short_names": list(short),
                          "value_names": list(values),
                          "param_names": list(params),
                          "blessed_names": list(blessed)},
            "context": {"dictionary": ctx},
            "must_say": list(must)}


def test_walk_g1_memory_invention_fails_the_room():
    """G.1: a value from the model's MEMORY, absent from the room
    ('admission, discharge, transfer' on the subtype field)."""
    import business_walk as bw
    room = _room(short=["event subtype"], values=["Canceled"],
                 ctx="The subtype of the event record.",
                 must=["event subtype"])
    out = ("This field shows the event subtype, such as whether "
           "it reflects an admission, discharge, or transfer.")
    f = bw.check(out, room, "field")
    assert f and any("room" in x.lower() for x in f)
    assert any("admission" in x.lower() for x in f)


def test_walk_g2_omission_breaks_conservation():
    """G.2: 7 of 8 departments on the Excludes line — smooth text,
    missing value; the must-say direction catches it."""
    import business_walk as bw
    room = _room(values=EIGHT_DEPTS, must=list(EIGHT_DEPTS))
    out = ("Excludes: census events from " +
           ", ".join(EIGHT_DEPTS[:6]) + ", and " + EIGHT_DEPTS[6]
           + ".")  # DSC OR silently dropped
    f = bw.check(out, room, "card_line")
    assert f and any("conservation" in x.lower() for x in f)
    assert any("DSC OR" in x for x in f)


def test_walk_g3_paraphrased_name_is_a_name_violation():
    """G.3: the column spoken outside its ladder name."""
    import business_walk as bw
    room = _room(short=["event effective time"],
                 ctx="The instant when the event was supposed to "
                     "have happened.",
                 must=["event effective time"])
    out = ("This is the effective moment for the patient's "
           "census status.")
    f = bw.check(out, room, "field")
    assert f and any("event effective time" in x for x in f)


def test_walk_g4_filler_keeps_fails_scope_shape():
    """G.4: a keeps-sentence on a condition-less scope (the
    location split owns no membership conditions)."""
    import business_walk as bw
    room = _room(short=["revenue location"],
                 params=["the person running the report"],
                 must=["one row is"])  # no owned conditions
    out = ("One row here is one revenue location chosen when "
           "running the report. It keeps the locations picked "
           "when running the report.")
    f = bw.check(out, room, "scope")
    assert f and any("keep" in x.lower() for x in f)


def test_walk_g5_foreign_condition_fails_the_room():
    """G.5: the date window spoken inside the service-area
    scope — a fact no element of this room can ground."""
    import business_walk as bw
    room = _room(short=["service area"],
                 params=["the chosen service areas"],
                 must=["one row is"])
    out = ("One row here is one chosen service area, for events "
           "from the chosen start date through the chosen end "
           "date.")
    f = bw.check(out, room, "scope")
    assert f and any("room" in x.lower() for x in f)
    assert any("start date" in x.lower() for x in f)


def test_walk_g6_population_fact_on_a_field_fails():
    """G.6: a department name on a field sentence — the field
    room is blind to population (Q6), so it cannot resolve."""
    import business_walk as bw
    room = _room(short=["department"],
                 ctx="The abbreviated name of the department.",
                 must=["department"])
    out = ("This field shows the department, excluding CCMC "
           "EMERGENCY and DSC OR.")
    f = bw.check(out, room, "field")
    assert f and any("room" in x.lower() for x in f)
    assert any("CCMC EMERGENCY" in x for x in f)


def test_walk_g7_plumbing_on_the_card_fails():
    """G.7: class-3 values climbing to the card — the All-code 0
    and the marker 1 are in NO card room (the choice survives,
    its mechanism dies)."""
    import business_walk as bw
    room = _room(params=["the chosen service areas",
                         "the chosen locations"],
                 must=["the chosen service areas"])
    out = ("Who's in it: patients in the chosen service areas; "
           "choosing the value 0 includes every one, marked "
           "with a constant 1.")
    f = bw.check(out, room, "card_line")
    assert f and any("room" in x.lower() for x in f)
    assert any("0" in x or "1" in x for x in f)


def test_walk_selectors_are_disjoint_on_the_proving_file():
    """P4's disjointness law: the same predicate never lands in
    two card lines — one home per fact, mechanical at the card.
    Runs on the REAL census subgraph through the one read door."""
    import business_walk as bw
    store = bw.WalkStore(DIR05, DIR02, DIR03)
    sels = [bw.sel_whos_in_it, bw.sel_time_window,
            bw.sel_excludes]
    sets = [set(s(store, CENSUS)) for s in sels]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            assert not (sets[i] & sets[j])
    assert any(sets)  # the census file is not conditionless


def test_walk_build_conserves_the_21_rows(tmp_path):
    """The 2026-10-04 live find: the first walk build landed 4
    rows where 21 were owed (fields zipped against a 06 grain
    that does not exist). Locked: the proving file's floor build
    lands 1 file + 3 scope + 17 field rows, no-llm, zero cost."""
    import business_walk as bw
    out = tmp_path / "07"
    out.mkdir()
    rows = bw.build07_walk(DIR05, DIR06, out, DIR02, DIR03,
                           no_llm=True, only_file=CENSUS)
    grains = {}
    for r in rows:
        grains[r["grain"]] = grains.get(r["grain"], 0) + 1
    assert grains == {"file": 1, "scope": 3, "field": 17}


def test_walk_blessed_card_line_wins(tmp_path):
    """RULED 2026-10-04 (Sunny, option 2 on the inverted cancel
    clause): a blessed card line outranks every roll — blessed >
    gate_passed > floor, now at card-line grain. The walk build
    must consult the registry and never re-roll a blessed line."""
    import business_walk as bw
    out = tmp_path / "07"
    out.mkdir()
    blessed = "HER EXACT TIME WINDOW SENTENCE"
    (out / "07_blessing_registry.json").write_text(json.dumps(
        {"names": [], "sentences": [
            {"node_id": f"file::{CENSUS}::card/time_window",
             "blessed_text": blessed,
             "ruling": "RULED 2026-10-04"}]}))
    rows = bw.build07_walk(DIR05, DIR06, out, DIR02, DIR03,
                           no_llm=True, only_file=CENSUS)
    card = next(r for r in rows if r["grain"] == "file")
    assert blessed in card["audience_text"]


def test_walk_bless_door_requires_her_ruling(tmp_path):
    """THE RATIFY CLAUSE (2026-10-04): the write is machine-
    executed ONLY at Sunny's explicit ruling — an unruled write
    refuses; a ruled write lands her ruling verbatim; a newer
    dated ruling on the same node supersedes (delta-by-name)."""
    import business_walk as bw
    out = tmp_path / "07"
    out.mkdir()
    nid = f"file::{CENSUS}::card/time_window"
    try:
        bw.bless(out, nid, "some text", ruling="")
        raise AssertionError("unruled write must refuse")
    except ValueError as e:
        assert "ruling" in str(e).lower()
    bw.bless(out, nid, "her sentence",
             ruling="RULED 2026-10-04 (Sunny, in chat)")
    reg = json.loads((out / "07_blessing_registry.json")
                     .read_text())
    row = next(r for r in reg["sentences"]
               if r["node_id"] == nid)
    assert row["blessed_text"] == "her sentence"
    assert row["ruling"] == "RULED 2026-10-04 (Sunny, in chat)"
    bw.bless(out, nid, "her newer sentence",
             ruling="RULED 2026-10-05 (Sunny, in chat)")
    reg = json.loads((out / "07_blessing_registry.json")
                     .read_text())
    rows = [r for r in reg["sentences"] if r["node_id"] == nid]
    assert len(rows) == 1
    assert rows[0]["blessed_text"] == "her newer sentence"


def test_walk_choosing_all_is_licensed_with_choices():
    """The 2026-10-04 false positive: 'Choosing All' flagged as
    an unresolved claim. 'All' is S14's own ruled vocabulary —
    licensed whenever the room carries run-time choices."""
    import business_walk as bw
    room = _room(params=["the chosen service area",
                         "the chosen location"],
                 must=[])
    out = ("Census records in the chosen service area and the "
           "chosen location. Choosing All includes all.")
    assert bw.check(out, room, "card_line") == []


def test_walk_bless_name_door(tmp_path):
    """RULED 2026-10-04 (Sunny: bless 'patient servce' as
    'patient service'): the ratify door writes NAME rows too —
    same refusal law, and the ladder serves the blessed name
    first."""
    import business_walk as bw
    out = tmp_path / "07"
    out.mkdir()
    bw.bless(out, "ZC_PAT_SERVICE.NAME", "patient service",
             ruling="RULED 2026-10-04 (Sunny, in chat)",
             kind="name")
    store = bw.WalkStore(DIR05, DIR02, DIR03, out)
    assert store.ladder_name("ZC_PAT_SERVICE.NAME") == \
        "patient service"


def test_walk_class2_units_carry_no_string_must_say():
    """Q3 as ruled: class-2 survives as ONE plain clause, values
    NOT carried — so a class-2 room has no string must-say (the
    2026-10-04 doubled-Excludes root: must-say 'patient id'
    forced a second utterance beside 'not linked to a patient')."""
    import business_walk as bw
    store = bw.WalkStore(DIR05, DIR02, DIR03)
    for u in bw._top_units(store, CENSUS):
        room, ucls = bw._unit_room(store, u)
        if ucls == 2:
            assert room["must_say"] == []


def test_walk_rerender_applies_registry_without_calls(tmp_path):
    """RULED 2026-10-04 (Sunny's bless-1-and-2): landing a
    blessing must not reroll the unpinned lines — rerender mode
    rebuilds the card from the registry + the stored trace with
    ZERO calls, keeping every other row byte-identical."""
    import shutil

    import business_walk as bw
    src = Path("AIVIA_01_Data/07_business_descriptions")
    out = tmp_path / "07"
    out.mkdir()
    for f in ("07_business_sheet.json", "07_walk_trace.json",
              "07_blessing_registry.json"):
        shutil.copy(src / f, out / f)
    def no_caller(prompt):
        raise AssertionError("rerender must make zero calls")
    rows = bw.build07_walk(DIR05, DIR06, out, DIR02, DIR03,
                           only_file=CENSUS, rerender=True,
                           caller=no_caller)
    card = next(r for r in rows if r["grain"] == "file")
    assert "patient service" in card["audience_text"]
    assert "separately defined selection" not in \
        card["audience_text"]
    assert len(rows) == 21


# --------------------------------------- incremental delivery (D12)
# 10_work_wheel.md D12, ruled 2026-10-07: described = DONE. RED until
# build07 takes skip_files (a set of file stems): a skipped file's
# rows are CARRIED from the prior 07_business_sheet.json in out07 —
# the seat is never asked about them; only unskipped files propose.

def test_07_skip_files_carries_prior_rows_no_calls(tmp_path):
    out = tmp_path / "07"
    out.mkdir()
    bd.build07(DIR05, DIR06, out, DIR02, no_llm=True)  # the prior run
    prior = {r["node_id"]: r for r in json.loads(
        (out / "07_business_sheet.json").read_text())}
    stems = {n.split("::")[1] for n in prior}
    skip = stems - {LOTE}

    calls = []

    def spy(grain, docket_text, docket, registry):
        calls.append(grain)
        return ("x", "floor", [], 1)

    rows = bd.build07(DIR05, DIR06, out, DIR02, no_llm=False,
                      proposer=spy, skip_files=skip)
    # only LOTE's nodes reached the seat
    lote_nodes = [n for n in prior if n.split("::")[1] == LOTE]
    assert len(calls) == len(lote_nodes)
    # the skipped files' rows survive VERBATIM in the new sheet
    for r in rows:
        if r["node_id"].split("::")[1] != LOTE:
            assert r == prior[r["node_id"]], r["node_id"]


def test_07_skip_files_without_prior_sheet_refuses(tmp_path):
    """Skipping needs something to carry — no prior sheet in out07 is
    an honest refusal, never a silent hole."""
    out = tmp_path / "07"
    out.mkdir()
    import pytest
    with pytest.raises(ValueError, match="prior"):
        bd.build07(DIR05, DIR06, out, DIR02, no_llm=True,
                   skip_files={LOTE})


def test_07_defer_files_dropped_without_carry_or_refusal(tmp_path):
    """D12 batch door: a DEFERRED file (new, beyond max_new) is not
    in this run at all — no rows, no carry, no refusal; a later run
    takes it."""
    out = tmp_path / "07"
    out.mkdir()
    rows = bd.build07(DIR05, DIR06, out, DIR02, no_llm=True,
                      defer_files={LOTE})
    stems = {r["node_id"].split("::")[1] for r in rows}
    assert LOTE not in stems
    assert stems  # the others built
