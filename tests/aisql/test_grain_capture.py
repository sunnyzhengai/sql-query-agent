"""SLICE E — THE GRAIN-SOURCE CAPTURE (Brief_Pilot_Build_3,
Sunny "approved, build brief 3" 2026-09-20; FL17 the echo-mandated
window capture WIDENED to the whole grain-source family by FL21):
the mapper captures GROUP BY column refs, the DISTINCT flag, and
the window's PARTITION BY / ORDER BY contents — ONE capture act.
The FL17 acceptance test rides here: a partitioned ROW_NUMBER
dcol whose stored phrase names its partition AND its ordering.

Authored RED before the capture (test-first law).

Proves: contract:aisql-design-to-code
"""
from aisql.flows import produce
from aisql.graph.kg2_mapper import map_tree
from aisql.graph.read_api import ReadApi
from aisql.graph.store import Store

SQL = """
SELECT E.ENC_ID,
       ROW_NUMBER() OVER (PARTITION BY E.PAT_ID
                          ORDER BY E.REC_TIME DESC, E.SEQ) AS RN
INTO #T
FROM dbo.EVENTS E
GROUP BY E.ENC_ID
"""

SQL_DISTINCT = """
SELECT DISTINCT E.PAT_ID INTO #D FROM dbo.EVENTS E
"""

SQL_GUARD = """
IF OBJECT_ID(N'tempdb..#Base_PopTemp') IS NOT NULL
    DROP TABLE #Base_PopTemp
"""


def _scope(sql):
    tree = map_tree("f.sql", sql)
    return tree["statements"][0]["scope"]


def test_group_by_columns_are_captured():
    scope = _scope(SQL)
    gb = scope.get("group_by")
    assert gb, "GROUP BY contents captured, not just the string"
    assert [g["kind"] for g in gb] == ["column_ref"]
    assert gb[0]["ref"] == "E.ENC_ID"


def test_distinct_is_captured_as_a_flag():
    assert _scope(SQL_DISTINCT).get("distinct") is True
    assert _scope(SQL).get("distinct") is None


def test_over_captures_partition_and_ordering():
    scope = _scope(SQL)
    expr = scope["projection"][1]["expression"]
    over = expr["over"]
    assert isinstance(over, dict), "over is contents now, not a flag"
    assert [p["ref"] for p in over["partition_by"]] == ["E.PAT_ID"]
    got = [(o["expr"]["ref"], o.get("descending"))
           for o in over["order_by"]]
    assert got == [("E.REC_TIME", True), ("E.SEQ", None)]
    assert bool(expr.get("over")) is True  # the flag reading survives


def test_if_guard_captures_then_kind_and_drops():
    tree = map_tree("f.sql", SQL_GUARD)
    stmt = tree["statements"][0]
    assert stmt["statement_kind"] == "IF"
    assert stmt["then_kind"] == "DropTableStatement"
    assert stmt["then_drops"] == ["#Base_PopTemp"]


# ---- FL17's acceptance: the slotted ROW_NUMBER phrase ----

T0 = "2026-09-20T12:00:00Z"
PAT = "d|s|EVENTS|PAT_ID"
REC = "d|s|EVENTS|REC_TIME"


def _voice():
    store = Store()
    store.append_node("column", PAT, {"description": "Patient id."},
                      T0, "x1")
    store.append_node("column", REC, {"description": "Recorded time.",
                                      "data_type": "datetime"},
                      T0, "x1")
    return produce._Voice(ReadApi(store), {"parameters": []})


def _col(cid, name):
    # literal: shape
    return {"kind": "column_ref", "ref": f"E.{name}",
            "resolves_to": cid}


def test_partitioned_row_number_names_partition_and_ordering():
    """THE FL17 ACCEPTANCE TEST (echo-mandated): the stored phrase
    names the per-what and the by-what."""
    m = {"node": "projection_member", "name": "RN",
         "expression": {"kind": "function", "name": "ROW_NUMBER",
                        "args": [],
                        "over": {"partition_by": [_col(PAT, "PAT_ID")],
                                 "order_by": [
                                     {"expr": _col(REC, "REC_TIME"),
                                      "descending": True}]}}}
    assert produce.derived_phrase(m, _voice()) == (
        "Rn: the record's position within each pat id, ordered by "
        "the rec time (descending).")


def test_flagged_row_number_keeps_the_slotless_phrase():
    """A legacy over=True flag (or empty contents) falls back to the
    ratified slotless phrase — never an empty slot in prose."""
    m = {"node": "projection_member", "name": "RN",
         "expression": {"kind": "function", "name": "ROW_NUMBER",
                        "args": [], "over": True}}
    assert produce.derived_phrase(m, _voice()) == (
        "Rn: the record's position in its ordered sequence.")


def test_group_by_refs_resolve_against_the_dictionary():
    """The captured grain sources join the one resolver walk —
    a group_by column binds like any other ref."""
    from aisql.graph import kg2_mapper
    store = Store()
    # literal: shape — minimal registration the resolver reads
    reg = {"customer": "t", "dba_team": "t", "db_name": "d",
           "server": None, "registered_sources": ["s"],
           "schema_sources": {"dbo": "s"}}
    store.append_node("table", "s|dbo|EVENTS", {}, T0, "x1")
    for col in ("ENC_ID", "PAT_ID", "REC_TIME", "SEQ"):
        store.append_node("column", f"s|dbo|EVENTS|{col}", {}, T0, "x1")
    tree = kg2_mapper.resolve(map_tree("f.sql", SQL), store, reg)
    scope = tree["statements"][0]["scope"]
    assert scope["group_by"][0]["resolves_to"] == "s|dbo|EVENTS|ENC_ID"
    over = scope["projection"][1]["expression"]["over"]
    assert over["partition_by"][0]["resolves_to"] \
        == "s|dbo|EVENTS|PAT_ID"
    assert over["order_by"][0]["expr"]["resolves_to"] \
        == "s|dbo|EVENTS|REC_TIME"
