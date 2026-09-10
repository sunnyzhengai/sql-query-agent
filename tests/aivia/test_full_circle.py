"""Slice 7: FULL CIRCLE — one run from empty, every family proven.

Registration -> both extracts -> estate -> produce -> approve -> land
to an actual file -> observe, in ONE build; the authored expectations
of every fixture family assert against it. Plus: the F6 sweep closure
(every refusal case in the fixture maps to an implemented test — a
new case added to F6 fails this arithmetic), the two-denominator
coverage metric, the DBA-facing intake report, and the self-
containment law (no aivia module imports the old src tree).

This is the moment the new architecture can run an X-Ray engagement.

Proves: contract:aivia-design-to-code
"""
import ast
import csv
import json
import pathlib

import pytest

from aivia.flows import approve, inbound, land, produce
from aivia.graph import kg1_intake
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import census, derivation

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIX = ROOT / "AIVIA_Product" / "fixtures"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}
T0 = "2026-09-06T00:00:00Z"
RECENT = "description:usp_diabetic_visits.sql::#Recent"


@pytest.fixture(scope="module")
def circle(tmp_path_factory):
    """The whole engagement, from empty, in order."""
    out_dir = tmp_path_factory.mktemp("landed")
    store = Store()
    reg = json.loads((FIX / "F1_minimal_estate" / "registration.json")
                     .read_text())
    kg1_intake.apply_registration(store, reg)
    extract_reports = [
        inbound.receive_extract(
            store, reg,
            kg1_intake.load_snapshot(FIX / "F1_minimal_estate"
                                     / f"{src}_snapshot"),
            known_packs=KNOWN_PACKS)
        for src in ("simemr", "org")]
    estate_report = inbound.receive_estate(
        store, reg, FIX / "F2_estate_files" / "estate_snapshot")
    run_event = produce.run(store, occurred_at=T0)
    approve.rule(store, about=RECENT, ruling="accept",
                 author="person:maria", occurred_at=T0)

    export_path = out_dir / "catalog_a_descriptions.csv"

    def file_transport(payload):  # file-first: the ruled transport order
        with open(export_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(payload))
            writer.writeheader()
            writer.writerow(payload)
        return str(export_path)
    sent, receipt = land.send(store, ReadApi(store), RECENT, "catalog_a",
                              "person:admin", file_transport)
    land.observe(store, sent.identity, "published",
                 author="agent:bridge", occurred_at=T0)
    return {"store": store, "reg": reg,
            "extract_reports": extract_reports,
            "estate_report": estate_report, "run_event": run_event,
            "export_path": export_path, "sent": sent}


def test_every_fixture_family_holds_in_one_run(circle):
    store = circle["store"]
    read = ReadApi(store)
    # F1: the graph
    assert len(store.current_nodes("table")) == 7
    assert len(store.current_nodes("column")) == 21
    assert len(store.current_edges("joins_to")) == 5
    # F2: the trees
    assert len(read.trees()) == 3
    # F3: one lens spot per family (full checks live in test_lenses)
    f3 = json.loads((FIX / "F3_lenses" / "expected_lenses.json").read_text())
    assert set(census.lens_working_set(read, None)["yield"]) == \
        set(f3["working_set"]["yield"])
    # F4: byte-exact floors
    payload = json.loads((FIX / "F4_produce" / "floor_texts.json")
                         .read_text())["texts"]
    descs = {d.properties["about"][0]: d.properties["description"]
             for d in store.current_nodes("description")}
    assert descs == payload
    # F5: derived states after the script
    assert derivation.lens_standing(read, None)["yield"][RECENT] \
        == "accepted"
    assert derivation.lens_current_outcome(read, None)["yield"][
        circle["sent"].identity] == "published"


def test_landed_file_matches_the_binding(circle):
    with open(circle["export_path"]) as f:
        rows = list(csv.DictReader(f))
    binding = land.HEADERS["targets"]["catalog_a"]["description"]
    assert list(rows[0]) == binding["columns"]
    assert len(rows) == 1
    assert rows[0]["Full Name"] == "usp_diabetic_visits.sql::#Recent"
    assert rows[0]["Description"].startswith("AIVIA agent generated: ")
    assert rows[0]["Stewards"] == "person:maria"


# The F6 sweep closure: every authored case maps to an implemented
# test. Adding a case to the fixture without implementing it fails
# THIS test — coverage as arithmetic, not memory.
F6_IMPLEMENTED = {
    "R-DB": "test_refusals.test_r_db_unregistered_db",
    "R-CAPTURE": "test_refusals.test_r_capture_declared_vs_captured",
    "R-KEYLESS": "test_refusals.test_r_keyless_table_refuses_whole_extract",
    "R-FKGROUP":
        "test_refusals.test_r_fkgroup_quarantines_and_alerts_never_refuses",
    "R-ORPHANCOL": "test_refusals.test_r_orphancol_refused_not_half_created",
    "R-MIXEDSCHEMA": "test_refusals.test_r_mixedschema_refused_at_the_door",
}


def test_f6_sweep_closure():
    cases = json.loads((FIX / "F6_refusals" / "expected_refusals.json")
                       .read_text())["cases"]
    authored = {c["id"] for c in cases}
    assert authored == set(F6_IMPLEMENTED), \
        f"unswept refusal cases: {authored ^ set(F6_IMPLEMENTED)}"
    door2 = json.loads((FIX / "F6_refusals" / "phi_door2.json")
                       .read_text())["cases"]
    assert len(door2) >= 9  # exercised wholesale in test_phi_gate


def test_two_denominator_coverage_metric(circle):
    read = ReadApi(circle["store"])
    ws = census.lens_working_set(read, None)
    touched = set(ws["yield"])
    all_tables = touched | set(ws["not_touched"])
    grain_declared = {t.identity for t in read.nodes("table")
                      if t.properties.get("grain")}
    honest = (len(grain_declared & all_tables), len(all_tables))
    meaningful = (len(grain_declared & touched), len(touched))
    assert honest == (3, 7)      # all tables: the honest denominator
    assert meaningful == (3, 5)  # working set: the meaningful one
    assert len(touched) == 5     # 5 of 7 dictionary tables touched


def test_intake_report_renders_for_the_dba(circle):
    text = inbound.render_intake_report(
        circle["reg"], circle["extract_reports"],
        circle["estate_report"], ReadApi(circle["store"]))
    assert "Registered db: SIMDB" in text
    assert "[extract: simemr] loaded 6 tables, 19 columns" in text
    assert "[extract: org] loaded 1 tables, 2 columns" in text
    assert "3 table(s) with no declared grain" in text  # simemr's section
    assert "1 table(s) with no declared grain (org|org_custom|ORG_READMIT)" \
        in text
    assert "excluded (counted): dashboard.tmdl" in text
    assert "unresolved reference: L.NOTE_TXT in usp_odd_join.sql" in text
    assert "checks: pass" in text


def test_run_event_is_the_only_ledger(circle):
    events = circle["store"].current_nodes("run_event")
    assert len(events) == 1
    acct = events[0].properties["accounting"]["descriptions"]
    assert (acct["attempted"], acct["shipped"], acct["absent"]) == (4, 4, 0)


def test_aivia_is_self_contained_no_src_imports():
    """The new build never imports the old tree — the demo path stays
    untouched AND unentangled; organs were PORTED, not referenced."""
    offenders = []
    for path in sorted((ROOT / "aivia").rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name == "src" or name.startswith("src."):
                    offenders.append(f"{path.name}: {name}")
    assert offenders == []
