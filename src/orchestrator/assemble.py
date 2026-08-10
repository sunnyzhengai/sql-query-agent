"""Fixed fact assembly — the deterministic core's answer half (ADR 0032).

After the human picks a candidate, facts are fetched with FIXED
parameterized lookups — one per kind, refs as data, never as syntax.
Facts arrive through the SAME Kusto client as resolution (OneLake
shortcuts expose output_metric_logic and graph_nodes in the Eventhouse
database): one data plane, one auth path.

No free query exists here. The LLM sees the result only at the narrate
edge.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from src.orchestrator.core import Candidate

METRIC_FACTS_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "output_metric_logic | where metric_id == p_ref"
)

NODE_FACTS_QUERY = (
    "declare query_parameters(p_node_id:string);\n"
    "graph_nodes | where node_id == p_node_id"
)


@dataclass(frozen=True)
class FactSet:
    kind: str                     # metric | step
    ref: str
    facts: "dict"                 # the assembled, narratable fields
    basis: str                    # stamped by code
    sources: "tuple[str, ...]" = field(default_factory=tuple)


class AssemblyError(Exception):
    """The pick resolved to no facts — surfaced honestly, never papered over."""


def _one_row(rows: "list[dict]", what: str) -> dict:
    if not rows:
        raise AssemblyError(f"no facts found for {what}")
    return rows[0]


def assemble_metric(ref: str, run_kql: "Callable[[str, dict], list[dict]]") -> FactSet:
    row = _one_row(run_kql(METRIC_FACTS_QUERY, {"p_ref": ref}), f"metric {ref}")
    facts = {
        "metric_id": row.get("metric_id"),
        "metric_name": row.get("metric_name"),
        "business_name": row.get("business_name"),
        "description": row.get("description"),
        "steward": row.get("steward"),
        "developer": row.get("developer"),
        "report_name": row.get("report_name"),
        "report_url": row.get("report_url"),
        "transform_count": row.get("transform_count"),
        "source_tables": row.get("source_tables"),
        "calculation_logic": row.get("calculation_logic"),
    }
    return FactSet(
        kind="metric", ref=ref, facts=facts,
        basis=f"output_metric_logic[metric_id={ref!r}] -> 1 row",
        sources=("output_metric_logic",),
    )


def assemble_step(
    node_id: str, ref: str, run_kql: "Callable[[str, dict], list[dict]]"
) -> FactSet:
    """A calculation step plus its parent metric's identity facts.

    candidate.ref for a step IS its parent metric_id (semantic catalog
    contract), so the parent lookup reuses the same fixed metric query.
    """
    node = _one_row(run_kql(NODE_FACTS_QUERY, {"p_node_id": node_id}),
                    f"step {node_id}")
    props = node.get("properties") or "{}"
    if isinstance(props, str):
        props = json.loads(props)
    parent = _one_row(run_kql(METRIC_FACTS_QUERY, {"p_ref": ref}),
                      f"parent metric {ref}")
    facts = {
        "step_name": node.get("name"),
        "step_description": node.get("description"),
        "sql_fragment": props.get("sql_fragment"),
        "parent_metric_id": ref,
        "parent_business_name": parent.get("business_name"),
        "parent_description": parent.get("description"),
        "steward": parent.get("steward"),
        "developer": parent.get("developer"),
        "report_name": parent.get("report_name"),
        "report_url": parent.get("report_url"),
    }
    return FactSet(
        kind="step", ref=ref, facts=facts,
        basis=(f"graph_nodes[node_id={node_id!r}] -> 1 row; "
               f"output_metric_logic[metric_id={ref!r}] -> 1 row"),
        sources=("graph_nodes", "output_metric_logic"),
    )


def assemble(candidate: Candidate,
             run_kql: "Callable[[str, dict], list[dict]]") -> FactSet:
    if candidate.kind == "metric":
        return assemble_metric(candidate.ref, run_kql)
    if candidate.kind == "step":
        return assemble_step(candidate.node_id, candidate.ref, run_kql)
    raise AssemblyError(f"no assembly defined for kind {candidate.kind!r}")
