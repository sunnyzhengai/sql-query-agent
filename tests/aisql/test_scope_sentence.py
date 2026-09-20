"""R14 — THE BUSINESS TERM SENTENCE (Brief_Pilot_Build_3, Sunny
"approved, build brief 3" 2026-09-20; rulings (1)-(3), (10) and
Q1-Q5 "agree with all five" from Brief_Pilot_Findings_R1): the
scope's stored description becomes ONE sentence — grain-or-base
lead, membership, population, payload — composed from the TREE at
compose time. Byte-exact pins authored RED before the composer
(test-first law). The statement render-join (Q5) and the
temp-table-existence guard idiom (R11 amendment) pin here too.

Proves: contract:aisql-design-to-code
"""
from aisql.flows import produce
from aisql.graph.read_api import ReadApi
from aisql.graph.store import Store

T0 = "2026-09-20T12:00:00Z"

COLS = {
    "d|s|GROUPER_COMPILED_LISTS|CONTEXT_NAME": "Context name.",
    "d|s|VALUE_SETS|VALUE_SET_ID": "Value set id.",
    "d|s|ENCOUNTERS|ENC_ID": "Encounter id.",
    "d|s|VALUE_SETS|ENC_ID": "Encounter id.",
    "d|s|EVENTS|PAT_ID": "Patient id.",
    "d|s|EVENTS|REC_TIME": "Recorded time.",
    "d|s|DATES|DEPT_ROLLUP": "Department rollup.",
    "d|s|DATES|SEQ": "Seq.",
    "d|s|DATES|END_TIME": "End time.",
    "d|s|FLOW|REC_TIME": "Recorded time.",
    "d|s|FLOW|SHIFT_START": "Shift start.",
    "d|s|FLOW|SHIFT_END": "Shift end.",
    "d|s|FLOW|DAY_START": "Day start.",
    "d|s|FLOW|DAY_END": "Day end.",
    "d|s|PLANS|PLAN_CODE": "Plan code.",
    "d|s|ALERTS|ENC_ID": "Encounter id.",
    "d|s|HISTORY|ENC_ID": "Encounter id.",
}
TEMPORAL = {"d|s|EVENTS|REC_TIME", "d|s|DATES|END_TIME",
            "d|s|FLOW|REC_TIME", "d|s|FLOW|SHIFT_START",
            "d|s|FLOW|SHIFT_END", "d|s|FLOW|DAY_START",
            "d|s|FLOW|DAY_END"}


def _read():
    store = Store()
    for cid, desc in COLS.items():
        props = {"description": desc}
        if cid in TEMPORAL:
            props["data_type"] = "datetime"
        store.append_node("column", cid, props, T0, "x1")
    for tid in ("d|s|GROUPER_COMPILED_LISTS", "d|s|ENCOUNTERS",
                "d|s|VALUE_SETS", "d|s|EVENTS", "d|s|DATES",
                "d|s|FLOW", "d|s|PLANS", "d|s|ALERTS", "d|s|HISTORY"):
        store.append_node("table", tid, {}, T0, "x1")
    return ReadApi(store)


TREE = {"name": "f.sql", "parameters": [], "statements": []}


def col(cid, ref):
    # literal: shape
    return {"kind": "column_ref", "ref": ref, "resolves_to": cid}


def lit(value):
    # literal: shape
    return {"kind": "literal", "value": value}


def pred(kind, **kw):
    # literal: shape
    return {"node": "predicate", "kind": kind, **kw}


def pm(name, expression=None):
    # literal: shape
    return {"node": "projection_member", "name": name,
            "expression": expression
            or {"kind": "column_ref", "ref": name}}


def tref(table, tid):
    # literal: shape
    return {"table_ref": f"dbo.{table}", "resolves_to": tid}


def scope(**kw):
    base = {"node": "scope", "name": "#S", "name_key": "f.sql::#S",
            "from_refs": [], "join_on": [], "where": None,
            "projection": []}
    base.update(kw)
    return base


def sentence(sc):
    return produce.scope_sentence(_read(), TREE, sc)


# ---- the two ruled shapes (ruling (3)) ----

