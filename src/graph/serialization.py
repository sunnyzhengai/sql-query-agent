"""Serialize/deserialize graph data between Delta table rows and in-memory objects.

Used by notebooks that read graph_nodes/graph_edges from Delta tables
and need to reconstruct in-memory GraphNode/GraphEdge objects, or that
need to serialize them back to Delta-compatible rows.
"""

from __future__ import annotations

import json
from typing import Any

from src.models import EdgeType, GraphEdge, GraphNode, NodeLayer
from src.parser.sql_parser import CTEInfo, ParsedSQL, TableRef


def rows_to_nodes(rows: list[dict]) -> dict[str, GraphNode]:
    """Convert Delta table rows to a dict of node_id -> GraphNode."""
    nodes = {}
    for r in rows:
        props = json.loads(r["properties"]) if r.get("properties") else {}
        nodes[r["node_id"]] = GraphNode(
            node_id=r["node_id"],
            layer=NodeLayer(r["layer"]),
            name=r["name"],
            description=r.get("description") or "",
            properties=props,
        )
    return nodes


def rows_to_edges(rows: list[dict]) -> list[GraphEdge]:
    """Convert Delta table rows to a list of GraphEdge objects."""
    edges = []
    for r in rows:
        props = json.loads(r["properties"]) if r.get("properties") else {}
        edges.append(GraphEdge(
            source_id=r["source_id"],
            target_id=r["target_id"],
            edge_type=EdgeType(r["edge_type"]),
            properties=props,
        ))
    return edges


def nodes_to_rows(nodes: dict[str, GraphNode]) -> list[tuple]:
    """Convert in-memory GraphNode objects to Delta-compatible row tuples.

    Returns list of (node_id, layer, name, description, properties_json).
    """
    return [
        (n.node_id, n.layer.value, n.name, n.description, json.dumps(n.properties))
        for n in nodes.values()
    ]


def edges_to_rows(edges: list[GraphEdge]) -> list[tuple]:
    """Convert in-memory GraphEdge objects to Delta-compatible row tuples.

    Returns list of (source_id, target_id, edge_type, properties_json).
    """
    return [
        (e.source_id, e.target_id, e.edge_type.value, json.dumps(e.properties))
        for e in edges
    ]


def parse_result_to_parsed_sql(pr: dict) -> ParsedSQL:
    """Reconstruct a ParsedSQL from a parse_results Delta table row.

    Deserializes the JSON-encoded CTEs, table refs, and CTE refs
    back into typed objects.
    """
    ctes = []
    for c in json.loads(pr["ctes_json"]):
        table_refs = []
        for t in c["table_refs"]:
            if isinstance(t, dict):
                table_refs.append(TableRef(
                    table=t["table"],
                    schema=t.get("schema", "dbo"),
                    database=t.get("database"),
                ))
            else:
                table_refs.append(TableRef(table=t))
        ctes.append(CTEInfo(
            name=c["name"],
            sql_fragment=c["sql_fragment"],
            table_refs=table_refs,
            depends_on=c["depends_on"],
        ))

    raw_final = json.loads(pr["final_select_tables"])
    final_tables = []
    for t in raw_final:
        if isinstance(t, dict):
            final_tables.append(TableRef(
                table=t["table"],
                schema=t.get("schema", "dbo"),
                database=t.get("database"),
            ))
        else:
            final_tables.append(TableRef(table=t))

    return ParsedSQL(
        ctes=ctes,
        final_select_tables=final_tables,
        final_select_cte_refs=json.loads(pr["final_select_cte_refs"]),
    )
