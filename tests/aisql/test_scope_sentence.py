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
        # re-based at v2.15.0 (R15.a, Brief_Pilot_Build_2): the
        # column-to-column comparison now names both owners
        "Dates records: in 2 alternatives: (1) The department "
        "rollup is none of the values 'ER', 'P-ER'; The seq is 1; "
        "(2) The flow record's rec time is on or before the dates "
        "record's end time; carrying "
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


# ---- R15 THE VOICING REPAIRS (Brief_Pilot_Build_2, slice C —
# Sunny "agree with all seven recommendations, build it"
# 2026-09-20). Pins authored RED before the mechanisms. ----

def _voice():
    return produce._Voice(_read(), TREE)


def test_two_sided_compare_names_both_owners_tables():
    """R15.a (FL9, C2 (a)): every column-to-column compare names
    BOTH owners — the tautology 'The enc id is the enc id' dies.
    (Pinned at the predicate voice: the scope sentence excludes
    col=col equalities as join-key structure per R14; FL30 tracks
    that exclusion's same-table over-reach.)"""
    p = pred("COMPARE_EQ",
             subject=col("d|s|ALERTS|ENC_ID", "A.ENC_ID"),
             comparand=col("d|s|HISTORY|ENC_ID", "H.ENC_ID"))
    assert produce._voice_predicate(p, _voice()) == (
        "The alerts record's enc id is the history record's "
        "enc id.")


def test_two_sided_compare_scope_side_speaks_selection():
    """R15.a: a SAME-TREE side speaks 'the <words> selection's'."""
    p = pred("COMPARE_EQ",
             subject=col("d|s|ALERTS|ENC_ID", "A.ENC_ID"),
             comparand={"kind": "column_ref",
                        "ref": "[#Base_Pop].ENC_ID",
                        "resolves_to": "SAME-TREE scope f.sql::#Base_Pop"})
    assert produce._voice_predicate(p, _voice()) == (
        "The alerts record's enc id is the base pop selection's "
        "enc id.")


def test_two_sided_unresolved_side_keeps_bare_words():
    """R15.a: an unresolved side keeps bare name words — honesty
    over invention."""
    p = pred("COMPARE_EQ",
             subject={"kind": "column_ref", "ref": "A.ENC_ID"},
             comparand={"kind": "column_ref", "ref": "B.ENC_ID"})
    assert produce._voice_predicate(p, _voice()) == (
        "The enc id is the enc id.")


def _dateadd(unit, n, base):
    args = [lit(unit),
            ({"kind": "unary", "op": "Negative", "args": [lit(-n)]}
             if n < 0 else lit(n)),
            base]
    # literal: shape
    return {"kind": "function", "name": "DATEADD", "args": args}


def _getdate():
    # literal: shape
    return {"kind": "function", "name": "GETDATE", "args": []}


def test_within_the_last_idiom_year():
    """R15.b: subject >= DATEADD(unit, -N, GETDATE()) speaks the
    temporal window, never the raw fragment."""
    p = pred("COMPARE_GTE",
             subject=col("d|s|FLOW|REC_TIME", "F.REC_TIME"),
             comparand=_dateadd("YEAR", -1, _getdate()))
    assert produce._voice_predicate(p, _voice()) == (
        "The recorded time is within the last year.")


def test_within_the_last_idiom_days():
    p = pred("COMPARE_GTE",
             subject=col("d|s|FLOW|REC_TIME", "F.REC_TIME"),
             comparand=_dateadd("DD", -30, _getdate()))
    assert produce._voice_predicate(p, _voice()) == (
        "The recorded time is within the last 30 days.")


def test_within_the_next_idiom():
    p = pred("COMPARE_LTE",
             subject=col("d|s|FLOW|REC_TIME", "F.REC_TIME"),
             comparand=_dateadd("DD", 30, _getdate()))
    assert produce._voice_predicate(p, _voice()) == (
        "The recorded time is within the next 30 days.")


def test_negative_dateadd_speaks_before():
    """R15.b: a unary-minus offset voices 'before' — the guard
    reads through the wrapper, the raw fragment dies."""
    p = pred("COMPARE_GT",
             subject=col("d|s|FLOW|REC_TIME", "F.REC_TIME"),
             comparand=_dateadd("MI", -60,
                                col("d|s|FLOW|SHIFT_END",
                                    "F.SHIFT_END")))
    assert produce._voice_predicate(p, _voice()) == (
        "The recorded time is after 60 minutes before the shift "
        "end.")


