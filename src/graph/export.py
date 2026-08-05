"""Export graph nodes/edges as typed source tables for Fabric Graph.

Fabric Graph requires one table per node type and one per edge type,
with flattened columns (not JSON properties blobs). This module takes
the in-memory GraphBuilder output and produces dict rows suitable for
writing as Delta/parquet tables that the Graph Model editor can map.
"""

from __future__ import annotations

from src.graph.traversal import GraphTraverser
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
            metric_id = node.node_id.replace("canonical:", "")
            canonical.append({
                "nodeId": node.node_id,
                "metricId": metric_id,
                # ADR 0020: name is schema-qualified (== metricId) because the
                # NL2GQL generator habitually filters name with the user's
                # qualified reference; the bare object name lives in bareName.
                "name": metric_id,
                "bareName": node.name,
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
        EdgeType.TABLE_TO_COLUMN: "graph_edge_tab2col",
    }

    result: dict[str, list[dict]] = {name: [] for name in table_map.values()}

    for edge in edges:
        table_name = table_map[edge.edge_type]
        result[table_name].append({
            "sourceId": edge.source_id,
            "targetId": edge.target_id,
        })

    return result


def derive_calculated_by_rows(
    nodes: dict[str, GraphNode], edges: list[GraphEdge]
) -> list[dict]:
    """Materialize metric -> EVERY calculation step (ADR 0020).

    The NL2GQL generator habitually walks CALCULATED_BY as a single hop;
    with root-only edges that silently truncates the calculation. The LPG
    export therefore carries the full closure (roots + every DEPENDS_ON
    descendant); root-only edges remain in the raw graph_edges table.
    """
    traverser = GraphTraverser(nodes, edges)
    rows: list[dict] = []
    for node in nodes.values():
        if node.layer != NodeLayer.CANONICAL:
            continue
        metric_id = node.node_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)
        seen: set[str] = set()
        for step in subgraph.get("transformations", []):
            if step.node_id in seen:
                continue
            seen.add(step.node_id)
            rows.append({"sourceId": node.node_id, "targetId": step.node_id})
    return rows


def derive_uses_table_rows(
    nodes: dict[str, GraphNode], edges: list[GraphEdge]
) -> list[dict]:
    """Materialize the metric -> table transitive closure (ADR 0018).

    One row per (metric, technical TABLE the metric ultimately reads),
    computed over the full DEPENDS_ON closure via GraphTraverser — the
    same walk that defines metric lineage everywhere else. Column nodes
    are excluded (lineage is table-grained; columns hang off tables via
    TABLE_TO_COLUMN structure edges).

    These edges are derived, never stored in graph_edges: they exist so
    table<->metric questions are answerable with a single hop.
    """
    traverser = GraphTraverser(nodes, edges)
    rows: list[dict] = []
    for node in nodes.values():
        if node.layer != NodeLayer.CANONICAL:
            continue
        metric_id = node.node_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)
        seen: set[str] = set()
        for tech in subgraph.get("technical", []):
            if tech.properties.get("column") or tech.node_id in seen:
                continue
            seen.add(tech.node_id)
            rows.append({"sourceId": node.node_id, "targetId": tech.node_id})
    return rows