def test_base_form_population_and_payload():
    sc = scope(
        from_refs=[tref("GROUPER_COMPILED_LISTS",
                        "d|s|GROUPER_COMPILED_LISTS")],
        where=pred("COMPARE_EQ",
                   subject=col("d|s|GROUPER_COMPILED_LISTS|CONTEXT_NAME",
                               "G.CONTEXT_NAME"),
                   comparand=lit("'FLO'")),
        projection=[pm("RECORD_ID"), pm("FLO_ID")])
    assert sentence(sc) == (
        "Grouper compiled lists records: The context name is 'FLO'; "
        "carrying the record id, the flo id.")


def test_membership_speaks_inner_joins_with_on_residues():
    """Ruling (2): membership first; value conditions from
    inner-join ONs ride the member parenthetically; join keys
    excluded (the FL9 noise)."""
    join = {"node": "structure", "kind": "AND", "join_type": "Inner",
            "children": [
                pred("COMPARE_EQ",
                     subject=col("d|s|ENCOUNTERS|ENC_ID", "E.ENC_ID"),
                     comparand=col("d|s|VALUE_SETS|ENC_ID",
                                   "V.ENC_ID")),
                pred("COMPARE_EQ",
                     subject=col("d|s|VALUE_SETS|VALUE_SET_ID",
                                 "V.VALUE_SET_ID"),
                     comparand=lit(3031))]}
    sc = scope(from_refs=[tref("ENCOUNTERS", "d|s|ENCOUNTERS"),
                          tref("VALUE_SETS", "d|s|VALUE_SETS")],
               join_on=[join], projection=[pm("ENC_ID")])
    assert sentence(sc) == (
        "Encounters records, matched in value sets records (the "
        "value set id is 3031), carrying the enc id.")


def test_outer_joins_never_enter_membership():
    join = {"node": "structure", "kind": "AND",
            "join_type": "LeftOuter",
            "children": [pred(
                "COMPARE_EQ",
                subject=col("d|s|ENCOUNTERS|ENC_ID", "E.ENC_ID"),
                comparand=col("d|s|VALUE_SETS|ENC_ID", "V.ENC_ID"))]}
    sc = scope(from_refs=[tref("ENCOUNTERS", "d|s|ENCOUNTERS"),
                          tref("VALUE_SETS", "d|s|VALUE_SETS")],
               join_on=[join], projection=[pm("ENC_ID")])
    assert sentence(sc) == "Encounters records, carrying the enc id."


# ---- grain (ruling (1) + slice E) ----

def test_group_by_grain_leads_and_the_base_drops():
    sc = scope(from_refs=[tref("EVENTS", "d|s|EVENTS")],
               group_by=[col("d|s|ENCOUNTERS|ENC_ID", "E.ENC_ID")],
               projection=[pm("ENC_ID"),
                           pm("FIRST_TIME",
                              {"kind": "function", "name": "MIN",
                               "args": [col("d|s|EVENTS|REC_TIME",
                                            "E.REC_TIME")]})])
    assert sentence(sc) == ("One record per enc id, carrying the "
                            "first time, and 1 carried-through "
                            "column.")


def test_distinct_grain_speaks_the_distinct_columns():
    sc = scope(from_refs=[tref("EVENTS", "d|s|EVENTS")],
               distinct=True,
               projection=[pm("PAT_ID"), pm("ENC_ID")])
    assert sentence(sc) == ("One record per distinct pat id and enc "
                            "id, carrying the pat id, the enc id.")


def test_rank_filter_partition_becomes_the_grain():
    """Ruling (1): window-partition grain speaks at the scope that
    APPLIES the rank filter; the rank condition leaves the
    population (it is structure, spoken as grain)."""
    inner = scope(
        name=None, name_key=None,
        from_refs=[tref("EVENTS", "d|s|EVENTS")],
        projection=[pm("PAT_ID"), pm("RN", {
            "kind": "function", "name": "ROW_NUMBER", "args": [],
            "over": {"partition_by": [col("d|s|EVENTS|PAT_ID",
                                          "E.PAT_ID")],
                     "order_by": [{"expr": col("d|s|EVENTS|REC_TIME",
                                               "E.REC_TIME"),
                                   "descending": True}]}})])
    outer = scope(
        from_refs=[{"derived_scope": inner, "alias": "t"}],
        where=pred("COMPARE_EQ",
                   subject={"kind": "column_ref", "ref": "t.RN",
                            "resolves_to": "DERIVED scope member"},
                   comparand=lit(1)),
        projection=[pm("PAT_ID")])
    assert sentence(outer) == ("One record per pat id, carrying the "
                               "pat id.")


