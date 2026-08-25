"""L0 for the org_config referential-integrity audit (ops find 2,
2026-08-24 — the 610 dead-agent corpse): the reference collector is
pure and pinned; the live resolution runs in the script."""

from devtools.org_config_audit import collect_refs


def test_collects_the_three_fabric_graph_refs():
    refs = collect_refs({"fabric_graph": {
        "workspace_id": "ws1", "data_agent_id": "agent1",
        "graph_model_id": "gm1"}})
    by_key = {r["key"]: r for r in refs}
    assert set(by_key) == {"fabric_graph.workspace_id",
                           "fabric_graph.data_agent_id",
                           "fabric_graph.graph_model_id"}
    # the 610 class is a HARD failure; the unread graph model warns
    assert by_key["fabric_graph.data_agent_id"]["severity"] == "fail"
    assert "610" in by_key["fabric_graph.data_agent_id"]["remedy"]
    assert by_key["fabric_graph.graph_model_id"]["severity"] == "warn"


def test_absent_keys_collect_nothing():
    assert collect_refs({}) == []
    assert collect_refs({"fabric_graph": {}}) == []
