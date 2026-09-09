"""STEP D (promoted) — LABEL, not kind. The industry-standard term
(Neo4j, GQL, Fabric graph) everywhere a node's type is named;
Sunny's standing ruling (feedback: use standards; the invented
'kind' cost weeks of confusion).

Scope: the GRAPH node-type surfaces — the store field, the read
API, index entries, hits, registry sheets. NOT the twin's ratified
meaning-node taxonomy (the kind library: COMPARE_EQ, selection...)
— a different concept, documented in the design doc.

Proves: contract:aivia-design-to-code
"""

from aivia.graph.kg1_intake import new_store
from aivia.graph.read_api import ReadApi

T0 = "2026-09-08T12:00:00Z"


def test_the_store_speaks_label():
    store = new_store()
    store.append_node("table", "emr|dbo|T", {"description": "d"},
                      T0, "probe")
    node = store.current_nodes("table")[0]
    assert node.label == "table"
    assert not hasattr(node, "kind")


def test_the_read_api_speaks_label():
    store = new_store()
    store.append_node("table", "emr|dbo|T", {}, T0, "probe")
    read = ReadApi(store)
    assert [n.label for n in read.nodes("table")] == ["table"]
    assert {n.label for n in read.nodes(None)} == {"table"}


def test_index_entries_carry_label():
    from aivia.console import build_store
    from aivia.flows import ask
    store, _ = build_store("sepsis")
    index = ask.build_index(ReadApi(store))
    assert all("label" in e and "kind" not in e for e in index)
    labels = {e["label"] for e in index}
    assert "table" in labels and "file" in labels


def test_registry_sheets_speak_label():
    from aivia.graph import metamodel
    lenses = metamodel.load("lenses").sheets
    for row in lenses["Speech_Sources"]:
        assert "Label" in row and "Kind" not in row
    for row in lenses["Connection_Ledger"]:
        assert "Label" in row and "Kind" not in row
    kg1 = metamodel.load("kg1_technical").sheets
    assert all("Node label" in r for r in kg1["Node_Types"])


def test_no_kind_surface_remains_in_the_search_path():
    import pathlib
    for mod in ("aivia/graph/store.py", "aivia/graph/read_api.py",
                "aivia/flows/ask.py", "aivia/flows/speech.py",
                "aivia/flows/censuses.py"):
        src = pathlib.Path(mod).read_text()
        assert '.kind' not in src, mod
        assert '"kind"' not in src, mod