def test_isnull_far_future_speaks_open_ended():
    """R15.b: ISNULL(<date>, far-future sentinel) speaks the
    author's open-ended idiom."""
    p = pred("COMPARE_LTE",
             subject={"kind": "function", "name": "ISNULL",
                      "args": [col("d|s|DATES|END_TIME",
                                   "D.END_TIME"),
                               lit("'2999-12-31'")]},
             comparand=col("d|s|FLOW|DAY_END", "F.DAY_END"))
    assert produce._voice_predicate(p, _voice()) == (
        "The end time (treating a missing date as open-ended) is "
        "on or before the day end.")


def test_where_path_fills_the_library():
    """R15.b ONE LIBRARY, TWO READERS: DATEDIFF in a WHERE fills
    from the same row the derived path reads — and a 'the number
    of' phrase is a COUNT, never temporal."""
    p = pred("COMPARE_GT",
             subject={"kind": "function", "name": "DATEDIFF",
                      "args": [lit("MI"),
                               col("d|s|FLOW|SHIFT_START",
                                   "F.SHIFT_START"),
                               col("d|s|FLOW|REC_TIME",
                                   "F.REC_TIME")]},
             comparand=lit(60))
    assert produce._voice_predicate(p, _voice()) == (
        "The number of minutes between the shift start and the "
        "recorded time exceeds 60.")


def test_cast_transparent_in_where():
    """R15.b: the cast kind is TRANSPARENT on the WHERE path —
    CONVERT(numeric, x) never prints raw again."""
    p = pred("COMPARE_GT",
             subject={"kind": "cast",
                      "args": [col("d|s|PLANS|PLAN_CODE",
                                   "P.PLAN_CODE")]},
             comparand=lit(95.0))
    assert produce._voice_predicate(p, _voice()) == (
        "The plan code exceeds 95.0.")


def test_getdate_speaks_the_current_moment():
    p = pred("COMPARE_LT",
             subject=col("d|s|FLOW|REC_TIME", "F.REC_TIME"),
             comparand=_getdate())
    assert produce._voice_predicate(p, _voice()) == (
        "The recorded time is before the current date and time.")


def test_pair_words_both_and_either():
    """R15.e (FL18, C7): the n==2 forms, both sides of the class."""
    from aisql.flows import inbound
    two = [pred("NULL_CHECK", subject=col("d|s|FLOW|REC_TIME",
                                          "F.REC_TIME"))] * 2
    assert inbound.condition_render(
        {"kind": "AND", "children": two}, _voice()) == \
        "Both of its parts hold."
    assert inbound.condition_render(
        {"kind": "OR", "children": two}, _voice()) == \
        "Either of its parts holds."
    assert inbound.condition_render(
        {"kind": "AND", "children": two + two[:1]}, _voice()) == \
        "All 3 of its parts hold."
    assert inbound.condition_render(
        {"kind": "OR", "children": two + two[:1]}, _voice()) == \
        "Any of its 3 parts holds."


def test_noun_phrase_gate_verb_led_falls_to_identifier():
    """R15.g (FL19, C1): a verb-led dictionary description fails
    the gate and falls to the identifier tier — never 'the stores
    the unique category identifier ... is 0'."""
    assert produce._noun_phrase(
        "Stores the unique category identifier of the medication "
        "route.", "MED_ROUTE_C") == "med route c"


def test_noun_phrase_gate_second_person_falls():
    assert produce._noun_phrase(
        "You have the ability to specify a comment.",
        "COMMENT_TXT") == "comment txt"


def test_noun_phrase_truncation_respects_parens():
    """R15.g: the comma cut never lands inside an open paren."""
    assert produce._noun_phrase(
        "The status flag (Y, N) for arrival, set nightly.",
        "ARV_FLAG") == "status flag (y, n) for arrival"


# ---- R15.c THE PACK LADDER (FL11, ruling (6)) ----

CLARITY_X = "emr@2026-01-01T00:00:00Z#clarity-pack-1.2"
SEPSIS_X = "emr@2026-01-01T00:00:00Z#sepsis-pack-1.3"


def _pack_read():
    store = Store()
    store.append_node("column", "d|s|PE|ENC_TYPE_C", {}, T0, CLARITY_X)
    store.append_node("column", "d|s|PE|ADMITTED_YN", {}, T0, CLARITY_X)
    store.append_node("column", "d|s|PE|ADM_DTTM", {}, T0, CLARITY_X)
    store.append_node("column", "d|s|PE|ROUTE_C",
                      {"description": "The route category."},
                      T0, CLARITY_X)
    store.append_node("column", "d|s|PE|FLAG_YN", {}, T0, SEPSIS_X)
    return ReadApi(store)


