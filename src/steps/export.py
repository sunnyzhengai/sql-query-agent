"""Step 05: export typed LPG tables for Fabric Graph ingestion.

Logic relations asserted here: node tables partition the nodes by layer;
edge tables partition the edges by type — nothing lost, nothing invented.
Two edge tables are DERIVED closures and sit outside the partition:
graph_edge_uses_table (ADR 0018, metric->table) and graph_edge_c2t
(ADR 0020, metric->every step — the raw roots-only edges stay in
graph_edges; the export is shaped for the NL2GQL generator's habits).
"""

from __future__ import annotations

from src.graph.export import (
    derive_calculated_by_rows,
    derive_uses_table_rows,
    export_edge_tables,
    export_node_tables,
)
from src.graph.serialization import rows_to_edges, rows_to_nodes


def export_step(nodes_rows: "list[dict]", edges_rows: "list[dict]") -> "dict[str, list[dict]]":
    nodes = rows_to_nodes(nodes_rows)
    edges = rows_to_edges(edges_rows)

    tables = {**export_node_tables(nodes), **export_edge_tables(edges)}

    node_total = sum(
        len(rows) for name, rows in tables.items() if not name.startswith("graph_edge_")
    )
    edge_total = sum(
        len(rows) for name, rows in tables.items() if name.startswith("graph_edge_")
    )
    # Decision layer (ADR 0044 1b) is deliberately NOT exported yet —
    # the Fabric Graph read model gains it with the 0046 engine. The
    # conservation assert stays EXACT: declared exclusions are counted,
    # never absorbed into slack.
    from src.models import EdgeType, NodeLayer
    decision_nodes = sum(1 for n in nodes.values()
                         if n.layer == NodeLayer.DECISION)
    decision_edges = sum(1 for e in edges if e.edge_type in (
        EdgeType.STEP_TO_DECISION, EdgeType.DECISION_TO_COLUMN,
        EdgeType.DECISION_TO_STEP))
    assert node_total == len(nodes) - decision_nodes, (
        f"export_step: {len(nodes)} nodes ({decision_nodes} decision-layer "
        f"excluded) -> {node_total} exported node rows"
    )
    assert edge_total == len(edges) - decision_edges, (
        f"export_step: {len(edges)} edges ({decision_edges} decision-layer "
        f"excluded) -> {edge_total} exported edge rows"
    )

    uses_table = derive_uses_table_rows(nodes, edges)
    canonical_ids = {r["nodeId"] for r in tables["graph_canonical"]}
    table_ids = {
        r["nodeId"] for r in tables["graph_technical"] if not r["columnName"]
    }
    assert all(r["sourceId"] in canonical_ids for r in uses_table), (
        "export_step: uses_table sourceId not a canonical node"
    )
    assert all(r["targetId"] in table_ids for r in uses_table), (
        "export_step: uses_table targetId not a technical TABLE node"
    )
    tables["graph_edge_uses_table"] = uses_table

    calculated_by = derive_calculated_by_rows(nodes, edges)
    raw_roots = {(r["sourceId"], r["targetId"]) for r in tables["graph_edge_c2t"]}
    closure_pairs = {(r["sourceId"], r["targetId"]) for r in calculated_by}
    assert raw_roots <= closure_pairs, (
        "export_step: CALCULATED_BY closure must contain every root edge"
    )
    tables["graph_edge_c2t"] = calculated_by
    return tables
