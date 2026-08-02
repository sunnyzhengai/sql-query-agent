"""Step 04: flatten the graph into the agent's metric_logic table.

Logic relation asserted here: exactly one output row per canonical node.
"""

from __future__ import annotations

from src.graph.metric_logic import build_metric_logic_rows
from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.models import NodeLayer
from src.schemas import METRIC_LOGIC

_COLUMNS = [c[0] for c in METRIC_LOGIC["columns"]]


def metric_logic_step(nodes_rows: "list[dict]", edges_rows: "list[dict]") -> "list[dict]":
    nodes = rows_to_nodes(nodes_rows)
    edges = rows_to_edges(edges_rows)

    tuples = build_metric_logic_rows(nodes, edges)
    rows = [dict(zip(_COLUMNS, t)) for t in tuples]

    canonical_count = sum(1 for n in nodes.values() if n.layer == NodeLayer.CANONICAL)
    assert len(rows) == canonical_count, (
        f"metric_logic_step: {canonical_count} canonical nodes -> {len(rows)} rows"
    )
    assert len({r["metric_id"] for r in rows}) == len(rows), (
        "metric_logic_step: duplicate metric_ids in output"
    )
    return rows
