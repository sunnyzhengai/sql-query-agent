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
from src.tree.extract import (
    build_decision_tree,
    decision_site_rows,
    unextracted_fallout_rows,
)


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

    # Decision tree (ADR 0044 clause 1): one extraction per step fragment,
    # under the conservation law — unextractable sites become counted rows
    # and escalated fallout, never silence.
    decision_rows: "list[dict]" = []
    tree_fallout_rows: "list[dict]" = []
    for pr in parse_results_rows:
        builder.add_canonical_node(pr["metric_id"], pr["name"])
        parsed = parse_result_to_parsed_sql(pr)
        builder.build_from_parsed_sql(pr["metric_id"], parsed)
        for cte in parsed.ctes:
            tree = build_decision_tree(cte.sql_fragment)
            decision_rows.extend(
                decision_site_rows(tree, pr["metric_id"], step_name=cte.name))
            tree_fallout_rows.extend(
                unextracted_fallout_rows(tree, pr["metric_id"], step_name=cte.name))

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
    )
