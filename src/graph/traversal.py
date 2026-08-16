"""Graph traversal for query answering.

Given a canonical metric, traverse the graph to collect:
- The transformation pipeline (CTE chain with sql_fragments)
- The technical tables/columns involved
"""

from __future__ import annotations

import logging

from src.models import EdgeType, GraphEdge, GraphNode, NodeLayer

logger = logging.getLogger(__name__)


class GraphTraverser:
    """Traverse the graph to answer questions about metrics."""

    def __init__(self, nodes: dict[str, GraphNode], edges: list[GraphEdge]) -> None:
        self.nodes = nodes
        self.edges = edges
        self._adjacency: dict[str, list[GraphEdge]] = {}
        self._build_adjacency()

    def _build_adjacency(self) -> None:
        for edge in self.edges:
            self._adjacency.setdefault(edge.source_id, []).append(edge)

    def get_metric_subgraph(self, metric_id: str) -> dict:
        """Get the full subgraph for a canonical metric.

        Returns a dict with:
            canonical: the canonical node
            transformations: ordered list of transformation nodes
            technical: list of technical nodes
            sql_fragments: ordered list of SQL fragments for assembly
        """
        canonical_id = f"canonical:{metric_id}"
        if canonical_id not in self.nodes:
            return {}

        visited: set[str] = set()
        transformations: list[GraphNode] = []
        technical: list[GraphNode] = []

        self._traverse(canonical_id, visited, transformations, technical)

        return {
            "canonical": self.nodes[canonical_id],
            "transformations": transformations,
            "technical": technical,
            "sql_fragments": [t.properties.get("sql_fragment", "") for t in transformations],
        }

    def _traverse(
        self,
        node_id: str,
        visited: set[str],
        transformations: list[GraphNode],
        technical: list[GraphNode],
    ) -> None:
        if node_id in visited:
            return
        visited.add(node_id)

        node = self.nodes.get(node_id)
        if not node:
            return

        if node.layer == NodeLayer.TRANSFORMATION:
            transformations.append(node)
        elif node.layer == NodeLayer.TECHNICAL:
            technical.append(node)

        for edge in self._adjacency.get(node_id, []):
            # Metric subgraphs describe lineage (which TABLES feed the
            # metric). Table->column structure edges are for graph
            # exploration, not lineage — following them would pollute
            # source_tables with every column of every table.
            if edge.edge_type == EdgeType.TABLE_TO_COLUMN:
                continue
            self._traverse(edge.target_id, visited, transformations, technical)
