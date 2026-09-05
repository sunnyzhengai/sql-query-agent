"""Registry conversion — Design-to-Code Protocol step 2.

Reads the seven DRAFT xlsx registries and emits stamped, code-consumable
JSON into AIVIA_Design/registries/. Two operations, kept separate and
auditable:

1. TRANSCRIBE: every sheet becomes a list of row-records keyed by the
   sheet's header row, verbatim — no hand-typed content anywhere.
2. PATCH: rulings already RECORDED (in the ratified doc or the closed
   open register) that the xlsx DRAFTs predate are applied as explicit,
   cited patch entries below. Landing recorded verdicts only — nothing
   here decides anything new. Anything undecided stays flagged in the
   emitted _open list.

Rerunnable: same xlsx + same patches -> byte-identical JSON.
Usage: python3 AIVIA_Design/registries/convert_from_xlsx.py
"""
import json
import os

import openpyxl

BASE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(BASE)

# registry file -> (source xlsx, doc section it restates)
SOURCES = {
    "kg1_technical": ("L1_KG1_Technical_Layer_Registry_DRAFT.xlsx",
                      "Level 1 / KG Layer 1 — source dictionaries technical layer"),
    "kg2_kind_library": ("L1_KG2_Kind_Library_TSQL_Predicates_DRAFT.xlsx",
                         "Level 1 / KG Layer 2 — kind library (T-SQL predicates)"),
    "kg2_logic": ("L1_KG2_Logic_Layer_Registry_DRAFT.xlsx",
                  "Level 1 / KG Layer 2 — logic layer"),
    "kg3_artifacts": ("L1_KG3_Artifact_Layer_Registry_DRAFT.xlsx",
                      "Level 1 / KG Layer 3 — artifact layer"),
    "kg4_concepts": ("L1_KG4_Concept_Layer_Registry_DRAFT.xlsx",
                     "Level 1 / KG Layer 4 — concept layer"),
    "lenses": ("L2_Lenses_Registry_DRAFT.xlsx", "Level 2 — lenses"),
    "flows": ("L3_Flows_Registry_DRAFT.xlsx", "Level 3 — the flows"),
}

STAMP_VERSION = "0.2-draft"  # xlsx were 0.1/0.2; this conversion is one step
CONVERTED_ON = "2026-09-05"


def sheet_records(ws):
    rows = []
    for row in ws.iter_rows(values_only=True):
        vals = ["" if v is None else str(v).strip() for v in row]
        while vals and vals[-1] == "":
            vals.pop()
        if vals:
            rows.append(vals)
    if not rows:
        return []
    header = rows[0]
    recs = []
    for vals in rows[1:]:
        rec = {}
        for i, v in enumerate(vals):
            key = header[i] if i < len(header) else f"col_{i}"
            rec[key] = v
        recs.append(rec)
    return recs


# ---- PATCHES: recorded rulings the DRAFT xlsx predate. Each entry is
# (registry, sheet, match: {col: value-prefix}, set: {col: new value}, citation)
PATCHES = [
    ("kg1_technical", "Node_Types",
     {"Node kind": "table", "Property": "grain"},
     {"Required": "opportunistic — never required",
      "Shape / allowed values": "declared by grain phrase on core tables only; "
      "absent + gap-listed elsewhere, never guessed",
      "Notes": "RULING APPLIED at conversion: doc ratified grain opportunistic "
      "(field-calibrated 2026-09-04); register D11 CLOSED 2026-09-05. "
      "Supersedes the xlsx OPEN/tbd row."},
     "doc §KG1 grain (2026-09-04) + register D11"),
    ("kg1_technical", "Edge_Types",
     {"Edge": "contains", "From": "db"},
     {"Direction rationale": "parent->child per the ratified two-part "
      "convention: CONTAINMENT points parent->child; REFERENCE points toward "
      "the more stable node (doc edge-direction convention, ratified "
      "2026-09-05; register D13 CLOSED). Supersedes the xlsx 'unresolved' note."},
     "doc edge-direction convention (2026-09-05) + register D13"),
    ("kg3_artifacts", "Classes",
     {"Class": "usage event"},
     {"Payload": "action: asked|ran|confirmed; asked carries OUTCOME "
      "(matched|ambiguous|no-match); no about edge on no-match; inquiry text "
      "as payload post phi_gate",
      "Notes": "RULING APPLIED at conversion: register H5 CLOSED 2026-09-05 "
      "(asked carries outcome; no about on no-match). relied_on cut stands."},
     "register H5 (2026-09-05)"),
]

