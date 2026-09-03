"""P0-b (DESC-CORPUS-1, ordered 2026-08-31; re-cut to the ratified
acceptance 2026-09-02): the adversarial corpus over LIVE description
generation.

THE INSTRUMENT MEASURES WHAT SHIPS (ADR 0074 call 1 — spec:F/T1 as
the measurement instrument). Each case runs production's own
acceptance — `describe_step` (deterministic skeleton → one smoothing
attempt → grounding gate → skeleton floor) followed by the
empties-(a) voice kill, the exact block `generate_descriptions`
runs. Pattern ancestor (spec:G4 clause 3): the first cut of this
harness drove a raw-SQL prompt through `_grounded_describe` — the
pre-DESC-MEANING-1 acceptance — and kept grading that path after
production moved; this re-cut is the T2 lesson (checked ≠ shipping)
applied to the instrument itself.

Per class we report the PRODUCTION provenance vocabulary (spec:B2):
gate_passed (smoothed prose cleared the gate) · skeleton_floor (the
grounded skeleton shipped; the smoothing catch, if any, is listed) ·
emptied (voice kill — absence over fabrication, counted never
silent). Corpus cases carry NO dictionary, so this is the
worst-case leg: every meaning falls back to readable column names.

Usage:
  python devtools/desc_corpus.py            # live LLM (needs creds)
  python devtools/desc_corpus.py --dry      # gate evidence only
Writes: internal/docs/DESC_CORPUS_REPORT.md
"""

from __future__ import annotations

import os.path as _op
import sys as _sys

_sys.path.insert(0, _op.dirname(_op.dirname(_op.abspath(__file__))))

from dataclasses import dataclass, field  # noqa: E402

from src.descriptions import (  # noqa: E402
    describe_step,
    grounding_violations,
    line_level_kill,
    parsed_grain,
    parsed_tables,
)

# --- the adversarial corpus (the ordered classes) ---------------------
# Every case is a REAL fragment shape from the estate's vocabulary,
# chosen because it is where descriptions historically go wrong.

