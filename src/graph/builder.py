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
from src.parser.identity import fold_identifier
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
        # Projection-grain column lineage (ADR 0053): conservation
        # counters — refs = minted ⊎ dropped(reason), asserted by the
        # build step. The ADR 0029 honesty pattern: resolved-only
        # edges, every drop counted by reason, never absorbed.
        self.projection_refs = 0
        self.projection_minted = 0
        self.projection_dropped: dict[str, int] = {}

    def add_technical_node(
        self, table: str, column: str | None = None, description: str = "",
        schema: str = "dbo", database: str | None = None,
    ) -> str:
        """Add a technical-layer node (table or column).

        Node IDs are case-folded (ADR 0016) so dictionary case and SQL case
        always meet at the same node: tech:DBO.PATIENT / tech:DBO.PATIENT.PAT_ID.
        Display casing is preserved in `name` and properties.
        """
        qualified = f"{fold_identifier(schema)}.{fold_identifier(table)}"
        node_id = (
            f"tech:{qualified}"
            if column is None
            else f"tech:{qualified}.{fold_identifier(column)}"
        )
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
            if column is None:
                # Index by folded simple table name for schema-agnostic matching
                self._table_name_index.setdefault(fold_identifier(table), set()).add(node_id)
            else:
                # Column nodes hang off their table so they are reachable by
                # traversal, not just by naming convention.
                table_node_id = self.add_technical_node(
                    table, schema=schema, database=database
                )
                self.add_edge(table_node_id, node_id, EdgeType.TABLE_TO_COLUMN)
        return node_id

    def _find_tech_node_id(self, table_ref: TableRef) -> str | None:
        """Find a technical node ID matching a TableRef.

        Matching is case-insensitive (ADR 0016): exact folded schema.table
        first, then schema-agnostic fallback by folded table name (for SQL
        that omits or differs on schema — the dictionary has no schema).
        """
        exact_id = f"tech:{fold_identifier(table_ref.schema)}.{fold_identifier(table_ref.table)}"
        if exact_id in self.nodes:
            return exact_id

        candidates = self._table_name_index.get(fold_identifier(table_ref.table), set())
        if len(candidates) > 1:
            # Ambiguous bare-name match (same table in multiple schemas).
            # Deterministic pick (sorted) so two runs of identical input give
            # identical graphs — set iteration order made lineage differ
            # between runs (audit 2026-08-15). The 06 schema-ambiguity gate
            # (ADR 0016) blocks deployment unless the admin acknowledged
            # this; refuse-over-guess at build time is tracked as follow-up.
            chosen = sorted(candidates)[0]
            logger.warning(
                "Ambiguous table reference %r matches %d nodes (%s) — using %s",
                table_ref.table, len(candidates), ", ".join(sorted(candidates)), chosen,
            )
            return chosen
        if candidates:
            return next(iter(candidates))

        return None

    def add_transformation_node(
        self, metric_id: str, cte_name: str, sql_fragment: str,
        step_no: "int | None" = None,
    ) -> str:
        """Add a transformation-layer node (CTE step).

        step_no is the CTE's 1-based declaration position — T-SQL
        requires CTEs be declared before use, so declaration order IS
        the logical step order. Persisted so surfaces can say
        "step 3 of ED Sepsis" instead of exposing CTE names.
        """
        node_id = f"transform:{metric_id}:{cte_name}"
        if node_id not in self.nodes:
            properties = {"metric_id": metric_id, "sql_fragment": sql_fragment}
            if step_no is not None:
                properties["step_no"] = step_no
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.TRANSFORMATION,
                name=cte_name,
                properties=properties,
            )
        return node_id

    def add_decision_node(
        self, metric_id: str, step_name: str, site_id: str, context: str,
        predicate_count: int, expression_sql: str,
    ) -> str:
        """Add a decision-layer node (ADR 0044 1b): one per decision site.

        The full faithful subtree lives in graph_decision_sites (the
        record); the node carries light properties (spec:D3 — the node
        is the projection, the table is the truth)."""
        node_id = f"decision:{metric_id}:{step_name}:{site_id}"
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.DECISION,
                name=f"{step_name}/{context}",
                properties={
                    "metric_id": metric_id, "step_name": step_name,
                    "site_id": site_id, "context": context,
                    "predicate_count": predicate_count,
                    "expression_sql": expression_sql[:500],
                },
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

    def add_report_node(
        self, report_name: str, description: str = "",
        repo_name: str = "", semantic_model_path: str = "",
    ) -> str:
        """Add a consumption-layer report node (ADR 0040).

        Identity is the report name from the .SemanticModel folder —
        stable across git and workspace views of the same model.
        """
        node_id = f"report:{fold_identifier(report_name)}"
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.REPORT,
                name=report_name,
                description=description,
                properties={
                    "repo_name": repo_name,
                    "semantic_model_path": semantic_model_path,
                },
            )
        return node_id

    def add_measure_node(
        self, report_name: str, table_name: str, measure_name: str,
        expression: str, expression_type: str = "measure",
    ) -> str:
        """Add a DAX measure / calculated-column node (ADR 0040).

        The expression is stored like a transformation's sql_fragment —
        it IS business logic, so 07's description walk and the PHI gate
        treat it the same way.
        """
        node_id = (
            f"measure:{fold_identifier(report_name)}:"
            f"{fold_identifier(table_name)}[{measure_name}]"
        )
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(
                node_id=node_id,
                layer=NodeLayer.MEASURE,
                name=measure_name,
                properties={
                    "report_name": report_name,
                    "pbi_table": table_name,
                    "dax_expression": expression,
                    "expression_type": expression_type,
                },
            )
            report_id = self.add_report_node(report_name)
            self.add_edge(report_id, node_id, EdgeType.REPORT_TO_MEASURE)
        return node_id

    def _drop_projection(self, reason: str) -> None:
        self.projection_dropped[reason] = (
            self.projection_dropped.get(reason, 0) + 1)

    def mint_projection_edges(
        self, transform_id: str,
        column_refs: "list", table_refs: "list",
    ) -> None:
        """Projection-grain column lineage (ADR 0053, §3b-designed):
        mint transform→column edges for the fragment's column refs,
        resolved against the DICTIONARY — an edge exists only when the
        ref resolves to exactly one known column node.

        Inventory of minting contexts (v1): the parser's per-step
        column_refs (SELECT list + expressions of the fragment).
        Conservation: every ref lands in minted or a counted drop
        reason — unresolved_qualifier (alias/unknown table),
        no_dictionary_column, ambiguous (unqualified, >1 candidate),
        duplicate (already minted for this step)."""
        seen: "set[tuple]" = set()
        tables = [t for t in table_refs if isinstance(t, TableRef)]
        for ref in column_refs:
            self.projection_refs += 1
            col = getattr(ref, "column", None)
            if not col:
                self._drop_projection("no_column_name")
                continue
            qual = (str(ref.table).split(".")[-1].upper()
                    if getattr(ref, "table", None) else None)
            cands = ([t for t in tables if t.table.upper() == qual]
                     if qual else tables)
            if qual and not cands:
                self._drop_projection("unresolved_qualifier")
                continue
            hits: "set[str]" = set()
            for t in cands:
                tn = self._find_tech_node_id(t)
                if tn is None:
                    continue
                cn = f"{tn}.{fold_identifier(col)}"
                if cn in self.nodes:
                    hits.add(cn)
            if len(hits) == 1:
                target = next(iter(hits))
                if (transform_id, target) in seen:
                    self._drop_projection("duplicate")
                    continue
                seen.add((transform_id, target))
                self.add_edge(transform_id, target,
                              EdgeType.TRANSFORM_TO_COLUMN)
                self.projection_minted += 1
            elif not hits:
                self._drop_projection("no_dictionary_column")
            else:
                self._drop_projection("ambiguous")

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
        for step_no, cte in enumerate(parsed.ctes, start=1):
            transform_id = self.add_transformation_node(
                metric_id, cte.name, cte.sql_fragment, step_no=step_no)

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

            # Projection-grain column lineage (ADR 0053)
            self.mint_projection_edges(transform_id, cte.column_refs,
                                       cte.table_refs)

        # Find physical tables in the final SELECT that are NOT already
        # referenced by any CTE (those are already reachable via the CTE chain)
        cte_covered_tables = set()
        for cte in parsed.ctes:
            cte_covered_tables.update(cte.table_refs)
        final_only_tables = [t for t in parsed.final_select_tables
                             if (t.table if isinstance(t, TableRef) else t) not in cte_names
                             and t not in cte_covered_tables]

        # Wire these final-only tables via a synthetic transform node
        # For procs with no CTEs, use the normalized_sql as the fragment
        # so the agent can still explain what the SELECT does
        final_fragment = parsed.normalized_sql if not parsed.ctes else ""
        if final_only_tables:
            final_id = self.add_transformation_node(metric_id, "__final_select__", final_fragment)
            for table_ref in final_only_tables:
                tech_id = self._find_tech_node_id(table_ref) if isinstance(table_ref, TableRef) else f"tech:{table_ref}"
                if tech_id and tech_id in self.nodes:
                    self.add_edge(final_id, tech_id, EdgeType.TRANSFORM_TO_TECHNICAL)
            # Projection-grain column lineage for the final SELECT
            # (ADR 0053) — resolved against the final tables only
            self.mint_projection_edges(final_id,
                                       parsed.final_select_columns,
                                       parsed.final_select_tables)

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
