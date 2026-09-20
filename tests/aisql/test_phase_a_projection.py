"""Phase A exit (ADR 0077): the F8 phase-A answer keys go RUNNABLE.

The fixture (AIVIA_Product/fixtures/F8_twin_graph/cases.json) is the
truth — authored before this build; these tests walk its assertions
against the BUILT mapper. Covers: projection members captured with
name + expression subtree (PA-1, the FIRST_TIME_LINE / Gap B corpse),
the INTO write-target law (PA-2), the star counted-remainder branch
(PA-3), plus the conservation consequence the build surfaced:
non-scalar select elements were previously skipped SILENTLY — now
every select element is a member or a counted remainder row.
Requires ScriptDom — no fallback (ADR 0001).

Proves: contract:aisql-design-to-code
"""
import json
import pathlib

from aisql.graph import metamodel
from aisql.graph.kg2_mapper import METAMODEL_VERSION, map_tree

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
CASES = json.loads((FIX / "F8_twin_graph" / "cases.json").read_text())
BY_ID = {c["id"]: c for fam, cases in CASES.items()
         if not fam.startswith("_") for c in cases}


def _scope(tree, index=0):
    scoped = [s["scope"] for s in tree["statements"] if s.get("scope")]
    return scoped[index]


def test_pa1_derived_column_member_captured():
    case = BY_ID["PA-1-derived-column-corpse"]
    tree = map_tree("pa1.sql", case["sql"])
    scope = _scope(tree)
    assert "PROJECTION" in scope["structures"]
    members = scope["projection"]
    assert len(members) == 2
    assert [m["position"] for m in members] == [1, 2]
    first, second = members
    assert first["name"] == "ENCOUNTER_ID"
    assert first["expression"]["kind"] == "column_ref"
    assert second["name"] == "FIRST_TIME_LINE"
    # "window function" in the answer key = function + over marker;
    # Expression_Kinds stays closed (RG-C3), OVER is a property —
    # slice E (Brief_Pilot_Build_3, metamodel 1.50.0): the property
    # carries CONTENTS now, truthy wherever the old flag was read
    assert second["expression"]["kind"] == "function"
    assert second["expression"]["name"] == "ROW_NUMBER"
    over = second["expression"].get("over")
    assert isinstance(over, dict) and bool(over)
    assert "partition_by" in over and "order_by" in over
    assert tree["remainder"] == []


def test_pa2_select_into_single_member():
    case = BY_ID["PA-2-select-into"]
    tree = map_tree("pa2.sql", case["sql"])
    stmt = next(s for s in tree["statements"] if s.get("scope"))
    scope = stmt["scope"]
    members = scope["projection"]
    assert len(members) == 1
    assert members[0]["name"] == "ENCOUNTER_ID"
    # INTO names a WRITE TARGET, never a read (DESC-TEMP-1 law):
    # the scope is NAMED for the target; from_refs never contain it
    assert stmt["statement_kind"] == "SELECT INTO"
    assert scope["name"] == "#Base_Pop_ED_Readmit"
    read = {r["table_ref"] for r in scope["from_refs"]}
    assert "#Base_Pop_ED_Readmit" not in read


def test_pa3_star_is_meaning_never_enumeration():
    # RULED 2026-09-06 (plug-all-holes sweep): a star's meaning is
    # 'every column of the source at read time' — total by reference,
    # never an enumerated list (enumeration would freeze a column set
    # the source can outgrow: the drift hazard the interim counted
    # posture was waiting on)
    case = BY_ID["PA-3-star-remainder"]
    tree = map_tree("pa3.sql", case["sql"])
    scope = _scope(tree)
    assert len(scope["projection"]) == 1
    star = scope["projection"][0]
    assert star.get("star") is True and star["name"] is None
    assert star["expression"]["kind"] == "star"
    assert tree["remainder"] == []


def test_every_select_element_is_member_or_counted():
    # the silent-skip hole, closed: a SELECT @v = x element is neither
    # scalar member nor star — it must land in the counted remainder
    tree = map_tree("setvar.sql", "SELECT @n = COUNT(*) FROM PATIENT")
    scope = _scope(tree)
    counted = [r for r in tree["remainder"]
               if r["reason"] in ("star_projection",
                                  "unmapped select element")]
    assert len(scope["projection"]) + len(counted) == 1


def test_trees_stamp_the_metamodel_version():
    # the bump IS the re-parse trigger: a stamped tree under an old
    # version differs from its re-map, so idempotence regenerates it
    tree = map_tree("stamp.sql", "SELECT PATIENT_ID FROM PATIENT")
    assert tree["metamodel_version"] == METAMODEL_VERSION
    assert METAMODEL_VERSION == metamodel.load("kg2_kind_library").version


def test_projection_kind_is_in_the_ratified_registry():
    kl = metamodel.load("kg2_kind_library")
    kinds = {r["Kind"] for r in kl.sheets["Structure_Kinds_Phase_A"]}
    assert "PROJECTION" in kinds