CASES = [
    {"cls": "inclusion", "name": "Diabetic_Incl",
     "sql": """SELECT DISTINCT ED.PATIENT_ID
FROM ENCOUNTER_DIAGNOSIS ED
WHERE ED.DX_CODE LIKE 'E11%' OR ED.DX_CODE LIKE 'O24.4%'""",
     "expect": ["This is a selection of patients.",
                "dx code starts with 'E11' or dx code starts with "
                "'O24.4'"],
     "outcome": "ships"},
    {"cls": "exclusion", "name": "Diabetic_Excl",
     "sql": """SELECT DISTINCT ED.PATIENT_ID
FROM ENCOUNTER_DIAGNOSIS ED
WHERE ED.DX_CODE LIKE 'E11%' AND ED.DX_CODE NOT LIKE 'O24.4%'""",
     "expect": ["dx code starts with 'E11'",
                "dx code does not start with 'O24.4'"],
     "outcome": "ships"},
    {"cls": "grain_patient", "name": "Patient_Grain",
     "sql": """SELECT DISTINCT LR.PATIENT_ID
FROM LAB_RESULTS LR
WHERE LR.HBA1C_VALUE >= 6.5""",
     "expect": ["This is a selection of patients.",
                "hba1c value is at least 6.5"],
     "outcome": "ships"},
    {"cls": "grain_visit", "name": "Visit_Grain",
     "sql": """SELECT HE.HOSP_ENC_ID, HE.ADMIT_DATE
FROM HOSPITAL_ENCOUNTERS HE
WHERE HE.ENCOUNTER_TYPE = 'ED'""",
     "expect": ["This is a selection of encounters.",
                "encounter type is 'ED'"],
     "outcome": "ships"},
    {"cls": "threshold_ge", "name": "Threshold_GE",
     "sql": """SELECT LR.PATIENT_ID
FROM LAB_RESULTS LR
WHERE LR.HBA1C_VALUE >= 6.5""",
     "expect": ["hba1c value is at least 6.5"],
     "outcome": "ships"},
    {"cls": "threshold_gt", "name": "Threshold_GT",
     "sql": """SELECT LR.PATIENT_ID
FROM LAB_RESULTS LR
WHERE LR.HBA1C_VALUE > 6.5""",
     "expect": ["hba1c value is more than 6.5"],
     "outcome": "ships"},
    {"cls": "negation", "name": "No_PCP",
     "sql": """SELECT E.PATIENT_ID
FROM ENCOUNTERS E
WHERE NOT EXISTS (SELECT 1 FROM PATIENT_PCP_ASSIGNMENT P
                  WHERE P.PATIENT_ID = E.PATIENT_ID)""",
     "expect": ["no matching record exists (patient id)"],
     "outcome": "ships"},
    {"cls": "multi_join", "name": "Three_Table",
     "sql": """SELECT DISTINCT P.PATIENT_ID
FROM PATIENTS P
JOIN DIAGNOSIS_CODES DC ON DC.PATIENT_ID = P.PATIENT_ID
JOIN MEDICATION_ORDERS MO ON MO.PATIENT_ID = P.PATIENT_ID
WHERE DC.ICD_CODE LIKE 'E11%'
  AND MO.MED_NAME IN ('METFORMIN', 'INSULIN GLARGINE')""",
     "expect": ["icd code starts with 'E11'",
                "med name is 'METFORMIN', 'INSULIN GLARGINE'"],
     "outcome": "ships"},
    {"cls": "aggregate", "name": "High_Utilizer",
     "sql": """SELECT E.PATIENT_ID, COUNT(E.ENCOUNTER_ID) AS VISITS
FROM ENCOUNTERS E
GROUP BY E.PATIENT_ID
HAVING COUNT(E.ENCOUNTER_ID) >= 4""",
     "expect": ["the number of encounter id values is at least 4"],
     "forbid": ["the value is", "after grouping"],
     "outcome": "ships"},
    {"cls": "degenerate_empty", "name": "Passthrough",
     "sql": "SELECT * FROM DM_REGISTRY",
     "expect": ["No filtering conditions are applied in this step."],
     "outcome": "ships"},
    {"cls": "degenerate_literal", "name": "Constant",
     "sql": "SELECT 1 AS ALWAYS_TRUE",
     "expect": ["No source records are read; this step produces "
                "derived values."],
     "outcome": "ships"},
    # ---- grown 2026-09-03 (Sunny's retro test-first order): the
    # week's gate food, each with its AUTHORED right answer. expect =
    # substrings the deterministic skeleton must contain; forbid =
    # substrings it must not; outcome = the production acceptance's
    # verdict on the un-smoothed skeleton ("ships" | "emptied").
    # tests/test_corpus_answers.py asserts all of it without an LLM.
    {"cls": "expr_depth", "name": "Abx_Window",
     "sql": """SELECT MA.ENCOUNTER_ID FROM MED_ADMIN MA
WHERE (ABS(DATEDIFF(MI, MA.TAKEN_TIME,
       MA.BLOOD_CULTURE_ORDER_TIME)) / 60.00) <= 72.0""",
     "meanings": {"TAKEN_TIME": "the antibiotic administration time",
                  "BLOOD_CULTURE_ORDER_TIME":
                      "the blood culture order time"},
     "expect": ["This is a selection of encounters.",
                "the absolute value of the minutes between the "
                "antibiotic administration time and the blood culture "
                "order time, divided by 60.00 is at most 72.0"],
     "forbid": ["condition holds", "`"],
     "outcome": "ships"},
    {"cls": "expr_arith", "name": "Weight_Convert",
     "sql": ("SELECT PATIENT_ID FROM VITALS "
             "WHERE WEIGHT_KG * 2.2 > 300"),
     "meanings": {"WEIGHT_KG": "weight in kilograms"},
     "expect": ["weight in kilograms times 2.2 is more than 300"],
     "forbid": ["condition holds"],
     "outcome": "ships"},
    {"cls": "not_in", "name": "Med_Exclusion",
     "sql": ("SELECT PATIENT_ID FROM MEDICATION_ORDERS "
             "WHERE MED_NAME NOT IN ('METFORMIN', 'INSULIN')"),
     "expect": ["med name is not 'METFORMIN', 'INSULIN'"],
     "outcome": "ships"},
    {"cls": "not_between", "name": "A1c_Abnormal",
     "sql": ("SELECT PATIENT_ID FROM LAB_RESULTS "
             "WHERE HBA1C_VALUE NOT BETWEEN 4 AND 5.6"),
     "expect": ["hba1c value does not fall between 4 and 5.6"],
     "forbid": ["between 4 and 6"],   # the decimal-split corpse
     "outcome": "ships"},
    {"cls": "tautology", "name": "Scaffolding",
     "sql": ("SELECT PATIENT_ID FROM ENCOUNTERS "
             "WHERE 1=1 AND ENCOUNTER_TYPE = 'ED'"),
     "expect": ["encounter type is 'ED'"],
     "forbid": ["condition holds", "1=1"],
     "outcome": "ships"},
    {"cls": "param_default", "name": "Reporting_Window",
     "sql": ("IF @StartDate IS NULL SET @StartDate = '2024-01-01'\n"
             "SELECT PATIENT_ID FROM ENCOUNTERS "
             "WHERE ADMIT_DATE >= @StartDate"),
     "meanings": {"ADMIT_DATE": "admission date"},
     "expect": ["start date defaults to '2024-01-01' when no value "
                "is supplied",
                "admission date is at least start date"],
     "forbid": ["condition holds", "dstartdate"],
     "outcome": "ships"},
    {"cls": "elision", "name": "Long_Code_List",
     "sql": ("SELECT ENCOUNTER_ID FROM FLOWSHEET_RECORDED WHERE "
             "FLO_MEAS_ID IN ('A1','A2','A3','A4','A5','A6','A7','A8')"),
     "meanings": {"FLO_MEAS_ID": "the flowsheet measure"},
     "expect": ["the flowsheet measure is one of 8 values from "
                "'A1' to 'A8'"],
     "outcome": "ships"},    # the composed count is not an ungrounded value
    {"cls": "dict_sentence", "name": "Steward_Prose",
     "sql": ("SELECT ENCOUNTER_ID FROM MED_ADMIN "
             "WHERE TAKEN_TIME IS NOT NULL"),
     "meanings": {"TAKEN_TIME": "The user-specified time that the "
                                "action took place. Multiple actions "
                                "may exist for one order."},
     "expect": ["The user-specified time that the action took place "
                "is recorded"],
     "forbid": [". is recorded"],   # the spliced-sentence corpse
     "outcome": "ships"},
    {"cls": "placeholder_fp", "name": "Value_Set",
     "sql": ("SELECT PATIENT_ID FROM LDA_RECORDS "
             "WHERE VALUE_SET_ID = 3022"),
     "meanings": {"VALUE_SET_ID": "Unique identifier for the value "
                                  "set"},
     "expect": ["Unique identifier for the value set is 3022"],
     "outcome": "ships"},    # 'the value set' must NOT trip the mush ban
    {"cls": "unrenderable", "name": "Case_Predicate",
     "sql": ("SELECT PATIENT_ID FROM ENCOUNTERS WHERE "
             "CASE WHEN ADMIT_DATE > DISCHARGE_DATE THEN 1 "
             "ELSE 0 END = 1"),
     "expect": [],
     "outcome": "emptied"},  # the RIGHT answer is a counted empty:
                             # CASE-in-predicate is a ruled unrendered
                             # kind; raw echo, gate-refused, counted —
                             # and under §5.3a-1 a lead line alone is
                             # NOT a survivor (no decision bullet
                             # ships => the step still empties)
    # ---- grown 2026-09-04 (0074 §5.3a-1, kill unit = the SENTENCE;
    # authored BEFORE the build, per the answer-key law): a MIXED step
    # — one unvoicable raw-echo line beside true lines. The ruled
    # outcome: the violating LINE dies, the true lines SHIP, every
    # drop is counted. expect/forbid grade the SKELETON (which
    # rightly still carries the raw echo); expect_shipped /
    # forbid_shipped / killed grade what the ACCEPTANCE ships.
    {"cls": "mixed_kill", "name": "Mixed_Step",
     "sql": ("SELECT E.PATIENT_ID FROM ENCOUNTERS E WHERE "
             "CASE WHEN E.ADMIT_DATE > E.DISCHARGE_DATE THEN 1 "
             "ELSE 0 END = 1 "
             "AND E.ENCOUNTER_TYPE = 'ED' "
             "AND E.ADMIT_DATE IS NOT NULL"),
     "expect": ["encounter type is 'ED'",
                "admit date is recorded",
                "condition holds"],       # the skeleton is honest
     "outcome": "ships",                  # ...and the acceptance ships
     "expect_shipped": ["This is a selection of patients.",
                        "encounter type is 'ED'",
                        "admit date is recorded"],
     "forbid_shipped": ["condition holds", "`", "CASE WHEN"],
     "killed": 1},                        # exactly the raw-echo line
]

