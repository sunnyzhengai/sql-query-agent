"""Fabric Graph backend — traversal via GQL queries.

Implements GraphBackend protocol by sending GQL queries to the Fabric
Graph API instead of doing in-memory DFS. Returns the same dict shape
as DeltaBackend so consumers are backend-agnostic.

GQL Strategy:
    get_metric_subgraph uses 3 queries:
    1. Canonical + all reachable Transformation nodes (variable-length path)
    2. Technical nodes from discovered transforms
    3. Dimension nodes from discovered technical nodes
"""

from __future__ import annotations

import logging
from typing import Any

from src.graph.gql_client import GQLClient, GQLResult
from src.models import GraphNode, NodeLayer

logger = logging.getLogger(__name__)


class FabricGraphBackend:
    """GraphBackend implementation using Fabric Graph GQL API."""

    def __init__(self, client: GQLClient) -> None:
        self._client = client

    def get_metric_subgraph(self, metric_id: str) -> dict[str, Any]:
        """Query the Fabric Graph for a metric's full subgraph.

        Returns the same dict shape as GraphTraverser.get_metric_subgraph():
        {canonical, transformations, technical, dimensions, sql_fragments}
        or {} if the metric is not found.
        """
        canonical_id = f"canonical:{metric_id}"

        # Step 1: Get canonical node + all reachable transforms
        canonical, transformations = self._query_canonical_and_transforms(canonical_id)
        if canonical is None:
            return {}

        # Step 2: Get technical nodes from all transforms
        transform_ids = [t.node_id for t in transformations]
        technical = self._query_technical_nodes(transform_ids) if transform_ids else []

        # Step 3: Get dimension nodes from technical nodes
        tech_ids = [t.node_id for t in technical]
        dimensions = self._query_dimension_nodes(tech_ids) if tech_ids else []

        return {
            "canonical": canonical,
            "transformations": transformations,
            "technical": technical,
            "dimensions": dimensions,
            "sql_fragments": [
                t.properties.get("sql_fragment", "") for t in transformations
            ],
        }

    def list_canonical_metrics(self) -> list[str]:
        """Query all canonical metric IDs from the graph."""
        result = self._client.execute(
            "MATCH (c:Canonical) RETURN c.node_id AS node_id"
        )
        return [
            row["node_id"].removeprefix("canonical:")
            for row in result.data
            if row.get("node_id")
        ]

    def _query_canonical_and_transforms(
        self, canonical_id: str,
    ) -> tuple[GraphNode | None, list[GraphNode]]:
        """Get the canonical node and all reachable transformation nodes.

        Uses a variable-length path pattern to follow the full
        transform chain (CANONICAL_TO_TRANSFORM + TRANSFORM_TO_TRANSFORM).
        Falls back to explicit two-level query if needed.
        """
        # Try variable-length path first
        gql = (
            f"MATCH (c:Canonical {{node_id: '{canonical_id}'}})"
            f"-[:CANONICAL_TO_TRANSFORM]->(t1:Transformation) "
            f"OPTIONAL MATCH (t1)-[:TRANSFORM_TO_TRANSFORM*0..6]->(t_deep:Transformation) "
            f"RETURN c.node_id AS c_id, c.name AS c_name, c.description AS c_desc, "
            f"c.steward AS c_steward, c.developer AS c_developer, "
            f"t1.node_id AS t1_id, t1.name AS t1_name, "
            f"t1.metric_id AS t1_metric_id, t1.sql_fragment AS t1_fragment, "
            f"t_deep.node_id AS td_id, t_deep.name AS td_name, "
            f"t_deep.metric_id AS td_metric_id, t_deep.sql_fragment AS td_fragment"
        )

        try:
            result = self._client.execute(gql)
        except RuntimeError:
            logger.warning("Variable-length path query failed, trying explicit fallback")
            return self._query_canonical_and_transforms_fallback(canonical_id)

        if not result.data:
            return None, []

        # Parse canonical node from first row
        first = result.data[0]
        canonical = GraphNode(
            node_id=first["c_id"],
            layer=NodeLayer.CANONICAL,
            name=first.get("c_name", ""),
            description=first.get("c_desc", ""),
            properties={
                "steward": first.get("c_steward"),
                "developer": first.get("c_developer"),
            },
        )

        # Collect unique transform nodes from all rows
        transforms: dict[str, GraphNode] = {}
        for row in result.data:
            for prefix in ("t1", "td"):
                nid = row.get(f"{prefix}_id")
                if nid and nid not in transforms:
                    transforms[nid] = GraphNode(
                        node_id=nid,
                        layer=NodeLayer.TRANSFORMATION,
                        name=row.get(f"{prefix}_name", ""),
                        properties={
                            "metric_id": row.get(f"{prefix}_metric_id", ""),
                            "sql_fragment": row.get(f"{prefix}_fragment", ""),
                        },
                    )

        return canonical, list(transforms.values())

    def _query_canonical_and_transforms_fallback(
        self, canonical_id: str,
    ) -> tuple[GraphNode | None, list[GraphNode]]:
        """Explicit two-level fallback if variable-length paths aren't supported."""
        gql = (
            f"MATCH (c:Canonical {{node_id: '{canonical_id}'}})"
            f"-[:CANONICAL_TO_TRANSFORM]->(t1:Transformation) "
            f"OPTIONAL MATCH (t1)-[:TRANSFORM_TO_TRANSFORM]->(t2:Transformation) "
            f"RETURN c.node_id AS c_id, c.name AS c_name, c.description AS c_desc, "
            f"c.steward AS c_steward, c.developer AS c_developer, "
            f"t1.node_id AS t1_id, t1.name AS t1_name, "
            f"t1.metric_id AS t1_metric_id, t1.sql_fragment AS t1_fragment, "
            f"t2.node_id AS t2_id, t2.name AS t2_name, "
            f"t2.metric_id AS t2_metric_id, t2.sql_fragment AS t2_fragment"
        )

        result = self._client.execute(gql)
        if not result.data:
            return None, []

        first = result.data[0]
        canonical = GraphNode(
            node_id=first["c_id"],
            layer=NodeLayer.CANONICAL,
            name=first.get("c_name", ""),
            description=first.get("c_desc", ""),
            properties={
                "steward": first.get("c_steward"),
                "developer": first.get("c_developer"),
            },
        )

        transforms: dict[str, GraphNode] = {}
        for row in result.data:
            for prefix in ("t1", "t2"):
                nid = row.get(f"{prefix}_id")
                if nid and nid not in transforms:
                    transforms[nid] = GraphNode(
                        node_id=nid,
                        layer=NodeLayer.TRANSFORMATION,
                        name=row.get(f"{prefix}_name", ""),
                        properties={
                            "metric_id": row.get(f"{prefix}_metric_id", ""),
                            "sql_fragment": row.get(f"{prefix}_fragment", ""),
                        },
                    )

        return canonical, list(transforms.values())

    def _query_technical_nodes(self, transform_ids: list[str]) -> list[GraphNode]:
        """Get all technical nodes reachable from the given transform nodes."""
        id_list = ", ".join(f"'{tid}'" for tid in transform_ids)
        gql = (
            f"MATCH (t:Transformation)-[:TRANSFORM_TO_TECHNICAL]->(tech:Technical) "
            f"WHERE t.node_id IN [{id_list}] "
            f"RETURN DISTINCT tech.node_id AS node_id, tech.name AS name, "
            f"tech.description AS description, tech.table_name AS table_name, "
            f"tech.schema_name AS schema_name, tech.database_name AS database_name, "
            f"tech.column_name AS column_name"
        )

        result = self._client.execute(gql)
        nodes: dict[str, GraphNode] = {}
        for row in result.data:
            nid = row.get("node_id")
            if nid and nid not in nodes:
                nodes[nid] = GraphNode(
                    node_id=nid,
                    layer=NodeLayer.TECHNICAL,
                    name=row.get("name", ""),
                    description=row.get("description", ""),
                    properties={
                        "table": row.get("table_name", ""),
                        "schema": row.get("schema_name", ""),
                        "database": row.get("database_name") or None,
                        "column": row.get("column_name") or None,
                    },
                )

        return list(nodes.values())

    def _query_dimension_nodes(self, tech_ids: list[str]) -> list[GraphNode]:
        """Get all dimension nodes reachable from the given technical nodes."""
        id_list = ", ".join(f"'{tid}'" for tid in tech_ids)
        gql = (
            f"MATCH (tech:Technical)-[:TECHNICAL_TO_DIMENSION]->(d:Dimension) "
            f"WHERE tech.node_id IN [{id_list}] "
            f"RETURN DISTINCT d.node_id AS node_id, d.name AS name, "
            f"d.description AS description, d.table_name AS table_name, "
            f"d.column_name AS column_name"
        )

        result = self._client.execute(gql)
        nodes: dict[str, GraphNode] = {}
        for row in result.data:
            nid = row.get("node_id")
            if nid and nid not in nodes:
                nodes[nid] = GraphNode(
                    node_id=nid,
                    layer=NodeLayer.DIMENSION,
                    name=row.get("name", ""),
                    description=row.get("description", ""),
                    properties={
                        "table": row.get("table_name", ""),
                        "column": row.get("column_name", ""),
                    },
                )

        return list(nodes.values())
