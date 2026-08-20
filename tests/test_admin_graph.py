"""The admin graph projection (ADR 0048 item 3, spec §14b).

Laws under test: B1 (every edge has a witness — endpoints exist and
come from registry/event rows), D3 (pure projection — deterministic,
rebuilt identically), C1 reflexive (the extraction registry declares
the admin graph's source kind).
"""

from src.admin_graph import EDGE_TYPES, NODE_KINDS, build_admin_graph
from src.extraction_registry import EXTRACTION_REGISTRY
from src.notebook_registry import NOTEBOOK_REGISTRY
from src.schemas import TABLE_REGISTRY
from src.trace_registry import TRACE_REGISTRY


def test_every_edge_endpoint_exists_b1():
    out = build_admin_graph()
    ids = {n["node_id"] for n in out.nodes_rows}
    for e in out.edges_rows:
        assert e["source_id"] in ids, e
        assert e["target_id"] in ids, e
        assert e["edge_type"] in EDGE_TYPES, e


def test_kinds_are_the_closed_set():
    out = build_admin_graph()
    assert {n["kind"] for n in out.nodes_rows} <= set(NODE_KINDS)


def test_registry_coverage_every_contract_notebook_adr_projects():
    out = build_admin_graph()
    ids = {n["node_id"] for n in out.nodes_rows}
    for table in TABLE_REGISTRY:
        assert f"contract:{table}" in ids
    for nb in NOTEBOOK_REGISTRY:
        assert f"notebook:{nb}" in ids
    for adr in TRACE_REGISTRY:
        assert f"adr:{adr}" in ids


def test_produces_edges_match_table_registry_owners():
    out = build_admin_graph()
    produces = {(e["source_id"], e["target_id"]) for e in out.edges_rows
                if e["edge_type"] == "produces"}
    for table, contract in TABLE_REGISTRY.items():
        owner = (contract.get("owner") or {}).get("notebook")
        if owner and owner in NOTEBOOK_REGISTRY:
            assert (f"notebook:{owner}", f"contract:{table}") in produces


def test_implements_and_grounds_edges_match_trace_registry():
    out = build_admin_graph()
    implements = {(e["source_id"], e["target_id"]) for e in out.edges_rows
                  if e["edge_type"] == "implements"}
    grounds = {(e["source_id"], e["target_id"]) for e in out.edges_rows
               if e["edge_type"] == "grounds"}
    assert ("module:src/tree/diff.py", "adr:0044") in implements
    assert ("adr:0044", "axiom:F") in grounds


def test_error_rows_project_to_violates_edges():
    rows = [{"error_id": "e1", "reason_code": "missing",
             "reason_text": "input_dict_tables missing",
             "contract_id": "contract:input_dict_tables"},
            {"error_id": "e2", "reason_code": "unmatched",
             "contract_id": "contract:not_a_real_table"}]
    out = build_admin_graph(error_rows=rows)
    violates = [(e["source_id"], e["target_id"]) for e in out.edges_rows
                if e["edge_type"] == "violates"]
    assert any(t == "contract:input_dict_tables" for _, t in violates)
    # an unmatchable contract_id yields a node but no dangling edge
    assert all(t != "contract:not_a_real_table" for _, t in violates)
    ids = {n["node_id"] for n in out.nodes_rows}
    for e in out.edges_rows:
        assert e["source_id"] in ids and e["target_id"] in ids


def test_projection_is_deterministic_d3():
    a, b = build_admin_graph(), build_admin_graph()
    assert a.nodes_rows == b.nodes_rows
    assert a.edges_rows == b.edges_rows


def test_extraction_registry_declares_the_admin_source_c1_reflexive():
    row = EXTRACTION_REGISTRY["admin_governance_registries"]
    assert row["status"] == "extracted"
    assert row["extractor"]["module"] == "src/admin_graph.py"


def test_diagnosis_path_walks_symptom_to_decision():
    """The E3 shape: error —violates→ contract —produced_by→ notebook,
    and the contract's gate module —implements→ its ADR. Every hop a
    real edge — this is the walk the companion captions."""
    rows = [{"error_id": "x", "reason_code": "is empty",
             "contract_id": "contract:input_dict_tables"}]
    out = build_admin_graph(error_rows=rows)
    edges = out.edges_rows
    (violated,) = [e["target_id"] for e in edges
                   if e["edge_type"] == "violates"]
    producers = [e["source_id"] for e in edges
                 if e["edge_type"] == "produces" and e["target_id"] == violated]
    assert producers == ["notebook:040_dict_clarity"]
    enforcer = [e["target_id"] for e in edges
                if e["edge_type"] == "enforced_by" and e["source_id"] == violated]
    assert enforcer == ["module:src/steps/gates.py"]
    decisions = [e["target_id"] for e in edges
                 if e["edge_type"] == "implements" and e["source_id"] == enforcer[0]]
    assert "adr:0039" in decisions or "adr:0042" in decisions
