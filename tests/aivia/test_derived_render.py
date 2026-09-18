"""R12 THE COMPUTED OUTPUT (Grammar v2.10.0, ratified Sunny
2026-09-16) — byte-exact fixture pins authored BEFORE the renderer
(test-first law). The phrase shape: name words + the defining
phrase, voiced inside-out through THE FUNCTION-VOICING LIBRARY
(kg2_kind_library Function_Voicings, registries 1.44.0). Composite
kinds voice by rule: case standing phrase, cast TRANSPARENT, unary
sign-fold, arithmetic operator words. An unlisted operation renders
the safe fallback and lands a COUNTED remainder. The ADR 0076
value() overlays (COALESCE, LEFT/RIGHT, DATEADD) absorb into the
same fills — their condition-context phrases stay BYTE-IDENTICAL
(the verbatim law guards M3's stored texts).

Proves: contract:aivia-design-to-code
"""
from aivia.flows import produce
from aivia.graph import metamodel
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store

T0 = "2026-09-16T12:00:00Z"
BIRTH = "d|s|PATIENT|BIRTH_DATE"
ARRIVE = "d|s|ENC|ADT_ARRIVAL_TIME"
MEAS = "d|s|FLOW|MEAS_VALUE"
DOSE = "d|s|MED|DOSE_AMT"


def _voice():
    store = Store()
    cols = {
        BIRTH: {"description": "Date of birth.", "data_type": "datetime"},
        ARRIVE: {"description": "Arrival instant.", "data_type": "datetime"},
        MEAS: {"description": "Measured value.", "data_type": "varchar(20)"},
        DOSE: {"description": "Dose amount.", "data_type": "numeric(8,2)"},
    }
    for cid, props in cols.items():
        store.append_node("column", cid, dict(props), T0, "x1")
    blessed = {BIRTH: "birth date", ARRIVE: "arrival time",
               MEAS: "measured value", DOSE: "dose amount"}
    for i, (target, words) in enumerate(sorted(blessed.items()), 1):
        store.append_node("blessed_name", f"blessed#{i}",
                          # literal: shape
                          {"target": target, "words": words}, T0, "x1")
    return produce._Voice(ReadApi(store), {"parameters": []})


def col(cid, name):
    # literal: shape
    return {"kind": "column_ref", "ref": f"T.{name}", "resolves_to": cid}


def lit(value):
    # literal: shape
    return {"kind": "literal", "value": value}


def fn(name, *args, **extra):
    # literal: shape
    return {"kind": "function", "name": name, "args": list(args), **extra}


def member(name, expression):
    # literal: shape
    return {"node": "projection_member", "name": name,
            "expression": expression}


# ---- the AGE_IN_DAYS walkthrough: nesting voices inside-out ----

def test_datediff_nested_in_floor():
    m = member("AGE_IN_DAYS",
               fn("FLOOR", fn("DATEDIFF", lit("day"),
                              col(BIRTH, "BIRTH_DATE"),
                              col(ARRIVE, "ADT_ARRIVAL_TIME"))))
    assert produce.derived_phrase(m, _voice()) == (
        "Age in days: the number of days between the birth date and "
        "the arrival time, rounded down to a whole number.")


# ---- composite kinds voice by rule ----

def test_case_speaks_the_standing_phrase():
    m = member("SEPSIS_FLAG", {"kind": "case", "whens": []})
    assert produce.derived_phrase(m, _voice()) == (
        "Sepsis flag: a value derived by rule.")


def test_cast_is_transparent():
    m = member("EncWeight",
               {"kind": "cast", "args": [col(MEAS, "MEAS_VALUE")]})
    assert produce.derived_phrase(m, _voice()) == (
        "Enc weight: the measured value.")


def test_unary_sign_folds():
    m = member("NEG_DOSE", {"kind": "unary", "op": "Negative",
                            "args": [col(DOSE, "DOSE_AMT")]})
    assert produce.derived_phrase(m, _voice()) == (
        "Neg dose: negative the dose amount.")


def test_arithmetic_speaks_operator_words():
    m = member("KG_WEIGHT", {"kind": "arithmetic", "op": "Multiply",
                             "args": [col(MEAS, "MEAS_VALUE"),
                                      lit("0.0283495")]})
    assert produce.derived_phrase(m, _voice()) == (
        "Kg weight: the measured value times 0.0283495.")


# ---- the library rows ----

def test_row_number_renders_slotless():
    # over contents are a mapper flag, not contents — the slotted
    # template is DEFERRED with its recorded reason (registry row)
    m = member("FIRST_TIME_LINE", fn("ROW_NUMBER", over=True))
    assert produce.derived_phrase(m, _voice()) == (
        "First time line: the record's position in its ordered "
        "sequence.")


def test_min_temporal_says_earliest():
    m = member("FIRST_ARRIVAL", fn("MIN", col(ARRIVE, "ADT_ARRIVAL_TIME")))
    assert produce.derived_phrase(m, _voice()) == (
        "First arrival: the earliest arrival time.")


def test_min_non_temporal_says_smallest():
    m = member("MIN_DOSE", fn("MIN", col(DOSE, "DOSE_AMT")))
    assert produce.derived_phrase(m, _voice()) == (
        "Min dose: the smallest dose amount.")