def _pack_voice():
    return produce._Voice(_pack_read(), TREE)


def test_pack_ladder_c_suffix_drops():
    v = _pack_voice()
    assert v.name_words(col("d|s|PE|ENC_TYPE_C",
                            "E.ENC_TYPE_C")) == "enc type"


def test_pack_ladder_yn_speaks_flag():
    v = _pack_voice()
    assert v.name_words(col("d|s|PE|ADMITTED_YN",
                            "E.ADMITTED_YN")) == "admitted yes/no flag"


def test_pack_ladder_dttm_speaks_date_and_time():
    v = _pack_voice()
    assert v.name_words(col("d|s|PE|ADM_DTTM",
                            "E.ADM_DTTM")) == "adm date and time"


def test_pack_ladder_description_outranks_convention():
    """The dictionary tier stands above the convention rung."""
    v = _pack_voice()
    assert v.subject(col("d|s|PE|ROUTE_C",
                         "E.ROUTE_C")) == "route category"


def test_pack_ladder_empty_description_uses_convention():
    v = _pack_voice()
    assert v.subject(col("d|s|PE|ENC_TYPE_C",
                         "E.ENC_TYPE_C")) == "enc type"


def test_no_pack_estate_untouched():
    """Ruling (6): estates with no packaged pack keep the readable
    identifier tier exactly as before."""
    v = _pack_voice()
    assert v.name_words(col("d|s|PE|FLAG_YN",
                            "E.FLAG_YN")) == "flag yn"


def test_records_records_guard_in_owner_voice():
    """R15.a's records-records guard (echo of the 2026-09-15
    class): MED_ADMIN_RECORDS speaks 'the med admin record's',
    never 'records record's'."""
    p = pred("COMPARE_EQ",
             subject={"kind": "column_ref", "ref": "MA.TAKEN_TIME",
                      "resolves_to": "d|s|MED_ADMIN_RECORDS|TAKEN_TIME"},
             comparand=col("d|s|ALERTS|ENC_ID", "A.ENC_ID"))
    got = produce._voice_predicate(p, _voice())
    assert got == ("The med admin record's taken time is the "
                   "alerts record's enc id.")
    assert "records record's" not in got


# ---- Brief_Description_Levels Q4 (a) (Sunny "agree with all
# seven recommendations" 2026-09-20, built at his "build it"):
# noted-label lists compress past 3; bare lists keep the ruled 6.
# RED before the bar moves. ----

def _noted(v, note):
    # literal: shape
    return {"kind": "literal", "value": v, "annotation": note}


def test_noted_list_compresses_past_three():
    """FL27: #BasePopBolus's six noted medications printed ~450
    chars — the harm is rendered length; noted lists compress
    sooner."""
    p = pred("IN_LIST",
             subject=col("d|s|PLANS|PLAN_CODE", "P.PLAN_CODE"),
             comparand_list=[_noted(700001, "SODIUM CHLORIDE"),
                             _noted(7000739, "LACTATED RINGERS"),
                             _noted(700003, "ALBUMIN"),
                             _noted(7006331, "PLASMALYTE")])
    sc = scope(from_refs=[tref("PLANS", "d|s|PLANS")], where=p,
               projection=[pm("PLAN_CODE")])
    assert sentence(sc) == ("Plans records: The plan code is one "
                            "of 4 values; carrying the plan code.")


def test_noted_list_of_three_stays_whole():
    p = pred("IN_LIST",
             subject=col("d|s|PLANS|PLAN_CODE", "P.PLAN_CODE"),
             comparand_list=[_noted(1, "A"), _noted(2, "B"),
                             _noted(3, "C")])
    sc = scope(from_refs=[tref("PLANS", "d|s|PLANS")], where=p,
               projection=[pm("PLAN_CODE")])
    assert sentence(sc) == (
        "Plans records: The plan code is one of the values 1 "
        "(noted 'A'), 2 (noted 'B'), 3 (noted 'C'); carrying the "
        "plan code.")


def test_bare_list_of_six_stays_whole():
    """The ruled 6 stands for bare lists — only the noted class
    moved."""
    p = pred("IN_LIST",
             subject=col("d|s|PLANS|PLAN_CODE", "P.PLAN_CODE"),
             comparand_list=[lit(n) for n in (1, 2, 3, 4, 5, 6)])
    sc = scope(from_refs=[tref("PLANS", "d|s|PLANS")], where=p,
               projection=[pm("PLAN_CODE")])
    assert sentence(sc) == (
        "Plans records: The plan code is one of the values 1, 2, "
        "3, 4, 5, 6; carrying the plan code.")
