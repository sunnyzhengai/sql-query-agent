"""Export graph nodes/edges as typed source tables for Fabric Graph.

Fabric Graph requires one table per node type and one per edge type,
with flattened columns (not JSON properties blobs). This module takes
the in-memory GraphBuilder output and produces dict rows suitable for
writing as Delta/parquet tables that the Graph Model editor can map.
"""

from __future__ import annotations

from src.models import EdgeType, GraphEdge, GraphNode, NodeLayer


def export_node_tables(nodes: dict[str, GraphNode]) -> dict[str, list[dict]]:
    """Split nodes by layer into typed tables with flattened properties.

    Returns:
        {
            "graph_canonical": [...],
            "graph_transformation": [...],
            "graph_technical": [...],
            "graph_dimension": [...],
        }
    """
    canonical = []
    transformation = []
    technical = []
    dimension = []

    for node in nodes.values():
        if node.layer == NodeLayer.CANONICAL:
            canonical.append({
                "nodeId": node.node_id,
                "name": node.name,
                "description": node.description,
                "steward": node.properties.get("steward", ""),
                "developer": node.properties.get("developer", ""),
            })
        elif node.layer == NodeLayer.TRANSFORMATION:
            transformation.append({
                "nodeId": node.node_id,
                "name": node.name,
                "metricId": node.properties.get("metric_id", ""),
                "sqlFragment": node.properties.get("sql_fragment", ""),
            })
        elif node.layer == NodeLayer.TECHNICAL:
            technical.append({
                "nodeId": node.node_id,
                "name": node.name,
                "description": node.description,
                "tableName": node.properties.get("table", ""),
                "schemaName": node.properties.get("schema", ""),
                "databaseName": node.properties.get("database") or "",
                "columnName": node.properties.get("column") or "",
            })
        elif node.layer == NodeLayer.DIMENSION:
            dimension.append({
                "nodeId": node.node_id,
                "name": node.name,
                "description": node.description,
                "tableName": node.properties.get("table", ""),
                "columnName": node.properties.get("column", ""),
            })

    return {
        "graph_canonical": canonical,
        "graph_transformation": transformation,
        "graph_technical": technical,
        "graph_dimension": dimension,
    }


def export_edge_tables(edges: list[GraphEdge]) -> dict[str, list[dict]]:
    """Split edges by type into separate tables.

    Returns:
        {
            "graph_edge_c2t": [...],
            "graph_edge_t2t": [...],
            "graph_edge_t2tech": [...],
            "graph_edge_tech2dim": [...],
        }
    """
    table_map = {
        EdgeType.CANONICAL_TO_TRANSFORM: "graph_edge_c2t",
        EdgeType.TRANSFORM_TO_TRANSFORM: "graph_edge_t2t",
        EdgeType.TRANSFORM_TO_TECHNICAL: "graph_edge_t2tech",
        EdgeType.TECHNICAL_TO_DIMENSION: "graph_edge_tech2dim",
    }

    result: dict[str, list[dict]] = {name: [] for name in table_map.values()}

    for edge in edges:
        table_name = table_map[edge.edge_type]
        result[table_name].append({
            "sourceId": edge.source_id,
            "targetId": edge.target_id,
        })

    return result
