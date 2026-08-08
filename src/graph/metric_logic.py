"""Build the metric_logic flat table from the knowledge graph.

Traverses the graph for each canonical metric and flattens:
- Calculation logic (SQL fragments from transformation chain)
- Source tables (physical tables with descriptions)
- Steward and developer assignments

This produces the single-table view that the Data Agent queries.
"""

from __future__ import annotations

from src.graph.traversal import GraphTraverser
from src.models import GraphNode, NodeLayer
from src.parser.sql_parser import normalize_sql_whitespace


def build_metric_logic_rows(
    nodes: dict[str, GraphNode],
    edges: list,
) -> list[tuple]:
    """Build metric_logic row tuples from the in-memory graph.

    Returns list of tuples matching the METRIC_LOGIC schema:
    (metric_id, metric_name, business_name, report_name, report_url,
     description, steward, developer, transform_count, calculation_logic,
     source_tables, table_descriptions)
    """
    traverser = GraphTraverser(nodes, edges)

    canonical_nodes = [n for n in nodes.values() if n.layer == NodeLayer.CANONICAL]
    rows = []

    for canonical in canonical_nodes:
        metric_id = canonical.node_id.removeprefix("canonical:")
        subgraph = traverser.get_metric_subgraph(metric_id)
        if not subgraph:
            continue

        steward = canonical.properties.get("steward")
        developer = canonical.properties.get("developer")

        transforms = subgraph.get("transformations", [])
        sql_fragments = []
        for t in transforms:
            frag = t.properties.get("sql_fragment", "")
            if frag:
                frag = normalize_sql_whitespace(frag)
                sql_fragments.append(f"-- {t.name}\n{frag}")

        combined_logic = "\n\n".join(sql_fragments) if sql_fragments else None

        tech_nodes = subgraph.get("technical", [])
        tables = sorted(set(
            t.name for t in tech_nodes if t.properties.get("column") is None
        ))
        tables_str = ", ".join(tables) if tables else None

        table_descs = []
        for t in tech_nodes:
            if t.properties.get("column") is None and t.description:
                table_descs.append(f"{t.name}: {t.description}")
        table_descs_str = "; ".join(table_descs) if table_descs else None

        rows.append((
            metric_id, canonical.name,
            canonical.properties.get("business_name"),
            canonical.properties.get("report_name"),
            canonical.properties.get("report_url"),
            canonical.description,
            steward, developer,
            len(transforms), combined_logic,
            tables_str, table_descs_str,
        ))

    return rows