def test_charindex_and_left():
    m = member("SYSTOLIC",
               fn("LEFT", col(MEAS, "MEAS_VALUE"),
                  fn("CHARINDEX", lit("'/'"), col(MEAS, "MEAS_VALUE"))))
    assert produce.derived_phrase(m, _voice()) == (
        "Systolic: the first the position of '/' within the measured "
        "value characters of the measured value.")


def test_isnull_round_datename():
    v = _voice()
    m = member("R", fn("ROUND", col(DOSE, "DOSE_AMT"), lit(2)))
    assert produce.derived_phrase(m, v) == (
        "R: the dose amount rounded to 2 decimal places.")
    m = member("I", fn("ISNULL", col(DOSE, "DOSE_AMT"), lit(0)))
    assert produce.derived_phrase(m, v) == (
        "I: the dose amount, or 0 when the dose amount is not "
        "recorded.")
    m = member("MONTH_NAME", fn("DATENAME", lit("month"),
                                col(ARRIVE, "ADT_ARRIVAL_TIME")))
    assert produce.derived_phrase(m, v) == (
        "Month name: the name of the month of the arrival time.")


# ---- THE STUFF LIST IDIOM (Sunny 2026-09-16: 'rule the idiom') ----

def test_stuff_for_xml_speaks_list_joining():
    inner = {"node": "scope", "projection": [
        # literal: shape
        {"node": "projection_member", "name": None,
         "expression": {"kind": "arithmetic", "op": "Add",
                        "args": [lit("','"),
                                 {"kind": "cast",
                                  "args": [col(MEAS, "MEAS_VALUE")]}]}}]}
    m = member("AllSepsis_Scores",
               fn("STUFF", {"kind": "subquery_ref", "scope": inner},
                  lit(1), lit(1), lit("''")))
    assert produce.derived_phrase(m, _voice()) == (
        "All sepsis scores: every measured value joined into one "
        "list.")


def test_stuff_literal_row_survives_for_non_idiom():
    m = member("PATCHED", fn("STUFF", col(MEAS, "MEAS_VALUE"),
                             lit(1), lit(3), lit("'xy'")))
    assert produce.derived_phrase(m, _voice()) == (
        "Patched: the measured value with a segment replaced by "
        "'xy'.")


# ---- named literals, nameless members ----

def test_named_literal_is_the_constant():
    m = member("SEPSIS_ALERT_CANC_FLAG", lit("'Y'"))
    assert produce.derived_phrase(m, _voice()) == (
        "Sepsis alert canc flag: the constant 'Y'.")


def test_nameless_member_speaks_the_phrase_alone():
    m = member(None, {"kind": "arithmetic", "op": "Add",
                      "args": [lit("','"), col(MEAS, "MEAS_VALUE")]})
    assert produce.derived_phrase(m, _voice()) == (
        "',' plus the measured value.")


# ---- the counted remainder ----

def test_unlisted_operation_falls_back_counted():
    v = _voice()
    m = member("MYSTERY", fn("NONSENSE_FN", col(BIRTH, "BIRTH_DATE")))
    assert produce.derived_phrase(m, v) == (
        "Mystery: a value computed from the birth date.")
    assert v.function_remainders == {"NONSENSE_FN": 1}


# ---- ADR 0076 absorption: value() phrases stay BYTE-IDENTICAL ----

def test_dateadd_value_parity():
    v = _voice()
    one = fn("DATEADD", lit("HH"), lit("1"), col(ARRIVE, "X"))
    two = fn("DATEADD", lit("HH"), lit("2"), col(ARRIVE, "X"))
    assert v.value(one, one) == "1 hour after the arrival time"
    assert v.value(two, two) == "2 hours after the arrival time"


def test_coalesce_and_left_value_parity():
    v = _voice()
    e = fn("COALESCE", col(ARRIVE, "A"), col(BIRTH, "B"))
    assert v.value(e, e) == ("the first recorded of the arrival time, "
                             "the birth date")
    e = fn("LEFT", col(MEAS, "M"), lit("3"))
    assert v.value(e, e) == "the first 3 characters of the measured value"


# ---- the registry mirror: code skeletons == the sheet ----

def test_skeletons_mirror_the_registry():
    sheet = metamodel.load("kg2_kind_library").sheets["Function_Voicings"]
    rows = {r["Operation"]: r for r in sheet if r["Operation"] != "_ruling"}
    tmpl_col = "Voicing template (DRAFT — Sunny gap-checks phrasing)"
    closed = next(
        r for r in metamodel.load("kg2_kind_library").sheets["Closed_Sets"]
        if r["Set"] == "FUNCTION_VOICING_OPS")["Members"].split("|")
    assert set(closed) <= set(rows)
    for op_name, skeleton in produce.FN_SKELETONS.items():
        row = rows.get(op_name) or rows.get("STUFF + FOR XML PATH('')")
        assert skeleton in row[tmpl_col], (op_name, skeleton)
    for op_name in closed:
        assert op_name in produce.FN_SKELETONS or op_name == "STUFF", \
            f"registry op {op_name} has no code fill"


def test_grammar_version_bumped():
    assert produce.FLOOR_GRAMMAR_VERSION == "2.12.0"
