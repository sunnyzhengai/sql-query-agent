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
    IP_ENC = ("repo://sepsis-corpus/reporting/"
              "USP_IP_SepsisEncounters.sql")
    def scripted_scribe(evidence_by_id):
        out = {}
        for ident in evidence_by_id:
            if ident == ED_FILE:
                out[ident] = ("severe and non-severe sepsis case "
                              "identification for emergency "
                              "department encounters")
            elif ident == IP_ENC:
                out[ident] = ("inpatient sepsis admissions and "
                              "their movement history")
        return out
    drafts = describe.draft(read, targets, scripted_scribe)
    n = describe.land(store, drafts,
                      basis={"model": "scripted", "prompt_version": "test"},
                      created_at=T0)
    assert n == 2
    return store, ReadApi(store)


# ---- the scan sees what lacks aboutness ------------------------------
def test_scan_targets_files_only(bare_world):
    # Sunny's ruling (2026-09-09): reports DERIVE their description
    # from their procs through the executes edge — the Scribe never
    # drafts for a report
    _store, read = bare_world
    targets = describe.scan_undescribed(read)
    assert ED_FILE in targets
    assert DASH not in targets
    assert all(t.startswith("repo://") for t in targets)


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


def test_report_speech_derives_from_its_procs(described_world):
    """Sunny's ruling: 'the report users SHOULD see the logic' — a
    1:1 report speaks its proc's exact description; the (single)
    multi-proc report composes both; no type words either way."""
    _store, read = described_world
    entry = {"label": "pbi_report", "identity": DASH,
             "name": "ED Sepsis Screening Dashboard"}
    text = speech.speak(read, entry)
    # the dashboard executes the ED proc — its drafted aboutness
    # IS the report's speech (composed with its siblings')
    assert "sepsis case identification" in text
    assert "power bi" not in text  # type words are the label card's
    assert "displays:" in text     # its own parts still speak


def test_one_to_one_report_speaks_its_procs_exact_words(described_world):
    store, read = described_world
    # find any 1:1 report whose proc carries a description
    for n in read.nodes("pbi_report"):
        ex = n.properties.get("executes") or []
        if len(ex) == 1:
            proc_about = speech._aboutness(read, ex[0])
            if proc_about:
                entry = {"label": "pbi_report",
                         "identity": n.identity,
                         "name": n.properties["name"]}
                text = speech.speak(read, entry)
                assert text.startswith(proc_about)
                return
    raise AssertionError("no 1:1 report with a described proc")


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