DAX_CASES = [
    {"cls": "dax_measure", "name": "Control Rate",
     "expr": "DIVIDE(CALCULATE(COUNTROWS(Registry), "
             "Registry[A1C] < 7), COUNTROWS(Registry))"},
]

@dataclass
class Tally:
    gate_passed: int = 0
    skeleton_floor: int = 0
    emptied: int = 0
    killed_lines: int = 0     # §5.3a-1: dropped lines across the class
    violations: "list[str]" = field(default_factory=list)
    samples: "list[tuple]" = field(default_factory=list)


def case_dict_lines(case: dict) -> "list[str] | None":
    """A case's meanings rendered the way production renders its
    dictionary (dictionary_for_step's '- NAME: desc' lines)."""
    m = case.get("meanings")
    return [f"- {k}: {v}" for k, v in m.items()] if m else None


def grade_case(case: dict, describe) -> "tuple[str, str, list, list]":
    """Production acceptance, verbatim (descriptions.py, the
    generate_descriptions step loop): describe_step → if the skeleton
    ships, the §5.3a-1 SENTENCE-grain voice kill decides what ships —
    the violating line dies, survivors ship, drops are counted; the
    step empties only when no decision line survives.
    Cases with a 'meanings' map run the with-dictionary leg — what
    production always has (grown 09-03; the dictionary-less leg alone
    could not see the sentence-meanings bug class).

    Returns (outcome, final_text, smoothing_catch_violations,
    killed_line_texts)."""
    sql = case["sql"]
    sd = describe_step(sql, case.get("meanings"), smooth=describe)
    if sd.source == "skeleton":
        shipped, killed, kill = line_level_kill(
            sd.text, sql, case_dict_lines(case))
        if kill and not shipped:
            return "emptied", "", sd.violations + kill, killed
        return "skeleton_floor", shipped, sd.violations, killed
    return "gate_passed", sd.text, sd.violations, []


