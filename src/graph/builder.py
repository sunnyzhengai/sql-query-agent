"""Build the three-layer graph from parsed SQL and data dictionary.

Flow:
1. Parse SQL sources -> extract CTEs, table/column refs
2. Create technical nodes from data dictionary (tables + columns)
3. Create transformation nodes from CTEs (with sql_fragments)
4. Create canonical nodes from certified metric definitions
5. Wire edges across layers
"""

from __future__ import annotations

import logging

from src.models import EdgeType, GraphEdge, GraphNode, NodeLayer
from src.parser.sql_parser import ParsedSQL, TableRef

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds the three-layer graph incrementally."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        # Lookup: simple table name → set of qualified node IDs
        # Used to match parsed table refs (which may lack schema) to dictionary nodes
        self._table_name_index: dict[str, set[str]] = {}

    def add_technical_node(
        self, table: str, column: str | None = None, description: str = "",
        schema: str = "dbo", database: str | None = None,
    ) -> str:
        """Add a technical-layer node (table or column).

        Node ID uses schema.table format: tech:dbo.PATIENT
        Column nodes: tech:dbo.PATIENT.PAT_ID
        """
        qualified = f"{schema}.{table}"
        node_id = f"tech:{qualified}" if column is None else f"tech:{qualified}.{column}"
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.TECHNICAL,
                name=column or table,
                description=description,
                properties={
                    "table": table,
                    "schema": schema,
                    "database": database,
                    "column": column,
                },
            )
            # Index by simple table name for fuzzy matching
            if column is None:
                self._table_name_index.setdefault(table, set()).add(node_id)
                self._table_name_index.setdefault(table.upper(), set()).add(node_id)
        return node_id

    def _find_tech_node_id(self, table_ref: TableRef) -> str | None:
        """Find a technical node ID matching a TableRef.

        Tries exact match first (schema.table), then falls back to
        simple table name match (for SQL that omits schema).
        """
        # Exact match: tech:schema.table
        exact_id = f"tech:{table_ref.qualified_name}"
        if exact_id in self.nodes:
            return exact_id

        # Case-insensitive exact match
        exact_upper = f"tech:{table_ref.schema}.{table_ref.table.upper()}"
        if exact_upper in self.nodes:
            return exact_upper

        # Fuzzy match: any node with this table name (regardless of schema)
        candidates = self._table_name_index.get(table_ref.table, set())
        if not candidates:
            candidates = self._table_name_index.get(table_ref.table.upper(), set())
        if candidates:
            return next(iter(candidates))  # return first match

        return None

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
        """Wire up transformation and technical nodes from a parsed SQL result.

        Handles both simple (single CTE) and complex (multi-CTE from
        proc_normalize) queries. Wires the full dependency chain so
        traversal reaches all tables.
        """
        cte_names = {cte.name for cte in parsed.ctes}

        # Create transformation nodes for each CTE
        for cte in parsed.ctes:
            transform_id = self.add_transformation_node(metric_id, cte.name, cte.sql_fragment)

            # Wire CTE dependencies (transform -> transform)
            for dep in cte.depends_on:
                dep_id = f"transform:{metric_id}:{dep}"
                if dep_id in self.nodes:
                    self.add_edge(transform_id, dep_id, EdgeType.TRANSFORM_TO_TRANSFORM)

            # Wire to technical nodes for referenced physical tables
            for table_ref in cte.table_refs:
                tech_id = self._find_tech_node_id(table_ref) if isinstance(table_ref, TableRef) else f"tech:{table_ref}"
                if tech_id and tech_id in self.nodes:
                    self.add_edge(transform_id, tech_id, EdgeType.TRANSFORM_TO_TECHNICAL)

        # Find physical tables in the final SELECT that are NOT already
        # referenced by any CTE (those are already reachable via the CTE chain)
        cte_covered_tables = set()
        for cte in parsed.ctes:
            cte_covered_tables.update(cte.table_refs)
        final_only_tables = [t for t in parsed.final_select_tables
                             if (t.table if isinstance(t, TableRef) else t) not in cte_names
                             and t not in cte_covered_tables]

        # Wire these final-only tables via a synthetic transform node
        if final_only_tables:
            final_id = self.add_transformation_node(metric_id, "__final_select__", "")
            for table_ref in final_only_tables:
                tech_id = self._find_tech_node_id(table_ref) if isinstance(table_ref, TableRef) else f"tech:{table_ref}"
                if tech_id and tech_id in self.nodes:
                    self.add_edge(final_id, tech_id, EdgeType.TRANSFORM_TO_TECHNICAL)

        # Wire canonical -> entry point transform nodes
        canonical_id = f"canonical:{metric_id}"
        if canonical_id not in self.nodes:
            return

        if parsed.final_select_cte_refs:
            # Connect canonical to each CTE referenced by the final SELECT
            for cte_name in parsed.final_select_cte_refs:
                transform_id = f"transform:{metric_id}:{cte_name}"
                if transform_id in self.nodes:
                    self.add_edge(canonical_id, transform_id, EdgeType.CANONICAL_TO_TRANSFORM)
        elif parsed.ctes:
            # Fallback: connect to the last CTE (simple case)
            last_transform = f"transform:{metric_id}:{parsed.ctes[-1].name}"
            self.add_edge(canonical_id, last_transform, EdgeType.CANONICAL_TO_TRANSFORM)

        # Connect canonical to the final SELECT's physical tables node
        if final_only_tables:
            final_id = f"transform:{metric_id}:__final_select__"
            self.add_edge(canonical_id, final_id, EdgeType.CANONICAL_TO_TRANSFORM)
