"""Join compliance — declared-vs-practiced, computed never stored.

A12 FINAL (2026-09-05): DIRECT table-table ON pairs ONLY; a join
mediated through a scope (#temp, CTE) is NOT JUDGED and the loophole
is DECLARED on every result, never hidden. A practiced join along no
declared path is a compliance FINDING, not a graph edit.
"""
from typing import Any, Dict

from aisql.lenses.decisions import named_scopes

A12_COMPLETENESS = ("direct table-table ON pairs ONLY; scope-mediated "
                    "joins not judged (A12 deferral, declared on every "
                    "result)")
FINDING = ("practiced join along no declared path — a compliance finding, "
           "not a graph edit")


def _flatten(pred):
    if pred is None:
        return []
    if pred.get("kind") == "AND":
        return list(pred["children"])
    return [pred]


def _table_of(col_id: str) -> str:
    return col_id.rsplit("|", 1)[0]


def lens_join_compliance(read, params) -> Dict[str, Any]:
    declared = {}
    for e in read.edges("joins_to"):
        declared[(e.from_id, e.to_id)] = e
    violations, compliant, not_judged = [], [], []
    for tree in read.trees().values():
        for scope in named_scopes(tree):
            for join_pred in scope.get("join_on", []):
                for pred in _flatten(join_pred):
                    if pred.get("kind") != "COMPARE_EQ":
                        continue
                    subject, comparand = pred["subject"], pred["comparand"]
                    sides = [subject.get("resolves_to"),
                             comparand.get("resolves_to")]
                    if any(s is None or s.startswith("SAME-TREE")
                           for s in sides):
                        not_judged.append(
                            f"{tree['name']}: "
                            f"{subject.get('ref')} = {comparand.get('ref')} "
                            "— scope-mediated, NOT JUDGED per A12")
                        continue
                    s_table, c_table = map(_table_of, sides)
                    s_col = subject["ref"].split(".")[-1]
                    c_col = comparand["ref"].split(".")[-1]
                    if (s_table, c_table) in declared or \
                            (c_table, s_table) in declared:
                        frm, to = ((s_table, c_table)
                                   if (s_table, c_table) in declared
                                   else (c_table, s_table))
                        f_col, t_col = ((s_col, c_col) if frm == s_table
                                        else (c_col, s_col))
                        # literal: shape
                        compliant.append({
                            "file": tree["name"],
                            "practiced": (f"{frm.rsplit('|', 1)[1]} <-> "
                                          f"{to.rsplit('|', 1)[1]} on "
                                          f"{f_col} = {t_col}"),
                            "declared_path": f"{frm} -> {to}"})
                    else:
                        t1, t2 = sorted((s_table.rsplit("|", 1)[1],
                                         c_table.rsplit("|", 1)[1]))
                        # literal: shape
                        violations.append({
                            "file": tree["name"],
                            "practiced": f"{t1} <-> {t2} on "
                                         f"{s_col} = {c_col}",
                            "declared_path": "NONE",
                            "finding": FINDING})
    # literal: shape
    return {"violations": violations, "compliant_practiced": compliant,
            "not_judged": not_judged, "completeness": A12_COMPLETENESS,
            "stamp": read.stamp()}
