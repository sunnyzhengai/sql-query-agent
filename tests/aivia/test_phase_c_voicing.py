"""Phase C exit (ADR 0077): the F8 phase-C answer keys go RUNNABLE.

Grammar 2.0.0 — the policy walk: the composition sentence (PC-1, the
finding-4 corpse voices at last), the voicing ledger (PC-2), the
standing corpses stay dead under the port (PC-3, asserted by the
shakedown corpse tests remaining green), and the depth cap (PC-4).
Also the line-83 side-find dies: RANGE bounds voice via the DATEADD
overlay and steward words — raw tokens never face the steward.
Requires ScriptDom — no fallback (ADR 0001).

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import inbound, produce
from aivia.graph import kg1_intake
from aivia.graph.kg2_mapper import map_tree
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import decisions

BASE = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "estates" / "sepsis"
FIX = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "fixtures"
CASES = json.loads((FIX / "F8_twin_graph" / "cases.json").read_text())
BY_ID = {c["id"]: c for fam, cases in CASES.items()
         if not fam.startswith("_") for c in cases}
READMIT = "reporting/USP_ED_SEPSIS.sql::#Base_Pop_ED_Readmit"


@pytest.fixture(scope="module")
def read():
    store = Store()
    reg = json.loads((BASE / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(BASE / "sepsis_snapshot"),
        known_packs={"sepsis-pack-1.2"})
    inbound.receive_estate(store, reg, BASE / "estate_snapshot")
    return ReadApi(store)


def test_pc1_composition_sentence_voices_the_readmit_corpse(read):
    case = BY_ID["PC-1-composition-sentence"]
    floor = produce.compose_floor(read, READMIT)
    for want in case["expect_substrings"]:
        assert want in floor, (want, floor)
    for banned in case["forbid_substrings"]:
        assert banned not in floor, (banned, floor)
    # the readmit meaning is recoverable: a second ED arrival within
    # 24 hours of departure, for records already in the base pop
    assert "hours after" in floor          # the DATEADD overlay
    assert "positive scores selection" in floor.lower() \
        or "positivescores selection" in floor.lower()


def test_pc1_no_raw_range_bounds_anywhere(read):
    # the line-83 side-find, corpus-wide: no floor may show dateadd(
    for tree in read.trees().values():
        for scope in decisions.named_scopes(tree):
            floor = produce.compose_floor(read, scope["name_key"])
            assert "dateadd(" not in floor.lower(), scope["name_key"]


def test_pc2_voicing_ledger_balances(read):
    tree = next(t for k, t in read.trees().items()
                if k.endswith("reporting/USP_ED_SEPSIS.sql"))
    for scope in decisions.named_scopes(tree):
        ledger = produce.voicing_ledger(read, scope["name_key"])
        assert ledger["voiced"] + ledger["counted"] == ledger["total"]
        assert sum(ledger["detail"].values()) == ledger["counted"]


def test_pc4_depth_cap_inline_one_counted_deeper():
    case = BY_ID["PC-4-depth-cap"]
    tree = map_tree("pc4.sql", "SELECT A.X " + case["sql"])
    scope = tree["statements"][0]["scope"]
    ledger = {}
    sentence = produce._composition_sentence(None, tree, scope, ledger)
    assert "an inline selection" in sentence          # depth 1 inlines
    assert ledger.get("deep_nesting_counted") == 1    # depth 2 counted


def test_operational_statements_never_voice_but_exist(read):
    # T-2 in the floors' world: no floor mentions index maintenance —
    # and the twin still holds every operational statement (PC-3
    # spirit: silence is policy, presence is law)
    twins = {n.properties["twin"]["file"]: n.properties["twin"]
             for n in read.nodes("meaning_twin")}
    ops = sum(t["census"]["operational"] for t in twins.values())
    assert ops == 277  # +2 PRINTs when WHILE bodies opened
    floor = produce.compose_floor(read, READMIT)
    assert "index" not in floor.lower()
