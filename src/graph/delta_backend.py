"""Delta/in-memory graph backend.

Thin wrapper around the existing GraphTraverser, exposing it through
the GraphBackend protocol. Zero changes to existing traversal logic.
"""

from __future__ import annotations

from src.graph.traversal import GraphTraverser
from src.models import GraphEdge, GraphNode, NodeLayer


class DeltaBackend:
    """GraphBackend implementation using in-memory DFS over Delta-loaded nodes/edges."""

    def __init__(self, nodes: dict[str, GraphNode], edges: list[GraphEdge]) -> None:
        self._traverser = GraphTraverser(nodes, edges)
        self._nodes = nodes

    def get_metric_subgraph(self, metric_id: str) -> dict:
        return self._traverser.get_metric_subgraph(metric_id)

    def list_canonical_metrics(self) -> list[str]:
        return [
            nid.removeprefix("canonical:")
            for nid, n in self._nodes.items()
            if n.layer == NodeLayer.CANONICAL
        ]
