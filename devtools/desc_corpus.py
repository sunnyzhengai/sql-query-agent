"""P0-b (DESC-CORPUS-1, ordered 2026-08-31): the adversarial corpus
over LIVE description generation.

Not fixtures of outputs: REAL fragments → REAL generation → the
grounding gate → graded. The question this answers is not "does the
gate catch a lie we hand it" (P0-a settled that) but "what does the
live generator actually produce, at rate, on the shapes that break
descriptions".

Per class we report: clean (passed the gate first try), recovered
(the corrective retry fixed it), salvaged (surgical fallback kept
grounded lines), emptied (absence over fabrication), and the
violation classes seen. Failures are GATE FOOD — extend, re-run.

Usage:
  python devtools/desc_corpus.py            # live LLM (needs creds)
  python devtools/desc_corpus.py --dry      # prompt shapes only
Writes: internal/docs/DESC_CORPUS_REPORT.md
"""

from __future__ import annotations

import os.path as _op
import sys as _sys

_sys.path.insert(0, _op.dirname(_op.dirname(_op.abspath(__file__))))

from dataclasses import dataclass, field  # noqa: E402

from src.descriptions import (  # noqa: E402
    _grounded_describe,
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

_PROMPT = """You are describing ONE step of a certified metric for a
business audience.

SQL:
{sql}

Write 1-3 bullet lines. State what this step selects and the
conditions that decide membership. Use business words; never invent
values, tables, or a counted entity the SQL does not support."""


@dataclass
class Tally:
    clean: int = 0
    recovered: int = 0
    salvaged: int = 0
    emptied: int = 0
    violations: "list[str]" = field(default_factory=list)
    samples: "list[tuple]" = field(default_factory=list)


def grade_case(case: dict, describe) -> "tuple[str, str, list]":
    """Returns (outcome, final_text, first_pass_violations)."""
    sql = case["sql"]
    prompt = _PROMPT.format(sql=sql)
    first = describe(prompt).strip()
    first_v = grounding_violations(first, sql) if first else []
    text, removed = _grounded_describe(describe, prompt, sql, None)
    if not first_v:
        return "clean", text, []
    if text and not removed:
        return "recovered", text, first_v
    if text:
        return "salvaged", text, first_v
    return "emptied", "", first_v


def run(describe, cases=None) -> "dict[str, Tally]":
    out: "dict[str, Tally]" = {}
    for case in (cases if cases is not None else CASES):
        t = out.setdefault(case["cls"], Tally())
        outcome, text, first_v = grade_case(case, describe)
        setattr(t, outcome, getattr(t, outcome) + 1)
        for v in first_v:
            t.violations.append(v.split(":")[0])
        t.samples.append((case["name"], text, first_v))
    return out


def report(tallies: "dict[str, Tally]") -> str:
    lines = ["# P0-b — adversarial corpus over LIVE generation", ""]
    tot = {"clean": 0, "recovered": 0, "salvaged": 0, "emptied": 0}
    for cls, t in tallies.items():
        for k in tot:
            tot[k] += getattr(t, k)
    n = sum(tot.values()) or 1
    lines += [
        f"**{n} case(s)** · clean {tot['clean']} · recovered "
        f"{tot['recovered']} · salvaged {tot['salvaged']} · emptied "
        f"{tot['emptied']}",
        "",
        "clean = passed the gate first try · recovered = the "
        "corrective retry fixed it · salvaged = surgical fallback "
        "kept grounded lines · emptied = absence over fabrication",
        "",
        "## Per class", "",
    ]
    for cls in sorted(tallies):
        t = tallies[cls]
        vs = sorted(set(t.violations))
        lines.append(
            f"- **{cls}** — clean {t.clean} · recovered {t.recovered}"
            f" · salvaged {t.salvaged} · emptied {t.emptied}"
            + (f" · first-pass violations: {', '.join(vs)}"
               if vs else ""))
    lines += ["", "## Samples (fragment → final description)", ""]
    for cls in sorted(tallies):
        for name, text, first_v in tallies[cls].samples:
            lines += [f"### {cls} · {name}",
                      "```", (text or "(emptied)").strip(), "```"]
            if first_v:
                lines.append(f"first pass: {len(first_v)} violation(s)")
            lines.append("")
    return "\n".join(lines)


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


if __name__ == "__main__":
    main()
