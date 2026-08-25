"""ADR 0055 — the shape-corpus generator.

One cell definition emits BOTH the SQL and its expected outcomes
(flags, edges, drops, compare verdicts) — oracles true by
construction (principle 2). Deterministic (spec:E2): same palette in,
byte-identical corpus out; no timestamps, no randomness.

Palette separation is load-bearing (Sunny's demo-eligibility ruling):
every name below comes from the palette file — cell logic is
domain-independent and a palette swap is a data-file change, no code.

The matrix registry (src/shapes/matrix.py) owns totality; this module
owns emission. Phase 2's property-based surface is `compose()` — any
(name_relation, logic_relation, scope, path) combination is emittable
on demand, which is what lets the seeded-combination test assert
pipeline invariants over arbitrary cells.
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------
# palette


def load_palette(path: "str | Path") -> dict:
    return json.loads(Path(path).read_text())


def dict_rows(palette: dict) -> "tuple[list[dict], list[dict]]":
    """The palette IS the shape corpus's data dictionary — table and
    column rows in the 040 contract shape."""
    tables, columns = [], []
    for tname, t in sorted(palette["tables"].items()):
        tables.append({"TABLE_NAME": tname,
                       "DESCRIPTION": t["description"]})
        for cname, cdesc in sorted(t["columns"].items()):
            columns.append({"TABLE_NAME": tname, "COLUMN_NAME": cname,
                            "DESCRIPTION": cdesc})
    return tables, columns


def metric_name_rows(palette: dict) -> "list[dict]":
    rows = []
    for m in palette["metrics"].values():
        rows.append({"metric_id": f"{m['schema']}.{m['proc']}",
                     "business_name": m["business_name"],
                     "source": "shape_corpus", "report_name": "",
                     "report_url": "", "assigned_date": "2026-08-24"})
    return sorted(rows, key=lambda r: r["metric_id"])


# ---------------------------------------------------------------------
# SQL building blocks — every identifier arrives via the palette


def _path_cte(palette: dict, name: str, path_key: str) -> str:
    p = palette["logic_paths"][path_key]
    a = p["alias"]
    return (f"{name} AS (\n"
            f"  SELECT {a}.PATIENT_ID, {a}.{_date_col(palette, p['table'])}\n"
            f"  FROM {p['table']} {a}\n"
            f"  WHERE {p['predicate']}\n"
            f")")


def _date_col(palette: dict, table: str) -> str:
    cols = palette["tables"][table]["columns"]
    for c in cols:
        if c.endswith("_DATE"):
            return c
    return sorted(cols)[0]


def _respace(sql: str) -> str:
    """Whitespace/case-only variant — must normalize equal
    (_content_key casefolds and collapses whitespace)."""
    out = []
    for line in sql.split("\n"):
        stripped = line.strip()
        out.append("    " + stripped.lower() if stripped else "")
    return "\n".join(out)


def _proc(schema: str, proc: str, ctes: "list[str]",
          final_from: str) -> str:
    body = ",\n".join(ctes)
    return (f"CREATE PROCEDURE {schema}.{proc}\nAS\nBEGIN\n"
            f"WITH\n{body}\n"
            f"SELECT * FROM {final_from};\nEND\n")


def compose(palette: dict, name: str, path_key: str,
            style: str = "plain") -> str:
    """Phase-2 property surface: one CTE for any (name, path, style).
    style: plain | respace (ws/case-only twin) | semflip (semantically
    same predicate, syntactically different — the D2 boundary)."""
    text = _path_cte(palette, name, path_key)
    if style == "respace":
        return _respace(text)
    if style == "semflip":
        p = palette["logic_paths"][path_key]
        pred = p["predicate"]
        if ">=" in pred:
            left, right = [s.strip() for s in pred.split(">=", 1)]
            flipped = f"{right} <= {left}"
        else:
            flipped = f"({pred})"
        return text.replace(p["predicate"], flipped)
    return text


# ---------------------------------------------------------------------
# the corpus — every file, cell-tagged; expectations by construction


def generate(palette: dict) -> "tuple[dict[str, str], dict]":
    """Returns ({relpath: sql_text}, shape_manifest_dict)."""
    m = palette["metrics"]
    n = palette["cte_names"]
    files: "dict[str, str]" = {}

    def mid(key: str) -> str:
        return f"{m[key]['schema']}.{m[key]['proc']}"

    def rel(key: str) -> str:
        return f"{m[key]['schema']}/{m[key]['proc']}.sql"

    def put(key: str, ctes: "list[str]", final_from: str) -> str:
        files[rel(key)] = _proc(m[key]["schema"], m[key]["proc"],
                                ctes, final_from)
        return rel(key)

    # -- S/M pair procs ------------------------------------------------
    ws_a = _path_cte(palette, n["ws_control"], "med")
    lab_draws = _path_cte(palette, n["hash_control"], "lab")
    dup_body_a = _path_cte(palette, n["dup_a"], "med")
    dup_body_b = dup_body_a.replace(n["dup_a"], n["dup_b"], 1)

    put("dx_path", [
        compose(palette, n["misnomer_seed"], "dx"),
        ws_a,
        lab_draws,
        compose(palette, n["sem_boundary"], "lab"),
        dup_body_a,
    ], n["misnomer_seed"])
    put("lab_path", [
        compose(palette, n["misnomer_seed"], "lab"),
        _respace(ws_a),
        lab_draws,
        compose(palette, n["sem_boundary"], "lab", style="semflip"),
        dup_body_b,
    ], n["misnomer_seed"])

    put("registry", [_path_cte(palette, "Reg_Core", "med")],
        "Reg_Core")
    put("registry_v1", [_path_cte(palette, "Reg_Core_v1", "problem")],
        "Reg_Core_v1")

    controlled = _path_cte(palette, "Ctrl_Pop", "lab").replace(
        ">= 6.5", "< 8.0")
    put("controlled", [controlled], "Ctrl_Pop")
    put("controlled_m", [controlled], "Ctrl_Pop")

    put("a1c_compliance", [_path_cte(palette, "A1c_Tested", "lab")],
        "A1c_Tested")

    put("twin_reporting", [_path_cte(palette, "Active_Now", "dx")],
        "Active_Now")
    put("twin_reports", [_path_cte(palette, "Active_Now", "med")],
        "Active_Now")

    roster_core = _path_cte(palette, "Panel_All", "problem")
    put("roster", [roster_core], "Panel_All")
    put("dm_list", [roster_core], "Panel_All")

    snap = _path_cte(palette, "Enrolled", "dx")
    put("snapshot_a", [snap], "Enrolled")
    put("snapshot_b", [_respace(snap)], "Enrolled")

    # -- D4 reference forms -------------------------------------------
    ref_sql = (
        f"CREATE PROCEDURE {m['ref_forms']['schema']}."
        f"{m['ref_forms']['proc']}\nAS\nBEGIN\n"
        "SELECT LR.PATIENT_ID, LR.HBA1C_VALUE\n"
        "INTO #A1c_Pool\nFROM LAB_RESULTS LR\n"
        "WHERE LR.LAB_CODE = 'A1C';\n\n"
        "SELECT DC.PATIENT_ID, DC.ICD_CODE\nINTO #Dx_Events\n"
        "FROM DIAGNOSIS_CODES DC\nWHERE DC.ICD_CODE LIKE 'E11%';\n\n"
        "WITH\nDirect_Form AS (\n"
        "  SELECT LAB_RESULTS.LAB_CODE\n  FROM LAB_RESULTS\n"
        "  WHERE LAB_RESULTS.LAB_CODE = 'A1C'\n),\n"
        "Alias_Form AS (\n"
        "  SELECT LR2.RESULT_DATE\n  FROM LAB_RESULTS LR2\n"
        "  WHERE LR2.RESULT_DATE >= '2026-01-01'\n),\n"
        "TempChase_Form AS (\n"
        "  SELECT bc.HBA1C_VALUE\n  FROM #A1c_Pool bc\n"
        "  WHERE bc.HBA1C_VALUE >= 6.5\n),\n"
        "Unique_Form AS (\n"
        "  SELECT HBA1C_VALUE\n  FROM LAB_RESULTS\n"
        "  WHERE LAB_CODE = 'A1C'\n),\n"
        "Ambig_Form AS (\n"
        "  SELECT PATIENT_ID\n"
        "  FROM PATIENTS P\n  JOIN ENCOUNTERS E "
        "ON E.PATIENT_ID = P.PATIENT_ID\n"
        "  WHERE E.DEPARTMENT = 'ENDOCRINOLOGY'\n)\n"
        "SELECT * FROM TempChase_Form;\nEND\n")
    files[rel("ref_forms")] = ref_sql

    # -- D5 chains -----------------------------------------------------
    put("chain_linear", [
        _path_cte(palette, "Cascade_A", "dx"),
        ("Cascade_B AS (\n  SELECT CA.PATIENT_ID\n"
         "  FROM Cascade_A CA\n  WHERE CA.PATIENT_ID > 0\n)"),
        ("Cascade_C AS (\n  SELECT CB.PATIENT_ID\n"
         "  FROM Cascade_B CB\n  WHERE CB.PATIENT_ID > 0\n)"),
    ], "Cascade_C")
    put("chain_diamond", [
        _path_cte(palette, "Reach_Base", "problem"),
        ("Arm_Dx AS (\n  SELECT RB.PATIENT_ID\n  FROM Reach_Base RB\n"
         "  JOIN DIAGNOSIS_CODES DC ON DC.PATIENT_ID = RB.PATIENT_ID\n"
         "  WHERE DC.ICD_CODE LIKE 'E11%'\n)"),
        ("Arm_Lab AS (\n  SELECT RB.PATIENT_ID\n  FROM Reach_Base RB\n"
         "  JOIN LAB_RESULTS LR ON LR.PATIENT_ID = RB.PATIENT_ID\n"
         "  WHERE LR.HBA1C_VALUE >= 6.5\n)"),
        ("Funnel_Join AS (\n  SELECT AD.PATIENT_ID\n  FROM Arm_Dx AD\n"
         "  JOIN Arm_Lab AL ON AL.PATIENT_ID = AD.PATIENT_ID\n)"),
    ], "Funnel_Join")
    files[rel("chain_self")] = (
        f"CREATE PROCEDURE {m['chain_self']['schema']}."
        f"{m['chain_self']['proc']}\nAS\nBEGIN\n"
        "WITH Rollup_R AS (\n"
        "  SELECT P.PATIENT_ID, 0 AS DEPTH\n  FROM PATIENTS P\n"
        "  WHERE P.ACTIVE_FLAG = 1\n"
        "  UNION ALL\n"
        "  SELECT R.PATIENT_ID, R.DEPTH + 1\n  FROM Rollup_R R\n"
        "  WHERE R.DEPTH < 3\n)\n"
        "SELECT * FROM Rollup_R;\nEND\n")

    # -- D6 hygiene ----------------------------------------------------
    files[rel("dynamic_sql")] = (
        f"CREATE PROCEDURE {m['dynamic_sql']['schema']}."
        f"{m['dynamic_sql']['proc']}\nAS\nBEGIN\n"
        "DECLARE @sql NVARCHAR(MAX) = N'SELECT PATIENT_ID FROM "
        "PATIENTS WHERE ACTIVE_FLAG = 1';\nEXEC (@sql);\nEND\n")
    files[rel("multi_stmt")] = (
        f"CREATE PROCEDURE {m['multi_stmt']['schema']}."
        f"{m['multi_stmt']['proc']}\nAS\nBEGIN\n"
        "SELECT MO.PATIENT_ID, MO.MED_NAME\nINTO #Dx_Events\n"
        "FROM MEDICATION_ORDERS MO\n"
        "WHERE MO.MED_NAME = 'METFORMIN';\n\n"
        "WITH Refresh_Pop AS (\n"
        "  SELECT DE.PATIENT_ID\n  FROM #Dx_Events DE\n"
        "  WHERE DE.PATIENT_ID > 0\n)\n"
        "SELECT * FROM Refresh_Pop;\nEND\n")
    crlf = _proc(m["crlf_a"]["schema"], m["crlf_a"]["proc"],
                 [_path_cte(palette, n["crlf_seed"], "med")],
                 n["crlf_seed"])
    files[rel("crlf_a")] = crlf
    files[rel("crlf_b")] = crlf.replace(
        m["crlf_a"]["proc"], m["crlf_b"]["proc"]).replace("\n", "\r\n")
    files[rel("phi_probe")] = (
        f"CREATE PROCEDURE {m['phi_probe']['schema']}."
        f"{m['phi_probe']['proc']}\nAS\nBEGIN\n"
        "WITH Phi_Filter AS (\n"
        "  SELECT P.PATIENT_ID\n  FROM PATIENTS P\n"
        f"  WHERE P.PATIENT_NAME = {palette['phi_literal']}\n)\n"
        "SELECT * FROM Phi_Filter;\nEND\n")

    manifest = _manifest(palette, mid, rel)
    return files, manifest


# ---------------------------------------------------------------------
# expectations — by construction, per cell


def _manifest(palette: dict, mid, rel) -> dict:
    n = palette["cte_names"]

    def flag(cls, grain, identity, severity, logics):
        return {"flag_class": cls, "grain": grain, "identity": identity,
                "severity": severity, "distinct_logics": logics}

    cells = [
        # ---- Phase 1: D1×D2×D3 pair shapes ---------------------------
        {"cell_id": "S1", "dims": "step.cte.identical.hash_identical",
         "status": "instantiated",
         "files": [rel("dx_path"), rel("lab_path")],
         "expect": {"absent_flag_identities": [n["hash_control"]]}},
        {"cell_id": "S2", "dims": "step.cte.identical.ws_case_only",
         "status": "instantiated",
         "files": [rel("dx_path"), rel("lab_path")],
         "expect": {"absent_flag_identities": [n["ws_control"]]}},
        {"cell_id": "S3",
         "dims": "step.cte.identical.sem_same_syn_diff",
         "status": "instantiated",
         "files": [rel("dx_path"), rel("lab_path")],
         "expect": {"flags": [flag("misnomer", "step",
                                   n["sem_boundary"], "INFO", 2)],
                    "disclosure": "differs by normalized hash — the "
                                  "verdict never claims semantic "
                                  "difference (D2 boundary)"}},
        {"cell_id": "S4",
         "dims": "step.cte.identical.genuinely_different",
         "status": "instantiated",
         "files": [rel("dx_path"), rel("lab_path")],
         "expect": {"flags": [flag("misnomer", "step",
                                   n["misnomer_seed"], "INFO", 2)]}},
        {"cell_id": "S5",
         "dims": "step.temp.identical.genuinely_different",
         "status": "instantiated",
         "files": [rel("ref_forms"), rel("multi_stmt")],
         "expect": {"flags": [flag("misnomer", "step", "Dx_Events",
                                   "INFO", 2)]}},
        {"cell_id": "S6", "dims": "step.cte.disjoint.hash_identical",
         "status": "instantiated",
         "files": [rel("dx_path"), rel("lab_path")],
         "expect": {"flags": [flag("duplicate", "step",
                                   None, "INFO", 1)],
                    "duplicate_members": [n["dup_a"], n["dup_b"]]}},
        {"cell_id": "S7",
         "dims": "step.cte.disjoint.genuinely_different",
         "status": "instantiated",
         "files": [rel("registry"), rel("registry_v1")],
         "expect": {"absent_flag_identities": ["Reg_Core",
                                              "Reg_Core_v1"]}},
        {"cell_id": "S8", "dims": "step.*.cousin.*",
         "status": "excluded",
         "reason": "sweep v1 computes cousin families at metric grain "
                   "only (ADR 0054 §3b inventory); step-grain cousins "
                   "are a recorded follow-up"},
        {"cell_id": "S9", "dims": "step.schema_view.*",
         "status": "excluded",
         "reason": "schema-object sweep is a recorded ADR 0054 "
                   "follow-up; v1 artifact classes are steps and "
                   "metrics"},
        {"cell_id": "M1",
         "dims": "metric.business.identical.genuinely_different",
         "status": "instantiated",
         "files": [rel("twin_reporting"), rel("twin_reports")],
         "expect": {"flags": [flag("misnomer", "metric",
                                   "Active Diabetic Patients",
                                   "CONFLICT", 2)],
                    "compare": {"a": mid("twin_reporting"),
                                "b": mid("twin_reports"),
                                "verdict": "DIFFERS"}}},
        {"cell_id": "M2",
         "dims": "metric.business.cousin.genuinely_different",
         "status": "instantiated",
         "files": [rel("registry"), rel("registry_v1")],
         "expect": {"flags": [flag("cousin_conflict", "metric",
                                   "Diabetes Registry",
                                   "CONFLICT", 2)]}},
        {"cell_id": "M3", "dims": "metric.business.cousin.hash_identical",
         "status": "instantiated",
         "files": [rel("controlled"), rel("controlled_m")],
         "expect": {"flags": [flag("cousin_conflict", "metric",
                                   "Controlled Diabetes Rate",
                                   "INFO", 1)]}},
        {"cell_id": "M4",
         "dims": "metric.business.disjoint.hash_identical",
         "status": "instantiated",
         "files": [rel("roster"), rel("dm_list")],
         "expect": {"flags": [flag("duplicate", "metric", None,
                                   "INFO", 1)],
                    "duplicate_members": ["Diabetic Patient Roster",
                                          "DM Patient List"],
                    "compare": {"a": mid("roster"),
                                "b": mid("dm_list"),
                                "verdict": "IDENTICAL"}}},
        {"cell_id": "M5",
         "dims": "metric.business.disjoint.genuinely_different",
         "status": "instantiated",
         "files": [rel("a1c_compliance"), rel("registry")],
         "expect": {"absent_flag_identities": [
             "A1c Testing Compliance"]}},
        {"cell_id": "M6", "dims": "metric.business.identical.ws_case_only",
         "status": "instantiated",
         "files": [rel("snapshot_a"), rel("snapshot_b")],
         "expect": {"absent_flag_identities": ["Enrollment Snapshot"]}},
        {"cell_id": "M7",
         "dims": "metric.business.identical.hash_identical",
         "status": "excluded",
         "reason": "the M6 pair already proves the identical-name "
                   "normalized-equal control; a byte-identical twin "
                   "adds no coverage"},
        {"cell_id": "M8", "dims": "metric.*.sem_same_syn_diff",
         "status": "excluded",
         "reason": "the D2 boundary is a property of the normalizer, "
                   "proven at S3; the metric hash composes the same "
                   "normalized keys"},
        # ---- Phase 1: D4 reference forms -----------------------------
        {"cell_id": "R1", "dims": "ref.direct_qualified",
         "status": "instantiated", "files": [rel("ref_forms")],
         "expect": {"edges": [{
             "step": f"transform:{mid('ref_forms')}:Direct_Form",
             "column": "TECH:DBO.LAB_RESULTS.LAB_CODE"}]}},
        {"cell_id": "R2", "dims": "ref.aliased",
         "status": "instantiated", "files": [rel("ref_forms")],
         "expect": {"edges": [{
             "step": f"transform:{mid('ref_forms')}:Alias_Form",
             "column": "TECH:DBO.LAB_RESULTS.RESULT_DATE"}]}},
        {"cell_id": "R3", "dims": "ref.via_temp_projection",
         "status": "instantiated", "files": [rel("ref_forms")],
         "expect": {"edges": [{
             "step": f"transform:{mid('ref_forms')}:TempChase_Form",
             "column": "TECH:DBO.LAB_RESULTS.HBA1C_VALUE",
             "via_step": True}]}},
        {"cell_id": "R4", "dims": "ref.unqualified_unique",
         "status": "instantiated", "files": [rel("ref_forms")],
         "expect": {"edges": [{
             "step": f"transform:{mid('ref_forms')}:Unique_Form",
             "column": "TECH:DBO.LAB_RESULTS.HBA1C_VALUE"}]}},
        {"cell_id": "R5", "dims": "ref.unqualified_ambiguous",
         "status": "instantiated", "files": [rel("ref_forms")],
         "expect": {"drop_min": {"ambiguous": 1},
                    "note": "the BARE PATIENT_ID ref drops as "
                            "ambiguous (two candidate tables); the "
                            "QUALIFIED join refs in the same CTE "
                            "legitimately mint — the drop bucket, "
                            "not edge absence, is the assertion"}},
        {"cell_id": "R6", "dims": "ref.wrong_kind",
         "status": "excluded",
         "reason": "ask-surface cell (lineage(table=<metric name>) → "
                   "the W9 redirect stamp) — no SQL file exists for "
                   "it; covered by the walk section and the live leg, "
                   "recorded here for totality"},
        # ---- Phase 2: D5 chains --------------------------------------
        {"cell_id": "C1", "dims": "chain.linear",
         "status": "instantiated", "files": [rel("chain_linear")],
         "expect": {"t2t_edges": [
             [f"transform:{mid('chain_linear')}:Cascade_B",
              f"transform:{mid('chain_linear')}:Cascade_A"],
             [f"transform:{mid('chain_linear')}:Cascade_C",
              f"transform:{mid('chain_linear')}:Cascade_B"]]}},
        {"cell_id": "C2", "dims": "chain.diamond",
         "status": "instantiated", "files": [rel("chain_diamond")],
         "expect": {"t2t_edges": [
             [f"transform:{mid('chain_diamond')}:Arm_Dx",
              f"transform:{mid('chain_diamond')}:Reach_Base"],
             [f"transform:{mid('chain_diamond')}:Arm_Lab",
              f"transform:{mid('chain_diamond')}:Reach_Base"],
             [f"transform:{mid('chain_diamond')}:Funnel_Join",
              f"transform:{mid('chain_diamond')}:Arm_Dx"],
             [f"transform:{mid('chain_diamond')}:Funnel_Join",
              f"transform:{mid('chain_diamond')}:Arm_Lab"]]}},
        {"cell_id": "C3", "dims": "chain.self_reference",
         "status": "instantiated", "files": [rel("chain_self")],
         "expect": {"steps_present": [
             f"transform:{mid('chain_self')}:Rollup_R"],
             "note": "recursive CTE — build must complete with no "
                     "dangling edges (cycle broken at the back-edge)"}},
        {"cell_id": "C4", "dims": "chain.cross_schema_twin",
         "status": "instantiated",
         "files": [rel("twin_reporting"), rel("twin_reports")],
         "expect": {"metrics_present": [mid("twin_reporting"),
                                        mid("twin_reports")]}},
        # ---- Phase 2: D6 hygiene -------------------------------------
        {"cell_id": "H1", "dims": "hygiene.dynamic_sql",
         "status": "instantiated", "files": [rel("dynamic_sql")],
         "expect": {"handled_exception": mid("dynamic_sql"),
                    "note": "dynamic SQL — the declared exception "
                            "path (suppressed extraction or zero "
                            "extractable steps), never a crash"}},
        {"cell_id": "H2", "dims": "hygiene.multi_statement",
         "status": "instantiated", "files": [rel("multi_stmt")],
         "expect": {"steps_present": [
             f"transform:{mid('multi_stmt')}:Dx_Events",
             f"transform:{mid('multi_stmt')}:Refresh_Pop"]}},
        {"cell_id": "H3", "dims": "hygiene.crlf",
         "status": "instantiated",
         "files": [rel("crlf_a"), rel("crlf_b")],
         "expect": {"absent_flag_identities": [n["crlf_seed"]]}},
        {"cell_id": "H4", "dims": "hygiene.phi_literal",
         "status": "instantiated", "files": [rel("phi_probe")],
         "expect": {"phi_redaction_step":
                    f"transform:{mid('phi_probe')}:Phi_Filter"}},
    ]
    return {"palette_id": palette["palette_id"], "cells": cells}
