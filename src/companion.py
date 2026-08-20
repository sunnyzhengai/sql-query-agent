"""The admin companion (ADR 0048 item 4) — deterministic core.

Two surfaces, both facts-first:

- explain_step: what a pipeline step needs, produces, and checks — a
  pure registry projection (the facts need no LLM).
- diagnose: a failure explained as a PATH in the admin graph —
  symptom → error —violates→ contract —produced_by→ notebook, plus
  the contract's gate and the decisions behind it. The walk is the
  ADR 0017 pattern (resolve the anchor, traverse pre-shaped
  templates); every hop is a real ops_admin_graph_edges row — never a
  second engine, never a vibe.

E3 discipline: the optional narrate hook (customer's own LLM, BYOT)
only rephrases the assembled facts — it receives the caption, not the
question, and its output is returned BESIDE the deterministic caption
(E6 presentation honesty), never instead of it.
"""

from __future__ import annotations

from src.notebook_registry import NOTEBOOK_REGISTRY
from src.schemas import TABLE_REGISTRY
from src.steps.gates import optional_inputs, required_inputs, tables_owned_by
from src.trace_registry import TRACE_REGISTRY


def explain_step(step_name: str) -> dict:
    """Registry projection: what this step needs, produces, and checks.

    Raises KeyError with the known steps named — an unknown step is an
    admin typo, answered with the list, not a stack trace."""
    if step_name not in NOTEBOOK_REGISTRY:
        raise KeyError(
            f"unknown step {step_name!r} — known steps: "
            f"{', '.join(sorted(NOTEBOOK_REGISTRY))}")
    nb = NOTEBOOK_REGISTRY[step_name]
    requires = [
        {"table": t,
         "producer": (TABLE_REGISTRY[t].get("owner") or {}).get("notebook"),
         "description": TABLE_REGISTRY[t].get("description", "")}
        for t in required_inputs(step_name)
    ]
    optional = [
        {"table": t,
         "remediation": TABLE_REGISTRY[t].get("remediation", "")}
        for t in optional_inputs(step_name)
    ]
    produces = [
        {"table": t, "description": TABLE_REGISTRY[t].get("description", "")}
        for t in tables_owned_by(step_name)
    ]
    return {
        "step": step_name,
        "purpose": nb.get("purpose", ""),
        "family": nb.get("family", ""),
        "requires": requires,
        "optional": optional,
        "produces": produces,
        "gates": list(nb.get("gates", [])),
        "requires_engine": nb.get("requires_engine", ""),
    }


def step_explanation_lines(info: dict) -> "list[str]":
    """The explain_step projection as admin-readable lines."""
    lines = [f"{info['step']} — {info['purpose']}"]
    if info["requires"]:
        lines.append("Needs before it runs:")
        for r in info["requires"]:
            lines.append(f"  - {r['table']} (produced by {r['producer']})")
    for o in info["optional"]:
        lines.append(f"  - optional: {o['table']} — {o['remediation']}")
    if info["produces"]:
        lines.append("Produces:")
        for p in info["produces"]:
            lines.append(f"  - {p['table']}")
    if info["gates"]:
        lines.append(f"Checks: {', '.join(info['gates'])} "
                     f"(wheel ≥ {info['requires_engine']})")
    return lines


def _out_edges(edges_rows, source_id, edge_type):
    return sorted(e["target_id"] for e in edges_rows
                  if e["source_id"] == source_id
                  and e["edge_type"] == edge_type)


def _in_edges(edges_rows, target_id, edge_type):
    return sorted(e["source_id"] for e in edges_rows
                  if e["target_id"] == target_id
                  and e["edge_type"] == edge_type)


def diagnose(
    error_row: dict,
    nodes_rows: "list[dict]",
    edges_rows: "list[dict]",
    narrate=None,
) -> dict:
    """A diagnosis is a path in the admin graph, captioned.

    error_row: any event row carrying contract_id (gate failures,
    fallout, installation errors). nodes/edges: the projected admin
    graph (ops_admin_graph_nodes / ops_admin_graph_edges rows).
    narrate: optional callable(str) -> str — the customer's LLM
    rephrases the caption; the deterministic caption always ships."""
    by_id = {n["node_id"]: n for n in nodes_rows}
    contract_id = str(error_row.get("contract_id") or "")
    table = contract_id.removeprefix("contract:")
    node_id = f"contract:{table}"
    hops: "list[tuple[str, str, str]]" = []
    caption: "list[str]" = [
        "Symptom: "
        + str(error_row.get("reason_text") or error_row.get("message")
              or error_row.get("reason_code") or "reported failure"),
    ]

    if node_id not in by_id:
        what = contract_id or "no contract_id on the event"
        caption.append(
            f"No contract matched ({what}) — novelty escalates (spec:H2): "
            "route to the vendor with the raw event."
        )
        return {"found": False, "hops": hops, "caption_lines": caption,
                "narrative": None}

    caption.append(f"Violated contract: {table} — "
                   f"{by_id[node_id].get('description', '')[:160]}")
    producers = _in_edges(edges_rows, node_id, "produces")
    for p in producers:
        hops.append((node_id, "produced_by", p))
        purpose = by_id.get(p, {}).get("description", "")
        caption.append(f"Producing step: {p.removeprefix('notebook:')} — "
                       f"{purpose}. Fix the state there and rerun it.")
    remediation = TABLE_REGISTRY.get(table, {}).get("remediation")
    if remediation:
        caption.append(f"Remediation on record: {remediation}")
    for gate in _out_edges(edges_rows, node_id, "enforced_by"):
        hops.append((node_id, "enforced_by", gate))
        for adr in _out_edges(edges_rows, gate, "implements"):
            hops.append((gate, "implements", adr))
            title = TRACE_REGISTRY.get(adr.removeprefix("adr:"), {}).get(
                "title", "")
            caption.append(
                f"Why this check exists: ADR {adr.removeprefix('adr:')} — "
                f"{title}")

    narrative = None
    if narrate is not None:
        try:
            narrative = narrate(
                "Rephrase this diagnosis for a system admin, changing no "
                "facts:\n" + "\n".join(caption)).strip() or None
        except Exception:  # noqa: BLE001 — narration is optional polish
            narrative = None
    return {"found": True, "hops": hops, "caption_lines": caption,
            "narrative": narrative}