def run(describe, cases=None) -> "dict[str, Tally]":
    out: "dict[str, Tally]" = {}
    for case in (cases if cases is not None else CASES):
        t = out.setdefault(case["cls"], Tally())
        outcome, text, caught, killed = grade_case(case, describe)
        setattr(t, outcome, getattr(t, outcome) + 1)
        if outcome != "emptied":
            t.killed_lines += len(killed)
        for v in caught:
            t.violations.append(v.split(":")[0])
        t.samples.append((case["name"], text, caught, case["sql"],
                          killed if outcome != "emptied" else []))
    return out


def fabricated_count(tallies: "dict[str, Tally]") -> int:
    """THRESHOLDS['fabricated']: a violation surviving into FINAL
    shipped text. Structurally impossible past the acceptance —
    re-asserted from the outside (the instrument checks the checker)."""
    return sum(len(grounding_violations(text, sql))
               for t in tallies.values()
               for _name, text, _caught, sql, _killed in t.samples
               if text)


def report(tallies: "dict[str, Tally]") -> str:
    lines = ["# P0-b — adversarial corpus over LIVE generation "
             "(production acceptance, ADR 0074)", ""]
    tot = {"gate_passed": 0, "skeleton_floor": 0, "emptied": 0}
    tot_killed = 0
    for cls, t in tallies.items():
        for k in tot:
            tot[k] += getattr(t, k)
        tot_killed += t.killed_lines
    n = sum(tot.values()) or 1
    lines += [
        f"**{n} case(s)** · gate_passed {tot['gate_passed']} · "
        f"skeleton_floor {tot['skeleton_floor']} · emptied "
        f"{tot['emptied']} · killed lines {tot_killed}",
        "",
        "gate_passed = smoothed prose cleared the gate · "
        "skeleton_floor = the grounded skeleton shipped (the smoothing "
        "catch, if any, is listed) · emptied = voice kill, absence "
        "over fabrication (0074 §5.3a) · killed lines = §5.3a-1 "
        "SENTENCE-grain kills on partial ships (the violating line "
        "died, the true lines shipped, every drop counted). "
        "Dictionary-less leg: meanings fall back to readable column "
        "names.",
        "",
        "## Per class", "",
    ]
    for cls in sorted(tallies):
        t = tallies[cls]
        vs = sorted(set(t.violations))
        lines.append(
            f"- **{cls}** — gate_passed {t.gate_passed} · "
            f"skeleton_floor {t.skeleton_floor} · emptied {t.emptied}"
            + (f" · killed lines {t.killed_lines}"
               if t.killed_lines else "")
            + (f" · smoothing catch: {', '.join(vs)}" if vs else ""))
    lines += ["", "## Samples (fragment → final description)", ""]
    for cls in sorted(tallies):
        for name, text, caught, _sql, killed in tallies[cls].samples:
            lines += [f"### {cls} · {name}",
                      "```", (text or "(emptied)").strip(), "```"]
            if caught:
                lines.append(
                    f"smoothing catch: {len(caught)} violation(s) — "
                    "the skeleton shipped instead")
            if killed:
                lines.append(
                    f"killed line(s) ({len(killed)}, counted — never "
                    "shipped): " + " · ".join(f"`{k}`" for k in killed))
            lines.append("")
    return "\n".join(lines)


