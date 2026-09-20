"""Phase B exit (ADR 0077): the F8 phase-B answer keys go RUNNABLE.

The translator — the parser's twin, KG2b's one writer — against the
fixture's assertions: the homomorphism law (PB-1), content_key
invariance under syntax-only churn (PB-2) and sensitivity to truth
changes (PB-3), degenerate-translated-never-voiced (PB-4), and
draws_from citing KG1 material with the counted coverage-gap fallback
(PB-5). Requires ScriptDom — no fallback (ADR 0001).

Proves: contract:aisql-design-to-code
"""
import json
import pathlib

from aisql.graph import metamodel
from aisql.graph.kg2_mapper import map_tree
from aisql.graph.kg2_translator import (
    TRANSLATOR_VERSION,
    content_keys,
    parsed_census,
    translate,
)

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
CASES = json.loads((FIX / "F8_twin_graph" / "cases.json").read_text())
BY_ID = {c["id"]: c for fam, cases in CASES.items()
         if not fam.startswith("_") for c in cases}

LIBRARY_KINDS = {
    r["Kind"]
    for r in metamodel.load("kg2_kind_library")
    .sheets["Meaning_Node_Kinds"]
    if r["Kind"] != "_ruling"
}


def _twin(sql, name="t.sql", columns=None):
    return translate(map_tree(name, sql), columns)


# ---- PB-1: the homomorphism law -------------------------------------
def test_pb1_homomorphism_no_third_bucket():
    sql = BY_ID["PA-1-derived-column-corpse"]["sql"]
    tree = map_tree("pb1.sql", sql)
    twin = translate(tree)
    census = twin["census"]
    assert census["translated"] + census["gaps"] == census["twin_nodes"]
    assert census["twin_nodes"] == parsed_census(tree)  # == every node


def test_pb1_every_node_points_at_exactly_one_parsed_node():
    twin = _twin(BY_ID["PA-2-select-into"]["sql"])
    paths = [n["points_at"] for n in twin["nodes"]]
    assert len(paths) == len(set(paths))  # exactly one each, no shares


def test_pb1_kinds_stamps_and_composition():
    twin = _twin(BY_ID["PA-1-derived-column-corpse"]["sql"])
    for node in twin["nodes"]:
        assert node["kind"] in LIBRARY_KINDS, node
        assert node["content_key"]
    assert twin["translator_version"] == TRANSLATOR_VERSION
    assert twin["metamodel_version"] == \
        metamodel.load("kg2_kind_library").version
    # composition: the file root's key derives from its children —
    # change a child (the literal 4 -> 5) and the root key moves
    other = _twin(BY_ID["PA-1-derived-column-corpse"]["sql"]
                  .replace(">= 4", ">= 5"))
    root = next(n for n in twin["nodes"] if n["kind"] == "file")
    other_root = next(n for n in other["nodes"] if n["kind"] == "file")
    assert root["content_key"] != other_root["content_key"]


# ---- PB-2: content_key invariance -----------------------------------
BASE_SQL = ("SELECT E.APPT_STATUS_C FROM APPOINTMENTS E "
            "WHERE E.APPT_STATUS_C = 2 AND E.DEPT_ID = 900112")


def test_pb2_syntax_only_churn_keeps_every_key():
    base = content_keys(_twin(BASE_SQL))
    reformatted = content_keys(_twin(
        "SELECT   E.APPT_STATUS_C\nFROM APPOINTMENTS E\n"
        "WHERE\n    E.APPT_STATUS_C = 2\n    AND E.DEPT_ID = 900112"))
    aliased = content_keys(_twin(BASE_SQL.replace("E.", "ENC.")
                                 .replace(" E ", " ENC ")))
    reordered = content_keys(_twin(
        "SELECT E.APPT_STATUS_C FROM APPOINTMENTS E "
        "WHERE E.DEPT_ID = 900112 AND E.APPT_STATUS_C = 2"))
    assert base == reformatted
    assert set(base.values()) == set(aliased.values())
    # AND arms swap: the AND node and everything above keep their
    # keys (commutative sort); the arms keep theirs at moved paths
    assert set(base.values()) == set(reordered.values())


def test_pb2_trailing_comment_never_keys():
    with_note = content_keys(_twin(
        "SELECT A.X FROM T A WHERE A.EVENT_TYPE_CODE = 4  --TRANSFER OUT"))
    without = content_keys(_twin(
        "SELECT A.X FROM T A WHERE A.EVENT_TYPE_CODE = 4"))
    assert with_note == without


