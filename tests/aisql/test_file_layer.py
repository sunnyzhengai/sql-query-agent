"""M6 THE FILE LAYER — structural pins on the F2 fixture estate
(authored BEFORE the builder; test-first law;
Brief_M6_File_Layer approved 2026-09-17).

Twin/tree-recomputed expectations, no fixture-count literals.
The exact dev-estate numbers (67 + 4 edges, the two fields) live
in AIVIA_Test/test_ed_sepsis_dev_estate.py.

Ruled: file—has_part→statement for EVERY statement (the debt
retirement mechanism) + file—has_part→param; the technical
definition is deterministic (verbatim: stored == recomputed);
the description stores ONLY approved artifact text — no
approval, no description, the emptiness counted (never a
placeholder phrase).

Proves: contract:aisql-design-to-code
"""
import json
import pathlib

import pytest

from aisql.flows import inbound
from aisql.graph import kg1_intake
from aisql.graph.read_api import ReadApi
from aisql.graph.store import Store

FIX = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "fixtures"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


@pytest.fixture(scope="module")
def built():
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
    report = inbound.receive_estate(
        store, reg, FIX / "F2_estate_files" / "estate_snapshot")
    return store, report


def test_every_statement_birth_edges_from_its_file(built):
    """The debt-retirement mechanism, recomputed per file: the
    file parents ALL its statements — operational included."""
    store, _ = built
    hp = {}
    for e in store.current_edges("has_part"):
        hp.setdefault(e.from_id, set()).add(e.to_id)
    read = ReadApi(store)
    for key, tree in sorted(read.trees().items()):
        want = {f"{key}::stmt/{i + 1}"
                for i in range(len(tree["statements"]))}
        assert want, "F2 files carry statements"
        assert want <= hp.get(key, set()), key


def test_params_birth_edge_from_their_file(built):
    store, _ = built
    p_ids = {n.identity for n in store.current_nodes("param")}
    if not p_ids:
        pytest.skip("F2 carries no params")
    hp_targets = {e.to_id for e in store.current_edges("has_part")}
    assert p_ids <= hp_targets


def test_technical_definition_stored_and_verbatim(built):
    """R13, verbatim law at file grain: stored == recomputed."""
    store, _ = built
    read = ReadApi(store)
    for n in store.current_nodes("file"):
        td = n.properties.get("technical_definition")
        assert td and td.strip(), n.identity
        assert td == inbound._render_technical_definition(
            read, n.identity)


def test_description_never_stored_without_approval(built):
    """The approval gate: F2 has NO approved description
    artifacts, so file.description stays ABSENT — counted, never
    a placeholder phrase (the (b)-ruling posture at file grain)."""
    store, _ = built
    approved_about = set()
    for n in store.current_nodes("description"):
        if n.properties.get("status") == "approved":
            approved_about.add(str(n.properties.get("about", "")))
    for n in store.current_nodes("file"):
        if not any(n.identity in a for a in approved_about):
            assert not n.properties.get("description"), n.identity


def test_rebooting_is_idempotent(built):
    store, _ = built
    before = len(store.current_edges("has_part"))
    layer = inbound._store_file_layer(store, "2026-09-17T00:00:00Z")
    assert len(store.current_edges("has_part")) == before
    assert layer["files"] == len(store.current_nodes("file"))
