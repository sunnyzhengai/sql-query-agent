"""E1 — THE SPEECH CONTRACT build (ruled 2026-09-09, Scribe route).

The contract (Design_Graph_Engine.md): a node's speech is ITS OWN
ABOUTNESS — never its sources' descriptions (the 4,600-char wall),
never its name, never its type words. The Scribe drafts one
aboutness sentence per file/report from the structural evidence;
drafts land as kg3 description artifacts, machine-authored with
status 'drafted' and a basis stamp; estate data loads them at boot
(builders never journal); an undescribed file speaks NOTHING and is
a COUNTED gap — never a wall.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import describe, speech
from aivia.graph.read_api import ReadApi

T0 = "2026-09-09T12:00:00Z"

ED_FILE = "repo://sepsis-corpus/reporting/USP_ED_SEPSIS.sql"
DASH = "pbi://sepsis/ed-sepsis-screening-dashboard"


@pytest.fixture(scope="module")
def bare_world():
    """The estate WITHOUT descriptions — the pre-Scribe state."""
    from aivia.console import build_store
    store, _ = build_store("sepsis", descriptions=False)
    return store, ReadApi(store)


@pytest.fixture(scope="module")
def described_world():
    """The estate + scripted Scribe drafts landed the estate-data
    way (receive_descriptions), exactly as prod boots."""
    from aivia.console import build_store
    store, _ = build_store("sepsis", descriptions=False)
    read = ReadApi(store)
    targets = describe.scan_undescribed(read)
    def scripted_scribe(evidence_by_id):
        out = {}
        for ident in evidence_by_id:
            if ident == ED_FILE:
                out[ident] = ("severe and non-severe sepsis case "
                              "identification for emergency "
                              "department encounters")
            elif ident == DASH:
                out[ident] = ("emergency department sepsis "
                              "screening: screening detail, ed "
                              "summary, inpatient rollup")
        return out
    drafts = describe.draft(read, targets, scripted_scribe)
    n = describe.land(store, drafts,
                      basis={"model": "scripted", "prompt_version": "test"},
                      created_at=T0)
    assert n == 2
    return store, ReadApi(store)


# ---- the scan sees what lacks aboutness ------------------------------
def test_scan_finds_files_and_reports_without_descriptions(bare_world):
    _store, read = bare_world
    targets = describe.scan_undescribed(read)
    assert ED_FILE in targets
    assert DASH in targets


def test_evidence_is_the_nodes_own_anatomy(bare_world):
    _store, read = bare_world
    ev = describe.evidence(read, ED_FILE)
    # the structural voicing IS the evidence the Scribe distills
    assert "sepsis" in ev.lower()


# ---- drafts land attributed, journal-free ----------------------------
def test_drafts_land_as_machine_descriptions_with_basis(described_world):
    _store, read = described_world
    node = next(n for n in read.nodes("description")
                if ED_FILE in (n.properties.get("about") or []))
    assert node.properties["status"] == "drafted"
    assert "scribe" in node.properties["author"]
    assert node.properties["basis"]["model"] == "scripted"


# ---- the speech card obeys the contract ------------------------------
def test_described_file_speaks_aboutness_not_the_wall(described_world):
    _store, read = described_world
    entry = {"label": "file", "identity": ED_FILE,
             "name": "USP_ED_SEPSIS"}
    text = speech.speak(read, entry)
    assert "sepsis case identification" in text
    # the wall is DEAD: no source-table catalog recitals, no
    # boilerplate lead
    assert "this is a selection of records" not in text
    assert "the patients table holds" not in text
    assert len(text) < 300


def test_undescribed_file_is_a_counted_gap_not_a_wall(bare_world):
    _store, read = bare_world
    entry = {"label": "file", "identity": ED_FILE,
             "name": "USP_ED_SEPSIS"}
    assert speech.speak(read, entry) == ""


def test_description_overrides_pbi_type_words(described_world):
    _store, read = described_world
    entry = {"label": "PBI Report", "identity": DASH,
             "name": "ED Sepsis Screening Dashboard"}
    text = speech.speak(read, entry)
    assert "screening" in text
    assert "power bi" not in text  # type words are the label card's
    assert "displays:" in text     # its own parts still speak


# ---- boot loads committed drafts as estate data ----------------------
def test_boot_loads_descriptions_when_present(tmp_path):
    import json

    from aivia.console import build_store
    from aivia.flows import inbound
    store, _ = build_store("sepsis", descriptions=False)
    p = tmp_path / "descriptions.json"
    p.write_text(json.dumps({
        "author": "agent:scribe", "created_at": T0,
        "basis": {"model": "m", "prompt_version": "1"},
        "descriptions": {ED_FILE: "an aboutness sentence"}}))
    n = inbound.receive_descriptions(store, p)
    assert n == 1
    read = ReadApi(store)
    entry = {"label": "file", "identity": ED_FILE,
             "name": "USP_ED_SEPSIS"}
    assert speech.speak(read, entry) == "an aboutness sentence"