def test_rank_filter_without_contents_keeps_the_structural_clause():
    """Q4: no captured partition -> the honest structural clause,
    never an invented grain."""
    inner = scope(
        name=None, name_key=None,
        from_refs=[tref("EVENTS", "d|s|EVENTS")],
        projection=[pm("PAT_ID"), pm("RN", {
            "kind": "function", "name": "ROW_NUMBER", "args": [],
            "over": True})])
    outer = scope(
        from_refs=[{"derived_scope": inner, "alias": "t"}],
        where=pred("COMPARE_EQ",
                   subject={"kind": "column_ref", "ref": "t.RN",
                            "resolves_to": "DERIVED scope member"},
                   comparand=lit(1)),
        projection=[pm("PAT_ID")])
    assert sentence(outer) == (
        "Events records; the first record in its ordered sequence "
        "kept; carrying the pat id.")


def test_inline_base_resolves_through_the_derived_scope():
    """Ruling (10): the composer reads the tree — an inline base
    speaks the derived scope's own base; the interior's inner
    joins join the membership."""
    join = {"node": "structure", "kind": "AND", "join_type": "Inner",
            "children": [pred(
                "COMPARE_EQ",
                subject=col("d|s|ALERTS|ENC_ID", "A.ENC_ID"),
                comparand=col("d|s|HISTORY|ENC_ID", "H.ENC_ID"))]}
    inner = scope(name=None, name_key=None,
                  from_refs=[tref("ALERTS", "d|s|ALERTS"),
                             tref("HISTORY", "d|s|HISTORY")],
                  join_on=[join],
                  projection=[pm("A")])
    outer = scope(from_refs=[{"derived_scope": inner, "alias": "t"}],
                  projection=[pm("A")])
    assert sentence(outer) == ("Alerts records, matched in history "
                               "records, carrying the a.")


# ---- union arms (Q2) ----

def test_union_arms_speak_once_with_alternatives():
    arm1 = scope(
        name=None, name_key=None,
        from_refs=[tref("DATES", "d|s|DATES")],
        where={"node": "structure", "kind": "AND", "children": [
            {"node": "structure", "kind": "NOT", "children": [
                pred("IN_LIST",
                     subject=col("d|s|DATES|DEPT_ROLLUP",
                                 "D.DEPT_ROLLUP"),
                     comparand_list=[lit("'ER'"), lit("'P-ER'")])]},
            pred("COMPARE_EQ",
                 subject=col("d|s|DATES|SEQ", "D.SEQ"),
                 comparand=lit(1))]},
        projection=[pm("A")])
    arm2 = scope(
        name=None, name_key=None,
        from_refs=[tref("DATES", "d|s|DATES")],
        where=pred("COMPARE_LTE",
                   subject=col("d|s|FLOW|REC_TIME", "D.REC_TIME"),
                   comparand=col("d|s|DATES|END_TIME",
                                 "D.END_TIME")),
        projection=[pm("A")])
    sc = scope(combination_arms=[arm1, arm2], combination="Union",
               combination_all=True)
    assert sentence(sc) == (
        "Dates records: in 2 alternatives: (1) The department "
        "rollup is none of the values 'ER', 'P-ER'; The seq is 1; "
        "(2) The rec time is on or before the end time; carrying "
        "the a.")


# ---- population mechanics (Q3 + ruling (3) compression) ----

def test_identical_subjects_betweens_merge():
    sc = scope(
        from_refs=[tref("FLOW", "d|s|FLOW")],
        where={"node": "structure", "kind": "AND", "children": [
            pred("RANGE",
                 subject=col("d|s|FLOW|REC_TIME", "F.REC_TIME"),
                 lower_bound=col("d|s|FLOW|SHIFT_START",
                                 "F.SHIFT_START"),
                 upper_bound=col("d|s|FLOW|SHIFT_END",
                                 "F.SHIFT_END")),
            pred("RANGE",
                 subject=col("d|s|FLOW|REC_TIME", "F.REC_TIME"),
                 lower_bound=col("d|s|FLOW|DAY_START", "F.DAY_START"),
                 upper_bound=col("d|s|FLOW|DAY_END", "F.DAY_END"))]},
        projection=[pm("A")])
    assert sentence(sc) == (
        "Flow records: The recorded time is between the shift start "
        "and the shift end (inclusive) or between the day start and "
        "the day end (inclusive); carrying the a.")


