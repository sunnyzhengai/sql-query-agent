"""Step 05: export typed LPG tables for Fabric Graph ingestion.

Logic relations asserted here: node tables partition the nodes by layer;
edge tables partition the edges by type — nothing lost, nothing invented.
"""

from __future__ import annotations

from src.graph.export import export_edge_tables, export_node_tables
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
    return tables
