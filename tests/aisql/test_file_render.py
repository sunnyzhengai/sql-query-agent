"""§R13 v2 — THE THREE LEVELS (Brief_Pilot_Build_3, Sunny
"approved, build brief 3" 2026-09-20, amending the ratified
v2.12.0 form): headline ("Delivers …", the delivery scope's R14
sentence) → Pipeline (the statement chain wearing scope heads,
the Q5 render-join) → appendix (Presents — the M7 cherry-pick's
source, kept — then Population filters and Inner joins BOTH
grouped per selection, FL20). Form pins on the F2 fixture; the
byte-exact USP_ED_SEPSIS pin re-based by measurement (the
answer-key precedent — Sunny's gap-check eye closes the brief).

Proves: contract:aisql-design-to-code
"""
import json
import pathlib
import re

import pytest

from aisql.flows import inbound
from aisql.graph import kg1_intake
from aisql.graph.read_api import ReadApi
from aisql.graph.store import Store

FIX = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "fixtures"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


@pytest.fixture(scope="module")
def read():
    store = Store()
    reg = json.loads((FIX / "F1_minimal_estate" / "registration.json")
                     .read_text())
    kg1_intake.apply_registration(store, reg)
    for src in ("simemr", "org"):
        inbound.receive_extract(
            store, reg,
            kg1_intake.load_snapshot(FIX / "F1_minimal_estate"
                                     / f"{src}_snapshot"),
            known_packs=KNOWN_PACKS)
    inbound.receive_estate(
        store, reg, FIX / "F2_estate_files" / "estate_snapshot")
    return ReadApi(store)


def _tds(read):
    return {fid: inbound._render_technical_definition(read, fid)
            for fid in read.trees()}


def test_sections_appear_in_the_ruled_order(read):
    tds = _tds(read)
    assert any(tds.values()), "F2 renders at least one definition"
    order = ["Pipeline: ", "Presents: ", "Population filters: ",
             "Inner joins: "]
    for fid, td in tds.items():
        if not td:
            continue
        positions = [td.find(s) for s in order]
        present = [p for p in positions if p >= 0]
        assert present == sorted(present), fid
        assert td.startswith("Delivers ") \
            or "delivers nothing." in td, fid


def test_inner_joins_group_per_selection(read):
    """FL20: joins carry their selection's address, the same shape
    the filters half already owned."""
    for td in _tds(read).values():
        if "Inner joins: " not in td:
            continue
        section = td.split("Inner joins: ", 1)[1]
        assert section.startswith("In the "), section


def test_items_join_with_the_one_separator(read):
    tds = _tds(read)
    td = next(t for t in tds.values() if "Population filters: " in t)
    body = td.split("Population filters: ", 1)[1].split(".")[0]
    if ";" in body:
        assert "; " in body  # never a bare semicolon


def test_outer_joins_never_ride(read):
    """Sunny's '(inner)': a LeftOuter join's phrase must not
    appear in any definition's Inner joins section."""
    store = read._store
    outer_texts = {str(n.properties.get("description") or "").rstrip(".")
                   for n in store.current_nodes("join")
                   if str(n.properties.get("joinType") or "")
                   != "Inner"}
    outer_texts.discard("")
    for td in _tds(read).values():
        if "Inner joins: " not in td:
            continue
        section = td.split("Inner joins: ", 1)[1]
        for txt in outer_texts:
            assert txt not in section


def test_the_ratified_estate_definition_byte_exact():
    """The checkpoint pin (Sunny "ratified", 2026-09-17): the
    real USP_ED_SEPSIS catch-all, pinned by hash + length + its
    opening — byte-exact without 16K of fixture text (the
    answer-key precedent: authored from measurement, his eye the
    authority)."""
    import hashlib

    from aisql.console import build_store
    store, _ = build_store("ed_sepsis_dev")
    r = ReadApi(store)
    td = inbound._render_technical_definition(
        r, "repo://sepsis-corpus/reporting/USP_ED_SEPSIS.sql")
    assert td.startswith(
        "Delivers the final selection, carrying the last bp to "
        "first positive score time, ")
    assert "Pipeline: (5) A decision step, taken when " in td
    assert ("Presents: every column of the final selection; "
            "first ip department; ") in td
    window = ("In the base pop selection: the arrival date is "
              "between the d start date parameter and the d end "
              "date parameter (inclusive).")
    assert window in td
    assert len(td) == RATIFIED_LEN
    assert hashlib.sha256(td.encode()).hexdigest() == RATIFIED_SHA


# re-based BY MEASUREMENT at Brief_Pilot_Build_2 (R15 slice C —
# two-sided owners, the temporal-window idiom, one-library-two-
# readers, normalized join fragments; was 20255/6c5867a8… at
# Brief_Pilot_Build_3, 16195/fa03a791… at the v2.12.0
# checkpoint); Sunny's gap-check eye at the shared closing run
RATIFIED_LEN = 21411
RATIFIED_SHA = ("73f6ad264080ff3129fdbe441165d10a"
                "f16ff5d2c5c42826131fb31fc75bc4b0")


def test_definition_is_deterministic(read):
    once = _tds(read)
    again = _tds(read)
    assert once == again


def test_no_raw_identifiers_in_presents(read):
    """Passthroughs speak the readable-name fold — never a raw
    UPPER_SNAKE identifier (the R5.b line for author words)."""
    for td in _tds(read).values():
        if not td.startswith("Presents: "):
            continue
        head = td.split("Population filters: ")[0] \
            .split("Inner joins: ")[0]
        assert not re.search(r"\b[A-Z]{2,}_[A-Z_]+\b", head), td
