"""Build the three-layer graph from parsed SQL and data dictionary.

Flow:
1. Parse SQL sources -> extract CTEs, table/column refs
2. Create technical nodes from data dictionary (tables + columns)
3. Create transformation nodes from CTEs (with sql_fragments)
4. Create canonical nodes from certified metric definitions
5. Wire edges across layers
"""

from __future__ import annotations

from src.models import EdgeType, GraphEdge, GraphNode, NodeLayer
from src.parser.sql_parser import ParsedSQL


class GraphBuilder:
    """Builds the three-layer graph incrementally."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []

    def add_technical_node(self, table: str, column: str | None = None, description: str = "") -> str:
        """Add a technical-layer node (table or column)."""
        node_id = f"tech:{table}" if column is None else f"tech:{table}.{column}"
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.TECHNICAL,
                name=column or table,
                description=description,
                properties={"table": table, "column": column},
            )
        return node_id

    def add_transformation_node(self, metric_id: str, cte_name: str, sql_fragment: str) -> str:
        """Add a transformation-layer node (CTE step)."""
        node_id = f"transform:{metric_id}:{cte_name}"
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.TRANSFORMATION,
                name=cte_name,
                properties={"metric_id": metric_id, "sql_fragment": sql_fragment},
            )
        return node_id

    def add_canonical_node(
        self,
        metric_id: str,
        name: str,
        description: str = "",
        steward: str | None = None,
        developer: str | None = None,
    ) -> str:
        """Add a canonical-layer node (business metric)."""
        node_id = f"canonical:{metric_id}"
        self.nodes[node_id] = GraphNode(
            node_id=node_id,
            layer=NodeLayer.CANONICAL,
            name=name,
            description=description,
            properties={"steward": steward, "developer": developer},
        )
        return node_id

    def add_dimension_node(self, table: str, column: str, description: str = "") -> str:
        """Add a dimension node (branches from technical table for filtering)."""
        node_id = f"dim:{table}.{column}"
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.DIMENSION,
                name=column,
                description=description,
                properties={"table": table, "column": column},
            )
            # Auto-wire edge from the parent technical table
            tech_table_id = f"tech:{table}"
            if tech_table_id in self.nodes:
                self.add_edge(tech_table_id, node_id, EdgeType.TECHNICAL_TO_DIMENSION)
        return node_id

    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType) -> None:
        """Add a directed edge between two nodes."""
        self.edges.append(GraphEdge(source_id=source_id, target_id=target_id, edge_type=edge_type))

    def build_from_parsed_sql(self, metric_id: str, parsed: ParsedSQL) -> None:
        """Wire up transformation and technical nodes from a parsed SQL result."""
        # Create transformation nodes for each CTE
        prev_transform_id = None
        for cte in parsed.ctes:
            transform_id = self.add_transformation_node(metric_id, cte.name, cte.sql_fragment)

            # Wire CTE dependencies (transform -> transform)
            for dep in cte.depends_on:
                dep_id = f"transform:{metric_id}:{dep}"
                if dep_id in self.nodes:
                    self.add_edge(transform_id, dep_id, EdgeType.TRANSFORM_TO_TRANSFORM)

            # Wire to technical nodes for referenced physical tables
            for table_name in cte.table_refs:
                tech_id = f"tech:{table_name}"
                if tech_id in self.nodes:
                    self.add_edge(transform_id, tech_id, EdgeType.TRANSFORM_TO_TECHNICAL)

            prev_transform_id = transform_id

        # Wire canonical -> last transformation (the pipeline output)
        canonical_id = f"canonical:{metric_id}"
        if canonical_id in self.nodes and parsed.ctes:
            last_transform = f"transform:{metric_id}:{parsed.ctes[-1].name}"
            self.add_edge(canonical_id, last_transform, EdgeType.CANONICAL_TO_TRANSFORM)