# ---- PB-3: content_key sensitivity ----------------------------------
def test_pb3_truth_changes_move_the_key():
    sql = BY_ID["PB-3-content-key-sensitivity"]["sql"]
    frame = "SELECT A.X FROM T A INNER JOIN U B ON A.ID = B.ID WHERE 1=1 {}"
    base = _twin(frame.format(sql))
    hours = _twin(frame.format(sql.replace("HH, 24", "HH, 48")))
    col = _twin(frame.format(sql.replace("ARRIVAL_DTTM", "DEPART_DTTM")))
    range_key = {n["content_key"] for n in base["nodes"]
                 if n["content"].get("predicate") == "RANGE"}
    assert range_key != {n["content_key"] for n in hours["nodes"]
                         if n["content"].get("predicate") == "RANGE"}
    assert range_key != {n["content_key"] for n in col["nodes"]
                         if n["content"].get("predicate") == "RANGE"}


def test_pb3_join_kind_moves_the_on_conditions_key():
    inner = _twin("SELECT A.X FROM T A INNER JOIN U B ON A.ID = B.ID")
    left = _twin("SELECT A.X FROM T A LEFT JOIN U B ON A.ID = B.ID")
    on_inner = {n["content_key"] for n in inner["nodes"]
                if n.get("join_type")}
    on_left = {n["content_key"] for n in left["nodes"]
               if n.get("join_type")}
    assert on_inner and on_left and on_inner != on_left


# ---- PB-4: degenerate translated, never voiced ----------------------
def test_pb4_degenerate_subkind_present_and_silenced():
    twin = _twin(BY_ID["PB-4-degenerate-translated"]["sql"]
                 .replace("WHERE", "SELECT D.X FROM DX D WHERE", 1))
    degenerate = [n for n in twin["nodes"]
                  if n.get("subkind") == "degenerate"]
    assert len(degenerate) == 1
    assert degenerate[0]["voiced"] == "never"
    assert degenerate[0]["kind"] == "condition"  # in the twin — the
    # homomorphism holds; silence is voicing policy, not absence
    likes = [n for n in twin["nodes"]
             if n["content"].get("predicate") == "PATTERN_MATCH"]
    assert len(likes) == 1 and "subkind" not in likes[0]


# ---- PB-5: draws_from cites sources; coverage gaps counted ----------
COL_ID = "simemr|dbo|APPOINTMENTS|APPT_STATUS_C"


def _resolved_tree():
    tree = map_tree("pb5.sql",
                    "SELECT E.APPT_STATUS_C FROM APPOINTMENTS E "
                    "WHERE E.APPT_STATUS_C = 2")
    def stamp(node):
        if isinstance(node, dict):
            if node.get("kind") == "column_ref":
                node["resolves_to"] = COL_ID
            for v in node.values():
                stamp(v)
        elif isinstance(node, list):
            for v in node:
                stamp(v)
    stamp(tree)
    return tree


def test_pb5_draws_from_cites_column_and_values_map():
    columns = {COL_ID: {
        "description": "Status category for the appointment record.",
        "values": {"2": "Completed"}}}
    twin = translate(_resolved_tree(), columns)
    condition = next(n for n in twin["nodes"]
                     if n["content"].get("predicate") == "COMPARE_EQ")
    assert COL_ID in condition["draws_from"]
    assert f"{COL_ID}|values:2" in condition["draws_from"]
    assert condition["content"]["value_meaning"] == "Completed"
    subject = next(n for n in twin["nodes"]
                   if n["content"].get("words_source") == "dictionary")
    assert "status category" in subject["content"]["words"].lower()
    assert twin["census"]["coverage_gaps"] == 0


def test_pb5_no_dictionary_words_is_readable_name_plus_counted_gap():
    columns = {COL_ID: {"description": ""}}  # known column, no words
    twin = translate(_resolved_tree(), columns)
    refs = [n for n in twin["nodes"]
            if n["content"].get("words_source") == "readable_name"]
    assert refs and all("appt status c" == n["content"]["words"]
                        for n in refs)
    assert twin["census"]["coverage_gaps"] == len(refs)  # counted,
    # never silent — the fallback posture, unchanged since R5