# ADR 0074 D2 (spec:F/T1 as the measurement instrument): the corpus
# run's build-stopper thresholds, as data. fabricated = a violation
# surviving into FINAL text — structurally impossible past the gate,
# asserted anyway (the instrument checks the checker).
THRESHOLDS = {"fabricated": 0, "role": "build_stopper"}


def main() -> None:
    dry = "--dry" in _sys.argv
    if dry:
        for case in CASES:
            print(f"== {case['cls']} · {case['name']}")
            print("   tables:", sorted(parsed_tables(case["sql"])),
                  "| grain:", sorted(parsed_grain(case["sql"])))
        return
    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.orchestrator.agent import azure_chat_api
    api = azure_chat_api()

    def describe(prompt: str) -> str:
        msg = api([{"role": "user", "content": prompt}], [])
        return str(msg.get("content") or "")

    tallies = run(describe)
    text = report(tallies)
    out = "internal/docs/DESC_CORPUS_REPORT.md"
    with open(out, "w") as f:
        f.write(text)
    print(text.split("## Samples")[0])
    print(f"wrote {out}")
    fab = fabricated_count(tallies)
    if fab > THRESHOLDS["fabricated"]:
        print(f"BUILD STOPPER: fabricated={fab} "
              f"(threshold {THRESHOLDS['fabricated']})")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
