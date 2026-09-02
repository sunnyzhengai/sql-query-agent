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
WHERE ED.DX_CODE LIKE 'E11%' OR ED.DX_CODE LIKE 'O24.4%'"""},
    {"cls": "exclusion", "name": "Diabetic_Excl",
     "sql": """SELECT DISTINCT ED.PATIENT_ID
FROM ENCOUNTER_DIAGNOSIS ED
WHERE ED.DX_CODE LIKE 'E11%' AND ED.DX_CODE NOT LIKE 'O24.4%'"""},
    {"cls": "grain_patient", "name": "Patient_Grain",
     "sql": """SELECT DISTINCT LR.PATIENT_ID
FROM LAB_RESULTS LR
WHERE LR.HBA1C_VALUE >= 6.5"""},
    {"cls": "grain_visit", "name": "Visit_Grain",
     "sql": """SELECT HE.HOSP_ENC_ID, HE.ADMIT_DATE
FROM HOSPITAL_ENCOUNTERS HE
WHERE HE.ENCOUNTER_TYPE = 'ED'"""},
    {"cls": "threshold_ge", "name": "Threshold_GE",
     "sql": """SELECT LR.PATIENT_ID
FROM LAB_RESULTS LR
WHERE LR.HBA1C_VALUE >= 6.5"""},
    {"cls": "threshold_gt", "name": "Threshold_GT",
     "sql": """SELECT LR.PATIENT_ID
FROM LAB_RESULTS LR
WHERE LR.HBA1C_VALUE > 6.5"""},
    {"cls": "negation", "name": "No_PCP",
     "sql": """SELECT E.PATIENT_ID
FROM ENCOUNTERS E
WHERE NOT EXISTS (SELECT 1 FROM PATIENT_PCP_ASSIGNMENT P
                  WHERE P.PATIENT_ID = E.PATIENT_ID)"""},
    {"cls": "multi_join", "name": "Three_Table",
     "sql": """SELECT DISTINCT P.PATIENT_ID
FROM PATIENTS P
JOIN DIAGNOSIS_CODES DC ON DC.PATIENT_ID = P.PATIENT_ID
JOIN MEDICATION_ORDERS MO ON MO.PATIENT_ID = P.PATIENT_ID
WHERE DC.ICD_CODE LIKE 'E11%'
  AND MO.MED_NAME IN ('METFORMIN', 'INSULIN GLARGINE')"""},
    {"cls": "aggregate", "name": "High_Utilizer",
     "sql": """SELECT E.PATIENT_ID, COUNT(E.ENCOUNTER_ID) AS VISITS
FROM ENCOUNTERS E
GROUP BY E.PATIENT_ID
HAVING COUNT(E.ENCOUNTER_ID) >= 4"""},
    {"cls": "degenerate_empty", "name": "Passthrough",
     "sql": "SELECT * FROM DM_REGISTRY"},
    {"cls": "degenerate_literal", "name": "Constant",
     "sql": "SELECT 1 AS ALWAYS_TRUE"},
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
    violations: "list[str]" = field(default_factory=list)
    samples: "list[tuple]" = field(default_factory=list)


def grade_case(case: dict, describe) -> "tuple[str, str, list]":
    """Production acceptance, verbatim (descriptions.py, the
    generate_descriptions step loop): describe_step → if the skeleton
    ships, the empties-(a) voice kill decides shipped vs absent.

    Returns (outcome, final_text, smoothing_catch_violations)."""
    sql = case["sql"]
    sd = describe_step(sql, None, smooth=describe)
    if sd.source == "skeleton":
        kill = grounding_violations(sd.text, sql)
        if kill:
            return "emptied", "", sd.violations + kill
        return "skeleton_floor", sd.text, sd.violations
    return "gate_passed", sd.text, sd.violations


def run(describe, cases=None) -> "dict[str, Tally]":
    out: "dict[str, Tally]" = {}
    for case in (cases if cases is not None else CASES):
        t = out.setdefault(case["cls"], Tally())
        outcome, text, caught = grade_case(case, describe)
        setattr(t, outcome, getattr(t, outcome) + 1)
        for v in caught:
            t.violations.append(v.split(":")[0])
        t.samples.append((case["name"], text, caught, case["sql"]))
    return out


def fabricated_count(tallies: "dict[str, Tally]") -> int:
    """THRESHOLDS['fabricated']: a violation surviving into FINAL
    shipped text. Structurally impossible past the acceptance —
    re-asserted from the outside (the instrument checks the checker)."""
    return sum(len(grounding_violations(text, sql))
               for t in tallies.values()
               for _name, text, _caught, sql in t.samples if text)


def report(tallies: "dict[str, Tally]") -> str:
    lines = ["# P0-b — adversarial corpus over LIVE generation "
             "(production acceptance, ADR 0074)", ""]
    tot = {"gate_passed": 0, "skeleton_floor": 0, "emptied": 0}
    for cls, t in tallies.items():
        for k in tot:
            tot[k] += getattr(t, k)
    n = sum(tot.values()) or 1
    lines += [
        f"**{n} case(s)** · gate_passed {tot['gate_passed']} · "
        f"skeleton_floor {tot['skeleton_floor']} · emptied "
        f"{tot['emptied']}",
        "",
        "gate_passed = smoothed prose cleared the gate · "
        "skeleton_floor = the grounded skeleton shipped (the smoothing "
        "catch, if any, is listed) · emptied = voice kill, absence "
        "over fabrication (0074 §5.3a). Dictionary-less leg: meanings "
        "fall back to readable column names.",
        "",
        "## Per class", "",
    ]
    for cls in sorted(tallies):
        t = tallies[cls]
        vs = sorted(set(t.violations))
        lines.append(
            f"- **{cls}** — gate_passed {t.gate_passed} · "
            f"skeleton_floor {t.skeleton_floor} · emptied {t.emptied}"
            + (f" · smoothing catch: {', '.join(vs)}" if vs else ""))
    lines += ["", "## Samples (fragment → final description)", ""]
    for cls in sorted(tallies):
        for name, text, caught, _sql in tallies[cls].samples:
            lines += [f"### {cls} · {name}",
                      "```", (text or "(emptied)").strip(), "```"]
            if caught:
                lines.append(
                    f"smoothing catch: {len(caught)} violation(s) — "
                    "the skeleton shipped instead")
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
