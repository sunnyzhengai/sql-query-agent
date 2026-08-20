"""The admin graph — the system's own governance, projected walkable
(ADR 0048 item 3; executes ADR 0039's planned follow-up; spec §14b).

A second Σ-structure over the same axiom groups: nodes are the
system's governance artifacts (contracts, notebooks, modules, ADRs,
axioms, error events, checklist rows), edges are deterministic
projections of registry and event-table truth. The witness rule
(spec:B1) applies — every edge here has a registry entry or event row
behind it; nothing is inferred. The graph is a PROJECTION (spec:D3):
rebuilt from the registries + event tables each run by 500_validate,
never a second truth.

Diagnosis is a path in this graph, captioned (E3 discipline): symptom
→ error event —violates→ contract —produced_by→ notebook —implements→
ADR → remediation, every hop a real edge.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.notebook_registry import NOTEBOOK_REGISTRY
from src.schemas import TABLE_REGISTRY
from src.trace_registry import SPEC_AXIOMS, TRACE_REGISTRY

NODE_KINDS = ("contract", "notebook", "module", "adr", "axiom",
              "error", "checklist")
EDGE_TYPES = ("produces", "enforced_by", "implements", "grounds",
              "traced_by", "violates")

# The one executable gate home: contracts are enforced by the gates
# that execute them at every notebook boundary (src/steps/gates.py —
# "gates cannot drift from the contracts because they ARE the
# contracts, executed").
GATE_MODULE = "src/steps/gates.py"


@dataclass
class AdminGraphOutput:
    nodes_rows: "list[dict]" = field(default_factory=list)
    edges_rows: "list[dict]" = field(default_factory=list)


def _node(node_id: str, kind: str, name: str, description: str = "") -> dict:
    return {"node_id": node_id, "kind": kind, "name": name,
            "description": (description or "")[:500]}


def _edge(source_id: str, target_id: str, edge_type: str) -> dict:
    return {"source_id": source_id, "target_id": target_id,
            "edge_type": edge_type}


def build_admin_graph(
    error_rows: "list[dict] | None" = None,
    checklist_rows: "list[dict] | None" = None,
) -> AdminGraphOutput:
    """Project the registries (+ optional event rows) into nodes/edges.

    error_rows: dicts with at least an id-ish field and contract_id
    (ops_installation_errors / ops_runtime_error_events / ops_fallout
    shapes all qualify — anything carrying contract_id).
    checklist_rows: ops_human_checklist rows (id + optional contract_id).
    Deterministic: same inputs, same output, stable order.
    """
    out = AdminGraphOutput()
    node_ids: "set[str]" = set()

    def add_node(row: dict) -> None:
        if row["node_id"] not in node_ids:
            node_ids.add(row["node_id"])
            out.nodes_rows.append(row)

    # --- registry-derived nodes -----------------------------------
    for name in sorted(TABLE_REGISTRY):
        contract = TABLE_REGISTRY[name]
        add_node(_node(f"contract:{name}", "contract", name,
                       contract.get("description", "")))
    for nb in sorted(NOTEBOOK_REGISTRY):
        add_node(_node(f"notebook:{nb}", "notebook", nb,
                       NOTEBOOK_REGISTRY[nb].get("purpose", "")))
    for adr in sorted(TRACE_REGISTRY):
        entry = TRACE_REGISTRY[adr]
        add_node(_node(f"adr:{adr}", "adr", entry["title"],
                       f"category: {entry['category']}"))
        for path in entry["modules"] + entry["tests"]:
            add_node(_node(f"module:{path}", "module", path))
    for axiom in sorted(SPEC_AXIOMS):
        add_node(_node(f"axiom:{axiom}", "axiom", axiom,
                       "spec axiom (docs/architecture/SPEC.md)"))
    add_node(_node(f"module:{GATE_MODULE}", "module", GATE_MODULE))

    # --- registry-derived edges (witness: the registry entry) -----
    for name in sorted(TABLE_REGISTRY):
        contract = TABLE_REGISTRY[name]
        owner = (contract.get("owner") or {}).get("notebook")
        if owner and owner in NOTEBOOK_REGISTRY:
            out.edges_rows.append(
                _edge(f"notebook:{owner}", f"contract:{name}", "produces"))
        gated = NOTEBOOK_REGISTRY.get(owner, {}).get("gates") if owner else None
        if gated:
            out.edges_rows.append(
                _edge(f"contract:{name}", f"module:{GATE_MODULE}",
                      "enforced_by"))
    for adr in sorted(TRACE_REGISTRY):
        entry = TRACE_REGISTRY[adr]
        for path in entry["modules"]:
            out.edges_rows.append(
                _edge(f"module:{path}", f"adr:{adr}", "implements"))
        for path in entry["tests"]:
            out.edges_rows.append(
                _edge(f"adr:{adr}", f"module:{path}", "traced_by"))
        for axiom in entry["axioms"]:
            out.edges_rows.append(
                _edge(f"adr:{adr}", f"axiom:{axiom}", "grounds"))

    # --- event-derived nodes + edges (witness: the event row) ------
    for i, row in enumerate(error_rows or []):
        eid = str(row.get("error_id") or row.get("run_at") or i) + f"#{i}"
        node_id = f"error:{eid}"
        add_node(_node(node_id, "error",
                       str(row.get("reason_code") or row.get("category")
                           or row.get("stage") or "error"),
                       str(row.get("reason_text") or row.get("message")
                           or "")))
        contract_id = str(row.get("contract_id") or "")
        table = contract_id.removeprefix("contract:")
        if table in TABLE_REGISTRY:
            out.edges_rows.append(
                _edge(node_id, f"contract:{table}", "violates"))
    for i, row in enumerate(checklist_rows or []):
        cid = str(row.get("item_id") or row.get("run_at") or i) + f"#{i}"
        node_id = f"checklist:{cid}"
        add_node(_node(node_id, "checklist",
                       str(row.get("stage") or "checklist"),
                       str(row.get("reason_text") or row.get("summary")
                           or "")))
        contract_id = str(row.get("contract_id") or "")
        table = contract_id.removeprefix("contract:")
        if table in TABLE_REGISTRY:
            out.edges_rows.append(
                _edge(node_id, f"contract:{table}", "violates"))

    return out
