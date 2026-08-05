"""Step 05: export typed LPG tables for Fabric Graph ingestion.

Logic relations asserted here: node tables partition the nodes by layer;
edge tables partition the edges by type — nothing lost, nothing invented.
graph_edge_uses_table is DERIVED (ADR 0018: precomputed metric->table
closure), so it sits outside the partition and asserts its own shape.
"""

from __future__ import annotations

from src.graph.export import (
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
    assert node_total == len(nodes), (
        f"export_step: {len(nodes)} nodes -> {node_total} exported node rows"
    )
    assert edge_total == len(edges), (
        f"export_step: {len(edges)} edges -> {edge_total} exported edge rows"
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
    return tables
