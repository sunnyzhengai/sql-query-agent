"""§R13 THE CATCH-ALL — form pins on the F2 fixture estate
(authored with the DRAFT rule; Brief_M6_File_Layer approved
2026-09-17; the byte-exact USP_ED_SEPSIS pin joins at the
checkpoint after Sunny's gap-check, the answer-key precedent).

The form: "Presents: …. Population filters: …. Inner joins: …."
— sections in that order (M6-5), "; "-joined items (the
one-separator idiom), composed from the graph's OWN stored rows.

Proves: contract:aivia-design-to-code
"""
import json
import pathlib
import re

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store

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
    order = ["Presents: ", "Population filters: ", "Inner joins: "]
    for fid, td in tds.items():
        if not td:
            continue
        positions = [td.find(s) for s in order]
        present = [p for p in positions if p >= 0]
        assert present == sorted(present), fid
        assert td.startswith("Presents: "), fid


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

    from aivia.console import build_store
    store, _ = build_store("ed_sepsis_dev")
    r = ReadApi(store)
    td = inbound._render_technical_definition(
        r, "repo://sepsis-corpus/reporting/USP_ED_SEPSIS.sql")
    assert td.startswith(
        "Presents: every column of the final selection; "
        "first ip department; ")
    window = ("In the base pop selection: the arrival date is "
              "between the d start date parameter and the d end "
              "date parameter (inclusive).")
    assert window in td
    assert len(td) == RATIFIED_LEN
    assert hashlib.sha256(td.encode()).hexdigest() == RATIFIED_SHA


RATIFIED_LEN = 16195  # pinned at the checkpoint (ratified)
RATIFIED_SHA = ("fa03a7912ca553962229d6a5eb3bbb1c"
                "1a3940cb42270eef22bedb06312451ff")


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
