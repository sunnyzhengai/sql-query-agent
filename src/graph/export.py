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
            "graph_report": [...],
            "graph_measure": [...],
        }
    """
    canonical = []
    transformation = []
    technical = []
    report = []
    measure = []

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
                "businessName": node.properties.get("business_name", ""),
                "reportName": node.properties.get("report_name", ""),
                "reportUrl": node.properties.get("report_url", ""),
                "description": node.description,
                "steward": node.properties.get("steward", ""),
                "developer": node.properties.get("developer", ""),
            })
        elif node.layer == NodeLayer.TRANSFORMATION:
            transformation.append({
                "nodeId": node.node_id,
                "name": node.name,
                "metricId": node.properties.get("metric_id", ""),
                "description": node.description or "",
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
        elif node.layer == NodeLayer.REPORT:
            report.append({
                "nodeId": node.node_id,
                "name": node.name,
                "description": node.description,
                "repoName": node.properties.get("repo_name", ""),
                "semanticModelPath": node.properties.get("semantic_model_path", ""),
            })
        elif node.layer == NodeLayer.MEASURE:
            measure.append({
                "nodeId": node.node_id,
                "name": node.name,
                "description": node.description,
                "reportName": node.properties.get("report_name", ""),
                "pbiTable": node.properties.get("pbi_table", ""),
                "daxExpression": node.properties.get("dax_expression", ""),
                "expressionType": node.properties.get("expression_type", ""),
            })

    return {
        "graph_canonical": canonical,
        "graph_transformation": transformation,
        "graph_technical": technical,
        "graph_report": report,
        "graph_measure": measure,
    }


def export_edge_tables(edges: list[GraphEdge]) -> dict[str, list[dict]]:
    """Split edges by type into separate tables.

    Returns:
        {
            "graph_edge_c2t": [...],
            "graph_edge_t2t": [...],
            "graph_edge_t2tech": [...],
            "graph_edge_report2canonical": [...],
        }
    """
    table_map = {
        EdgeType.CANONICAL_TO_TRANSFORM: "graph_edge_c2t",
        EdgeType.TRANSFORM_TO_TRANSFORM: "graph_edge_t2t",
        EdgeType.TRANSFORM_TO_TECHNICAL: "graph_edge_t2tech",
        EdgeType.TABLE_TO_COLUMN: "graph_edge_tab2col",
        EdgeType.REPORT_TO_CANONICAL: "graph_edge_report2canonical",
        EdgeType.REPORT_TO_TECHNICAL: "graph_edge_report2technical",
        EdgeType.REPORT_TO_MEASURE: "graph_edge_report2measure",
        EdgeType.MEASURE_TO_COLUMN: "graph_edge_measure2column",
    }

    # Decision-layer edges (ADR 0044 1b) are deliberately NOT exported
    # yet: the Fabric Graph read model gains them when the 0046 engine
    # ships (EXTRACTION_REGISTRY-style explicit exclusion, not a silent
    # drop — an edge type outside BOTH maps still fails loudly).
    deliberately_unexported = {
        EdgeType.STEP_TO_DECISION,
        EdgeType.DECISION_TO_COLUMN,
        EdgeType.DECISION_TO_STEP,
        # ADR 0053: projection edges serve the ask-surface via
        # graph_edges; the Fabric Graph read model gains them with
        # the 0046 engine (same exclusion class as decision edges)
        EdgeType.TRANSFORM_TO_COLUMN,
    }

    result: dict[str, list[dict]] = {name: [] for name in table_map.values()}

    for edge in edges:
        if edge.edge_type in deliberately_unexported:
            continue
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
