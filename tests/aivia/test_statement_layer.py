"""M5 THE STATEMENT LAYER — structural pins on the F2 fixture
estate (authored BEFORE the builder; test-first law;
Brief_M5_Statement_Layer approved 2026-09-17).

Every expectation here is RECOMPUTED from the twins each run —
no fixture-count literals. The exact dev-estate numbers (67/36/31,
44 edges) live in AIVIA_Test/test_ed_sepsis_dev_estate.py, the
acceptance surface.

Ruled: identity file::stmt/<position> (2026-09-10) · built after
scopes, before conditions (M5-1 "build order is the reverse.
after scopes") · subkind READ from the twin's T-2 field, never
re-derived (one writer, 2026-09-06) · the 31-class operational
statements store NOTHING and keep NO downward edge until M6
(counted-missing).

Proves: contract:aivia-design-to-code
"""
import json
import pathlib
import re

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake
from aivia.graph.store import Store

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


def _twin_statements(store):
    """(file_id, position, twin_node) per statement, recomputed
    from every twin blob; the twin pairs to its file by
    twin["file"] == tree["name"] (the _twin_selection precedent),
    and the file id is the tree's key."""
    name_to_fid = {n.properties["tree"].get("name"): n.identity
                   for n in store.current_nodes("file")}
    out = []
    for mt in store.current_nodes("meaning_twin"):
        twin = mt.properties["twin"]
        fid = name_to_fid.get(twin.get("file"))
        for n in twin["nodes"]:
            m = re.fullmatch(r"/statements/(\d+)",
                             n.get("points_at", ""))
            if m and n.get("kind") == "statement":
                out.append((fid, int(m.group(1)) + 1, n))
    return out


def test_every_twin_statement_is_a_store_node(built):
    store, _ = built
    twins = _twin_statements(store)
    assert twins, "F2 carries statements"
    nodes = {n.identity: n for n in store.current_nodes("statement")}
    assert len(nodes) == len(twins)
    for fid, pos, tn in twins:
        sid = f"{fid}::stmt/{pos}"
        assert sid in nodes, sid
        # subkind is READ from the twin — one writer (T-2)
        assert nodes[sid].properties.get("subkind") \
            == tn.get("subkind")


def test_statement_scope_edges_point_down(built):
    store, _ = built
    st_ids = {n.identity for n in store.current_nodes("statement")}
    lower = {n.identity for n in store.current_nodes("scope")}
    lower |= {n.identity for n in store.current_nodes("condition")}
    down = [e for e in store.current_edges("has_part")
            if e.from_id in st_ids]
    assert down, "data-producing statements parent their scopes"
    assert all(e.to_id in lower for e in down)


def test_operational_statements_are_counted_missing(built):
    """The declared M6 debt, per node: an operational statement
    has NO downward edge and NO description — both by ruling."""
    store, _ = built
    ops = [n for n in store.current_nodes("statement")
           if n.properties.get("subkind") == "operational"]
    outgoing = {e.from_id for e in store.current_edges("has_part")}
    outgoing |= {e.from_id
                 for e in store.current_edges("uses_param")}
    for n in ops:
        assert n.identity not in outgoing
        assert not n.properties.get("description")


def test_counter_matches_the_twin_recompute(built):
    """FL8 closed (Sunny 'real value'): held_statement_rooted ==
    the twins' own count of statement-rooted conditions (roots
    AND nested) — measured, never constant."""
    store, report = built
    rooted = 0
    for mt in store.current_nodes("meaning_twin"):
        for n in mt.properties["twin"]["nodes"]:
            if n.get("kind") == "condition" and re.match(
                    r"/statements/\d+/predicate",
                    n.get("points_at", "")):
                rooted += 1
    got = report.condition_layer["held_statement_rooted"]
    assert got == rooted


def test_rebooting_is_idempotent(built):
    store, _ = built
    before_nodes = len(store.current_nodes("statement"))
    before_edges = len(store.current_edges("has_part"))
    layer = inbound._store_statement_layer(
        store, "2026-09-17T00:00:00Z")
    assert len(store.current_nodes("statement")) == before_nodes
    assert len(store.current_edges("has_part")) == before_edges
    assert layer["statements"] == before_nodes
