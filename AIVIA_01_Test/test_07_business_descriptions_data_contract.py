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


def test_gate_names_banned_words_and_raw_codes():
    findings = bd.gate(ROUND4_SCOPE_BANNED_AND_CODE,
                       _scope_docket(), "scope")
    assert any("select" in f.lower() for f in findings)  # G-2
    assert any("code" in f.lower() and "1" in f
               for f in findings)                        # G-7


def test_gate_budget_fails_a_marathon_sentence():
    long = ("This selection holds patient contact language "
            "records for every contact whose relationship to the "
            "patient overlaps the configured reporting window in "
            "any of several distinct recorded ways.")
    findings = bd.gate(long, _scope_docket(), "scope")
    assert any("words" in f.lower() for f in findings)   # G-3


def test_gate_template_check_on_the_file_grain():
    assert bd.gate(ROUND5_FILE_CLEAN,
                   bd.docket_for_file(DIR05, DIR06, DIR02, LOTE),
                   "file") == []                          # G-4 ok
    prose = "This dataset shows monthly census patients."
    findings = bd.gate(prose,
                       bd.docket_for_file(DIR05, DIR06, DIR02,
                                          LOTE), "file")
    assert any("template" in f.lower() for f in findings)


def test_must_say_the_gap_on_the_dynamic_file():
    fname = "Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_SSRS"
    docket = bd.docket_for_file(DIR05, DIR06, DIR02, fname)
    no_gap = ("Who's in it: monthly census records.\n"
              "Each row shows: census day counts.\n"
              "Time window: a configurable date window\n"
              "Excludes: none stated")
    findings = bd.gate(no_gap, docket, "file")
    assert any("gap" in f.lower() for f in findings)      # G-6


def test_unbound_code_sighting_is_recorded():
    bd.reset_sightings()
    bd.gate(ROUND4_SCOPE_BANNED_AND_CODE, _scope_docket(),
            "scope")
    assert bd.code_sightings()  # the flywheel's second engine


# ------------------------------- prompt constructor (byte-exact)

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


def test_call_timeout_is_law():
    assert bd.CALL_TIMEOUT_S == 120


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
    texts = [p for p in out.iterdir() if p.suffix == ".txt"]
    assert len(texts) == 8