# Lens catalog rows the DRAFT predates — reads/yields transcribed from the
# L2 Code Structure Map (authored 2026-09-05, the newer artifact).
ADD_ROWS = [
    ("lenses", "Catalog_v1",
     {"Lens": "referenced-keys",
      "Reads": "inbound joins_to groups per table (L1)",
      "Yields": "declared reference keys per table (distinct column-sets)",
      "Completeness note": "total — RULING APPLIED at conversion: register "
      "D12 CLOSED 2026-09-05 (derived from inbound joins_to, never stored)"},
     "register D12 (2026-09-05)"),
    ("lenses", "Catalog_v1",
     {"Lens": "correspondence",
      "Reads": "minted concepts (basis), current relatedness families",
      "Yields": "corresponds|dispersed|merged|new per family",
      "Completeness note": "total over minted — RULING APPLIED at conversion: "
      "register H7 CLOSED 2026-09-05 (S4 overlap-maximal rule; ties -> "
      "ambiguous, human rules). DEFERRED from v1 (compares prior state)"},
     "register H7 (2026-09-05)"),
    ("lenses", "Catalog_v1",
     {"Lens": "demand",
      "Reads": "no-match asked events (redacted payloads)",
      "Yields": "unanswered-question themes + counts",
      "Completeness note": "total over ledger — RULING APPLIED at conversion: "
      "register H5 CLOSED 2026-09-05. DEFERRED from v1 (reads the ask surface)"},
     "register H5 (2026-09-05)"),
]

# Undecided items carried forward as flags, never resolved here.
OPEN_FLAGS = {
    "kg2_kind_library": [
        "RG-1 (caught by validate_registries RG-C1): QUANTIFIED_COMPARE "
        "declares role 'comparison-op' but the Roles sheet never defines it. "
        "Two compliant readings — define comparison-op as a role, or model "
        "the operator as a predicate PROPERTY (roles are edges to expression "
        "children; an operator is not an expression). Sunny rules.",
    ],
    "kg2_logic": [
        "scope identity name-key detail (A3 collision-counted, A4 unnamed "
        "forbidden-for-attachment, A11 ::delivery emitters) is ruled in the "
        "doc but not yet restated as registry rows — ratification pass item",
    ],
    "lenses": [
        "MVP v1 'eleven lenses' count vs this catalog's granularity "
        "(6 spine derivations + 7 named = 13 rows in v1 scope) — naming/"
        "counting question for the ratification pass, not a content gap",
    ],
    "flows": [
        "Stages_and_Checks compresses the doc rules by design ('doc is "
        "authority'); the ratification pass decides whether flow rules get "
        "row-per-rule treatment like the KG registries",
    ],
}


def convert():
    log = []
    for name, (xlsx, doc_section) in SOURCES.items():
        wb = openpyxl.load_workbook(os.path.join(DESIGN, xlsx))
        sheets = {ws.title: sheet_records(ws) for ws in wb}
        applied = []
        for (reg, sheet, match, sets, cite) in PATCHES:
            if reg != name:
                continue
            hits = [r for r in sheets[sheet]
                    if all(r.get(c, "").startswith(v) for c, v in match.items())]
            assert len(hits) == 1, f"{reg}/{sheet}: patch matched {len(hits)} rows"
            hits[0].update(sets)
            applied.append(cite)
        for (reg, sheet, row, cite) in ADD_ROWS:
            if reg != name:
                continue
            assert not any(r.get("Lens") == row.get("Lens")
                           for r in sheets[sheet]), f"{reg}: duplicate add"
            sheets[sheet].append(dict(row))
            applied.append(cite)
        out = {
            "registry": name,
            "stamp": {
                "version": STAMP_VERSION,
                "doc_section": doc_section,
                "doc_stamp": "NOT YET STAMPED — Sunny action: doc sections "
                "carry no version stamps; compare is NOT-RUNNABLE until they do",
                "ratified": False,
                "converted_on": CONVERTED_ON,
                "converted_from": xlsx,
            },
            "rulings_applied_at_conversion": applied,
            "_open": OPEN_FLAGS.get(name, []),
            "sheets": sheets,
        }
        path = os.path.join(BASE, name + ".json")
        with open(path, "w") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        log.append(f"{name}: {sum(len(v) for v in sheets.values())} rows, "
                   f"{len(applied)} ruling(s) applied, "
                   f"{len(OPEN_FLAGS.get(name, []))} open flag(s)")
    print("\n".join(log))


if __name__ == "__main__":
    convert()
