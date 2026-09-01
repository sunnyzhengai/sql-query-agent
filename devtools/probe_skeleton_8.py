"""REVIEW PROBE — the eight compose_skeleton cases, runnable.

Cases 1-4 are the DEFECTS (must change behaviour after the AST
re-cut). Cases 5-8 are REGRESSION (correct today, must stay correct).

Run:  .venv/bin/python <this file>
Exit: 0 if all eight hold, 1 otherwise. Prints each skeleton so the
OUTPUT READ is possible — the standing note is that counters cannot
see the decoy class.

This is review's harness, deliberately OUTSIDE tests/ so it cannot
collide with the fixtures dev pins. It asserts on rendered text, so
it works against the regex composer (red) and the AST one (green)
without modification.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/Users/sunnyzheng/sql-query-agent")

from src.descriptions import compose_skeleton  # noqa: E402

MEANINGS = {
    "PATIENT_ID": "the patient",
    "ENCOUNTER_ID": "the encounter",
    "GROUPER_ID": "the medication group",
    "FLO_MEAS_ID": "the flowsheet measure",
    "DEPARTMENT_ID": "the department",
    "TAKEN_TIME": "the time the medication was given",
    "CONTACT_DATE": "the date of the visit",
}

# (id, label, sql, predicate over the rendered skeleton, why it matters)
CASES = [
    (
        1,
        "NOT EXISTS must state the exclusion",
        "SELECT DISTINCT HU.PATIENT_ID INTO #NoPCP FROM #HighUtil HU "
        "WHERE NOT EXISTS (SELECT 1 FROM PATIENT_PCP_ASSIGNMENT PA "
        "WHERE PA.PATIENT_ID = HU.PATIENT_ID)",
        lambda s: ("exclud" in s.lower() or "no match" in s.lower()
                   or "without" in s.lower() or "not among" in s.lower()),
        "the exclusion IS the metric (High ED Utilizers WITHOUT PCP); "
        "silence here is the worst decoy in the set",
    ),
    (
        2,
        "HAVING threshold must survive",
        "SELECT PATIENT_ID INTO #HighUtil FROM ENCOUNTER "
        "WHERE CONTACT_DATE BETWEEN @dStart AND @dEnd "
        "GROUP BY PATIENT_ID HAVING COUNT(*) >= 4",
        lambda s: "4" in s,
        "the threshold DEFINES a high utilizer; dropping it describes "
        "a different cohort entirely",
    ),
    (
        3,
        "OR must not read as AND",
        "SELECT ENCOUNTER_ID INTO #Sepsis FROM ORDERS "
        "WHERE (GROUPER_ID IN ('800008','800009') OR DEPARTMENT_ID = 3022)",
        lambda s: ("any of" in s.lower() or " or " in s.lower()
                   or "either" in s.lower()),
        "sibling bullets read as conjunction; a steward certifies a "
        "narrower cohort than the SQL selects",
    ),
    (
        4,
        "SELECT-list CASE is a label, not a filter",
        "SELECT ENCOUNTER_ID, CASE WHEN FLO_MEAS_ID IN ('900112') "
        "THEN 'ETT' ELSE 'None' END AS AIRWAY INTO #Airway "
        "FROM FLOWSHEET WHERE DEPARTMENT_ID = 3022",
        lambda s: "900112" not in s,
        "a labelling expression rendered as membership invents a "
        "filter the query does not apply",
    ),
    (
        5,
        "REGRESSION: join keys dropped",
        "SELECT E.ENCOUNTER_ID INTO #J FROM ENCOUNTER E "
        "JOIN PATIENT P ON P.PATIENT_ID = E.PATIENT_ID "
        "WHERE E.DEPARTMENT_ID = 3022",
        lambda s: "3022" in s and s.lower().count("the patient is") == 0,
        "column=column wires tables and decides nothing",
    ),
    (
        6,
        "REGRESSION: ON-clause literal filter kept",
        "SELECT E.ENCOUNTER_ID INTO #J FROM ENCOUNTER E "
        "JOIN ORDERS O ON O.ENCOUNTER_ID = E.ENCOUNTER_ID "
        "AND O.GROUPER_ID IN ('800008')",
        lambda s: "800008" in s,
        "56 of 413 corpus steps put a REAL filter inside a JOIN ON",
    ),
    (
        7,
        "REGRESSION: comments are not values",
        "SELECT ENCOUNTER_ID INTO #P FROM MAR "
        "WHERE GROUPER_ID IN ('800008', -- norepinephrine\n"
        "'800009') -- pressors",
        lambda s: "norepinephrine" not in s.lower(),
        "Clarity annotates IN-lists with trailing comments; "
        "documentation is not data",
    ),
    (
        8,
        "REGRESSION: @parameter range stated",
        "SELECT ENCOUNTER_ID INTO #B FROM ENCOUNTER "
        "WHERE CONTACT_DATE BETWEEN @dStartDate AND @dEndDate",
        lambda s: "between" in s.lower(),
        "the date range is THE filter on most cohort steps",
    ),
]


def main() -> int:
    failed = []
    for cid, label, sql, holds, why in CASES:
        try:
            sk = compose_skeleton(sql, MEANINGS)
        except Exception as err:  # noqa: BLE001 — a probe reports, never hides
            sk = f"<EXCEPTION {type(err).__name__}: {err}>"
        ok = False
        try:
            ok = bool(holds(sk))
        except Exception:  # noqa: BLE001
            ok = False
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(cid)
        print(f"\n=== CASE {cid} [{mark}] {label}")
        print(f"    why: {why}")
        print("    SQL:", " ".join(sql.split())[:150])
        print("    SKELETON:")
        for line in sk.splitlines():
            print(f"      {line}")

    print("\n" + "=" * 62)
    if failed:
        print(f"FAILED CASES: {failed}  ({len(failed)}/8)")
        print("Cases 1-4 failing = the pre-re-cut baseline (expected red).")
        print("Cases 5-8 failing = a REGRESSION introduced by the re-cut.")
        return 1
    print("ALL EIGHT HOLD.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