def test_long_value_lists_compress_to_a_count():
    """Ruling (3): the sentence compresses; the FULL list stays on
    the condition row (derivable, never lost)."""
    members = [lit(f"'{i}'") for i in range(8)]
    p = pred("IN_LIST",
             subject=col("d|s|PLANS|PLAN_CODE", "P.PLAN_CODE"),
             comparand_list=members)
    sc = scope(from_refs=[tref("PLANS", "d|s|PLANS")], where=p,
               projection=[pm("A")])
    assert sentence(sc) == ("Plans records: The plan code is one of "
                            "8 values; carrying the a.")
    from aisql.flows import inbound
    voice = produce._Voice(_read(), TREE)
    full = inbound.condition_render(p, voice)
    for i in range(8):
        assert f"'{i}'" in full  # the row keeps every value


def test_payload_caps_at_eight_named_then_counts():
    dcols = [pm(f"C{i}", {"kind": "case", "whens": []})
             for i in range(1, 11)]
    passthrough = [pm(f"P{i}") for i in range(1, 6)]
    sc = scope(from_refs=[tref("EVENTS", "d|s|EVENTS")],
               projection=dcols + passthrough)
    assert sentence(sc) == (
        "Events records, carrying the c1, the c2, the c3, the c4, "
        "the c5, the c6, the c7, the c8 and 2 more computed "
        "columns, and 5 carried-through columns.")


# ---- the out-of-class scopes keep their sentences ----

def test_delete_scope_keeps_the_removal_sentence():
    sc = scope(operation="delete",
               from_refs=[tref("EVENTS", "d|s|EVENTS")])
    assert sentence(sc) == ("This step removes records from events "
                            "records.")


def test_unmapped_shape_keeps_the_honest_counted_sentence():
    sc = scope(unmapped_shape="CursorStatement")
    assert sentence(sc) == (
        "The logic of this selection is not yet modeled (unmapped "
        "query shape: CursorStatement); its contents are counted "
        "for engineering review, never described by guess.")


# ---- the head clause + the statement render-join (Q5) ----

def test_scope_head_extracts_the_grain_or_base_clause():
    assert produce.scope_head(
        "One record per pat id, carrying the pat id.") \
        == "One record per pat id"
    assert produce.scope_head(
        "The main adm details selection, matched in the vaplh "
        "selection: X; carrying the y.") \
        == "The main adm details selection"
    assert produce.scope_head("An inline selection, carrying x.") \
        is None


def test_statement_display_borrows_the_scope_head_at_render():
    """Q5 ruled: derivable display join — the stored R11 text is
    untouched; the head clause lives once, on the scope."""
    got = produce.statement_display(
        "Builds the base poptemp selection, preparing the datecte "
        "selection first.",
        {"basepoptemp": "The main adm details selection"})
    assert got == ("Builds the base poptemp selection (the main adm "
                   "details selection), preparing the datecte "
                   "selection first.")
    # no head known -> the stored text passes through untouched
    assert produce.statement_display(
        "Builds the x selection.", {}) == "Builds the x selection."


# ---- the guard idiom (R11 amendment, FL10 family) ----

def _guard_stmt(then_kind="DropTableStatement"):
    # literal: shape — the tree statement dict the mapper writes
    return {"statement_kind": "IF", "then_kind": then_kind,
            "then_drops": ["#Base_PopTemp"],
            "predicate": {"node": "structure", "kind": "NOT",
                          "children": [pred(
                              "NULL_CHECK",
                              subject={"kind": "function",
                                       "name": "OBJECT_ID",
                                       "args": [lit(
                                           "'tempdb..#Base_PopTemp'"
                                       )]})]}}


def test_object_id_drop_dance_speaks_as_a_cleanup_step():
    assert produce.statement_phrase(
        _guard_stmt(), predicate_phrase="whatever") == (
        "A cleanup step: removes the previous #Base_PopTemp when "
        "it already exists.")


def test_non_drop_then_keeps_the_decision_step():
    got = produce.statement_phrase(
        _guard_stmt(then_kind="SetVariableStatement"),
        predicate_phrase="The x is recorded.")
    assert got == "A decision step, taken when the x is recorded."
