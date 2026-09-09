"""THE SHAPE CENSUS — integrity battery #13 (THE SHAPE CONTRACT,
Sunny's ruling 2026-09-09). The store's shape IS design: every
label and edge is declared in the Shape_Ledger registry sheet as
PRESENT or TARGET(landing step named), and these gates FAIL on any
divergence in either direction. This is the permanent lock on the
blob corpse: the parse lived as blobs while every surface spoke in
nodes, and no test could see the difference — Sunny's three
queries could, so they are law now.

  Q1  MATCH (n) RETURN labels(n), count(*)        == PRESENT nodes
  Q2  MATCH (n) WHERE n.description IS NOT NULL   == the ledger's
      RETURN labels(n), count(*)                     obligations
  Q3  MATCH ()-[r]->() RETURN type(r), count(*)   == PRESENT edges

THE VERIFICATION LAW rides with it: a mind-image stated by Sunny
becomes a standing query BEFORE code claims to satisfy it.

Proves: contract:aivia-design-to-code
"""
from collections import Counter

import pytest

from aivia.flows import connect
from aivia.graph import metamodel
from aivia.graph.read_api import ReadApi


def _ledger():
    sheet = metamodel.load("lenses").sheets["Shape_Ledger"]
    nodes, edges = {}, {}
    for r in sheet:
        if r["Kind"] == "node":
            nodes[r["Name"]] = r
        elif r["Kind"] == "edge":
            edges[r["Name"]] = r
    return nodes, edges


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    read = ReadApi(store)
    return read, connect.build_adjacency(read)


# ---- Q1: labels(n), count(*) == the ledger, both directions ----------
def test_q1_every_store_label_is_declared_and_vice_versa(world):
    read, _adj = world
    nodes, _ = _ledger()
    store_labels = {n.label for n in read.nodes(None)}
    undeclared = store_labels - set(nodes)
    assert not undeclared, (
        f"UNDECLARED store labels {sorted(undeclared)} — a label "
        f"enters the Shape_Ledger (a ruling) before it enters the "
        f"store")
    present = {n for n, r in nodes.items() if r["Status"] == "PRESENT"}
    # PRESENT and absent is a divergence UNLESS the row says the
    # count may be 0 (journal-fed / act-minted kinds)
    for name in sorted(present - store_labels):
        row = nodes[name]
        assert "may be 0" in (row.get("Notes") or ""), (
            f"ledger declares '{name}' PRESENT but the store holds "
            f"none and the row does not allow a zero count")
    # TARGET labels must NOT silently appear before their build
    targets = {n for n, r in nodes.items()
               if str(r["Status"]).startswith("TARGET")}
    early = targets & store_labels
    assert not early, (
        f"TARGET labels already in the store {sorted(early)} — "
        f"flip their ledger row to PRESENT in the same breath")


# ---- Q2: description coverage == the ledger obligation ---------------
def test_q2_description_obligations_hold(world):
    read, _adj = world
    nodes, _ = _ledger()
    for name, row in sorted(nodes.items()):
        if name == "_ruling" or row["Status"] != "PRESENT":
            continue
        ob = row["Description obligation"]
        pop = read.nodes(name)
        if not pop:
            continue
        has = sum(1 for n in pop
                  if (n.properties.get("description")
                      or n.properties.get("text")
                      or n.properties.get("definition")
                      or n.properties.get("expansions")))
        if ob.startswith("stored"):
            assert has == len(pop) or "counted-gap" in ob, (
                f"'{name}': {has}/{len(pop)} carry descriptions; "
                f"obligation is {ob!r}")
            if "counted-gap" in ob:
                assert has > 0, (
                    f"'{name}': zero descriptions under a stored "
                    f"obligation — the dictionary load is broken")
        elif ob.startswith("TARGET"):
            # the declared, counted divergence — visible, never
            # silent; flips to 'stored' at its named landing
            pass


# ---- Q3: type(r), count(*) == the ledger, both directions ------------
def test_q3_every_edge_label_is_declared_and_vice_versa(world):
    _read, adj = world
    _, edges = _ledger()
    store_edges = {lbl for es in adj.values() for _t, lbl in es}
    undeclared = store_edges - set(edges)
    assert not undeclared, (
        f"UNDECLARED edge labels {sorted(undeclared)} — an edge "
        f"enters the Shape_Ledger before it enters the graph")
    present = {n for n, r in edges.items() if r["Status"] == "PRESENT"}
    for name in sorted(present - store_edges):
        row = edges[name]
        assert "may be 0" in (row.get("Notes") or ""), (
            f"ledger declares edge '{name}' PRESENT but the graph "
            f"holds none and the row does not allow zero")


# ---- the census is also a REPORT (the gap-check bucket) --------------
def test_the_shape_report_prints_the_three_answers(world):
    read, adj = world
    nodes, edges = _ledger()
    q1 = Counter(n.label for n in read.nodes(None))
    q3 = Counter(lbl for es in adj.values() for _t, lbl in es)
    targets = [n for n, r in nodes.items()
               if str(r["Status"]).startswith("TARGET")]
    # the declared debt is VISIBLE — the report names every TARGET
    assert "statement" in targets and "condition" in targets
    assert q1 and q3  # the answers exist to print
