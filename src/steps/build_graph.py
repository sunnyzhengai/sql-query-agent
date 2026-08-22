"""Step 03: build the three-layer knowledge graph from parse results.

Logic relations asserted here:
- Every parse-result metric has a canonical node.
- Every edge endpoint resolves to an existing node.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.dictionary import DataDictionary
from src.governance.display_names import apply_business_names
from src.governance.steward import StewardManager
from src.graph.builder import GraphBuilder
from src.graph.consumption import wire_consumption_layer
from src.graph.serialization import (
    edges_to_row_dicts,
    nodes_to_row_dicts,
    parse_result_to_parsed_sql,
)
from src.models import EdgeType
from src.parser.identity import fold_identifier
from src.parser.sql_parser import TableRef
from src.tree.extract import (
    build_decision_tree,
    decision_site_rows,
    unextracted_fallout_rows,
)


def _wire_decision_sites(builder, metric_id, step_name, tree, rows,
                         step_by_fold, row_step: "str | None" = None) -> None:
    """Decision nodes + edges (ADR 0044 1b, the reachability law).

    Per extracted site: a decision node, a step→decision edge, and for
    every column its predicates reference: decision→column when the
    alias resolves to a dictionary table (column-grain when the column
    node exists, table-grain otherwise), decision→step when it resolves
    to a temp/CTE step (the path to end nodes continues through the
    step's own reads). Sites with no resolvable reference carry a
    counted exception reason on their graph_decision_sites row —
    connected or counted, never dangling (Sunny, 2026-08-19)."""
    step_node_id = step_by_fold.get(fold_identifier(step_name))
    if step_node_id is None or step_node_id not in builder.nodes:
        return
    leaves_by_site: "dict[str, list]" = {}
    for node in tree.nodes:
        if node.kind == "predicate":
            leaves_by_site.setdefault(node.node_id.split(".")[0], []).append(node)
    for row in rows:
        if row["status"] != "extracted":
            continue
        site_id = row["site_id"]
        decision_id = builder.add_decision_node(
            metric_id, row_step or step_name, site_id, row["context"],
            row["predicate_count"], row["expression_sql"])
        builder.add_edge(step_node_id, decision_id, EdgeType.STEP_TO_DECISION)
        connected = False
        saw_unresolved = False
        saw_columns = False
        saw_params = False
        for leaf in leaves_by_site.get(site_id, []):
            saw_params = saw_params or any(
                o.startswith("@") for o in leaf.operands)
            for ref in leaf.columns:
                saw_columns = True
                if "." not in ref:
                    continue  # unqualified — cannot attribute an owner
                qual, col = ref.rsplit(".", 1)
                resolved = tree.table_aliases.get(
                    qual.split(".")[-1].upper())
                if resolved is None:
                    saw_unresolved = True
                    continue
                schema, table = resolved
                target_fold = fold_identifier(table.lstrip("#"))
                if table.startswith("#") or target_fold in step_by_fold:
                    target_step = step_by_fold.get(target_fold)
                    if target_step and target_step != step_node_id:
                        builder.add_edge(decision_id, target_step,
                                         EdgeType.DECISION_TO_STEP)
                        connected = True
                    elif target_step == step_node_id:
                        connected = True  # self-reference: the step itself
                    else:
                        saw_unresolved = True
                    continue
                table_ref = TableRef(table=table, schema=schema or "dbo")
                table_node = builder._find_tech_node_id(table_ref)
                if table_node is None:
                    saw_unresolved = True
                    continue
                column_node = f"{table_node}.{fold_identifier(col)}"
                target = column_node if column_node in builder.nodes else table_node
                builder.add_edge(decision_id, target,
                                 EdgeType.DECISION_TO_COLUMN)
                connected = True
        if connected:
            row["reachability"] = "connected"
        elif saw_unresolved:
            row["reachability"] = "unresolved_alias"
        elif saw_columns:
            row["reachability"] = "unqualified"
        elif saw_params:
            row["reachability"] = "parameter_only"
        else:
            row["reachability"] = "literal_only"


@dataclass
class BuildGraphOutput:
    nodes_rows: "list[dict]"    # graph_nodes rows
    edges_rows: "list[dict]"    # graph_edges rows
    node_count: int
    edge_count: int
    stewards_applied: int
    business_names_applied: int = 0
    business_names_skipped: "list[str]" = field(default_factory=list)
    # Consumption layer (ADR 0040)
    reports_added: int = 0
    measures_added: int = 0
    consumption_skipped: "list[str]" = field(default_factory=list)
    # Decision tree (ADR 0044 clause 1, phase 1)
    decision_rows: "list[dict]" = field(default_factory=list)
    tree_fallout_rows: "list[dict]" = field(default_factory=list)  # run_at stamped by caller
    decision_sites_extracted: int = 0
    decision_sites_unextracted: int = 0
    # Projection-grain column lineage (ADR 0053): conservation —
    # refs = minted ⊎ dropped(reason), asserted at build time
    projection_refs: int = 0
    projection_minted: int = 0
    projection_dropped: "dict[str, int]" = field(default_factory=dict)


def build_graph_step(
    parse_results_rows: "list[dict]",
    dict_tables_rows: "list[dict]",
    dict_columns_rows: "list[dict]",
    steward_records: "Iterable[dict]" = (),
    metric_name_records: "Iterable[dict]" = (),
    report_source_records: "Iterable[dict]" = (),
    dax_records: "Iterable[dict]" = (),
    *,
    table_name_col: str = "TABLE_NAME",
    column_name_col: str = "COLUMN_NAME",
    description_col: str = "DESCRIPTION",
    table_description_col: str = "DESCRIPTION",
) -> BuildGraphOutput:
    dictionary = DataDictionary()
    for row in dict_tables_rows:
        dictionary.add_table(row[table_name_col], row.get(table_description_col) or "")
    for row in dict_columns_rows:
        dictionary.add_column(
            row[table_name_col], row[column_name_col], row.get(description_col) or ""
        )

    builder = GraphBuilder()
    for table_info in dictionary.tables.values():
        table_name = table_info.table_name  # original casing for display
        builder.add_technical_node(table_name, description=table_info.description)
        for col_info in dictionary.get_columns_for_table(table_name):
            builder.add_technical_node(
                table_name, col_info.column_name, description=col_info.description
            )

    # Decision tree (ADR 0044 clause 1 + 1b): one extraction per step
    # fragment under the conservation law; extracted sites become
    # DECISION NODES wired step→decision and decision→column/step (the
    # reachability law: connected or counted, no dangling decisions).
    decision_rows: "list[dict]" = []
    tree_fallout_rows: "list[dict]" = []
    for pr in parse_results_rows:
        builder.add_canonical_node(pr["metric_id"], pr["name"])
        parsed = parse_result_to_parsed_sql(pr)
        builder.build_from_parsed_sql(pr["metric_id"], parsed)
        step_by_fold = {fold_identifier(c.name): f"transform:{pr['metric_id']}:{c.name}"
                        for c in parsed.ctes}
        # A proc may REDEFINE a CTE name across statements (field find,
        # tenant 300 run 2026-08-20: reports.USP_ED_Sepsis defines
        # PositiveCultures/NegativeCultures twice). Step NODES merge on
        # the name (pre-existing graph behavior); decision ROWS keep
        # BOTH definitions' decisions, keyed uniquely with an occurrence
        # suffix — the unique(metric, step, site) invariant holds and
        # nothing is silently dropped.
        occurrence: "dict[str, int]" = {}
        for cte in parsed.ctes:
            fold = fold_identifier(cte.name)
            occurrence[fold] = occurrence.get(fold, 0) + 1
            row_step = (cte.name if occurrence[fold] == 1
                        else f"{cte.name}#{occurrence[fold]}")
            tree = build_decision_tree(cte.sql_fragment)
            rows = decision_site_rows(tree, pr["metric_id"], step_name=row_step)
            _wire_decision_sites(
                builder, pr["metric_id"], cte.name, tree, rows, step_by_fold,
                row_step=row_step)
            decision_rows.extend(rows)
            tree_fallout_rows.extend(
                unextracted_fallout_rows(tree, pr["metric_id"], step_name=row_step))

    steward_manager = StewardManager()
    steward_manager.load_from_records(list(steward_records))
    stewards_applied = steward_manager.apply_to_graph(builder)

    names_applied, names_skipped = apply_business_names(builder, metric_name_records)

    reports_added, measures_added, consumption_skipped = wire_consumption_layer(
        builder, list(report_source_records), list(dax_records)
    )

    # Logic relations.
    node_ids = set(builder.nodes)
    missing_canonical = [
        pr["metric_id"] for pr in parse_results_rows
        if f"canonical:{pr['metric_id']}" not in node_ids
    ]
    assert not missing_canonical, (
        f"build_graph_step: parse results without canonical nodes: {missing_canonical[:5]}"
    )
    dangling = [
        (e.source_id, e.target_id) for e in builder.edges
        if e.source_id not in node_ids or e.target_id not in node_ids
    ]
    assert not dangling, f"build_graph_step: dangling edges: {dangling[:5]}"

    # ADR 0053 conservation: every projection ref accounted for
    assert builder.projection_refs == (
        builder.projection_minted
        + sum(builder.projection_dropped.values())), (
        f"build_graph_step: projection refs {builder.projection_refs} "
        f"!= minted {builder.projection_minted} + dropped "
        f"{builder.projection_dropped}")

    return BuildGraphOutput(
        nodes_rows=nodes_to_row_dicts(builder.nodes),
        edges_rows=edges_to_row_dicts(builder.edges),
        node_count=len(builder.nodes),
        edge_count=len(builder.edges),
        stewards_applied=stewards_applied,
        business_names_applied=names_applied,
        business_names_skipped=names_skipped,
        reports_added=reports_added,
        measures_added=measures_added,
        consumption_skipped=consumption_skipped,
        decision_rows=decision_rows,
        tree_fallout_rows=tree_fallout_rows,
        decision_sites_extracted=sum(
            r["predicate_count"] for r in decision_rows
            if r["status"] == "extracted"),
        decision_sites_unextracted=len(tree_fallout_rows),
        projection_refs=builder.projection_refs,
        projection_minted=builder.projection_minted,
        projection_dropped=dict(builder.projection_dropped),
    )
