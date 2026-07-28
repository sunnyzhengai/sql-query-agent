"""Graph backend protocol for pluggable traversal implementations.

Both the existing Delta/in-memory traversal and the new Fabric Graph
(GQL) traversal implement this protocol so tests and comparison
harnesses can run against either backend identically.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GraphBackend(Protocol):
    """Protocol for graph traversal backends.

    Implementations must return the same dict shape from
    get_metric_subgraph so consumers don't need to know
    which backend is active.
    """

    def get_metric_subgraph(self, metric_id: str) -> dict[str, Any]:
        """Get the full subgraph for a canonical metric.

        Returns a dict with:
            canonical: GraphNode for the metric
            transformations: list[GraphNode] transformation nodes
            technical: list[GraphNode] technical table/column nodes
            dimensions: list[GraphNode] dimension nodes
            sql_fragments: list[str] ordered SQL fragments

        Returns {} if the metric is not found.
        """
        ...

    def list_canonical_metrics(self) -> list[str]:
        """Return all canonical metric_ids."""
        ...
