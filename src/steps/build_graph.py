"""Step 03: build the three-layer knowledge graph from parse results.

Logic relations asserted here:
- Every parse-result metric has a canonical node.
- Every edge endpoint resolves to an existing node.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.dictionary import DataDictionary
from src.governance.steward import StewardManager
from src.graph.builder import GraphBuilder
from src.graph.serialization import (
    edges_to_row_dicts,
    nodes_to_row_dicts,
    parse_result_to_parsed_sql,
)


@dataclass
class BuildGraphOutput:
    nodes_rows: "list[dict]"    # graph_nodes rows
    edges_rows: "list[dict]"    # graph_edges rows
    node_count: int
    edge_count: int
    stewards_applied: int


def build_graph_step(
    parse_results_rows: "list[dict]",
    dict_tables_rows: "list[dict]",
    dict_columns_rows: "list[dict]",
    steward_records: "Iterable[dict]" = (),
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

    for pr in parse_results_rows:
        builder.add_canonical_node(pr["metric_id"], pr["name"])
        builder.build_from_parsed_sql(pr["metric_id"], parse_result_to_parsed_sql(pr))

    steward_manager = StewardManager()
    steward_manager.load_from_records(list(steward_records))
    stewards_applied = steward_manager.apply_to_graph(builder)

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
    )
