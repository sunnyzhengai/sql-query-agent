"""Graph traversal for query answering.

Given a canonical metric, traverse the graph to collect:
- The transformation pipeline (CTE chain with sql_fragments)
- The technical tables/columns involved
- Available dimension filters
"""

from __future__ import annotations

from src.models import EdgeType, GraphEdge, GraphNode, NodeLayer


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
            dimensions: list of dimension nodes
            sql_fragments: ordered list of SQL fragments for assembly
        """
        canonical_id = f"canonical:{metric_id}"
        if canonical_id not in self.nodes:
            return {}

        visited: set[str] = set()
        transformations: list[GraphNode] = []
        technical: list[GraphNode] = []
        dimensions: list[GraphNode] = []

        self._traverse(canonical_id, visited, transformations, technical, dimensions)

        return {
            "canonical": self.nodes[canonical_id],
            "transformations": transformations,
            "technical": technical,
            "dimensions": dimensions,
            "sql_fragments": [t.properties.get("sql_fragment", "") for t in transformations],
        }

    def _traverse(
        self,
        node_id: str,
        visited: set[str],
        transformations: list[GraphNode],
        technical: list[GraphNode],
        dimensions: list[GraphNode],
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
        elif node.layer == NodeLayer.DIMENSION:
            dimensions.append(node)

        for edge in self._adjacency.get(node_id, []):
            self._traverse(edge.target_id, visited, transformations, technical, dimensions)
