"""End-to-end graph build pipeline.

Takes list-of-dicts (works from JSON seed data or Spark .collect())
and returns a fully wired GraphBuilder.
"""

from __future__ import annotations

import logging
from typing import Any

from src.dictionary import DataDictionary
from src.graph.builder import GraphBuilder
from src.parser.sql_parser import parse_sql

logger = logging.getLogger(__name__)


def build_graph(
    dict_tables: list[dict[str, Any]],
    dict_columns: list[dict[str, Any]],
    sql_sources: list[dict[str, Any]],
    table_name_col: str = "TABLE_NAME",
    column_name_col: str = "COLUMN_NAME",
    description_col: str = "DESCRIPTION",
) -> GraphBuilder:
    """Build the three-layer graph from raw data.

    Args:
        dict_tables: List of dicts with at least table_name_col and description_col.
        dict_columns: List of dicts with at least table_name_col, column_name_col, description_col.
        sql_sources: List of dicts with keys: metric_id, name, sql, and optionally steward, developer.
        table_name_col: Column name for table name in dictionary data.
        column_name_col: Column name for column name in dictionary data.
        description_col: Column name for description in dictionary data.

    Returns:
        A GraphBuilder with all nodes and edges populated.
    """
    builder = GraphBuilder()

    # Step 1: Load data dictionary
    dictionary = DataDictionary()
    for row in dict_tables:
        dictionary.add_table(row[table_name_col], row.get(description_col, ""))
    for row in dict_columns:
        dictionary.add_column(row[table_name_col], row[column_name_col], row.get(description_col, ""))
    logger.info("Loaded data dictionary: %d tables, %d column entries", len(dictionary.tables), len(dict_columns))

    # Step 2: Create technical nodes from dictionary
    for table_name, table_info in dictionary.tables.items():
        builder.add_technical_node(table_name, description=table_info.description)
        for col_info in dictionary.get_columns_for_table(table_name):
            builder.add_technical_node(table_name, col_info.column_name, description=col_info.description)
    logger.info("Created technical nodes from dictionary")

    # Step 3: Process each SQL source
    for source in sql_sources:
        metric_id = source["metric_id"]
        name = source["name"]
        sql = source["sql"]
        steward = source.get("steward")
        developer = source.get("developer")

        # Create canonical node
        builder.add_canonical_node(metric_id, name, steward=steward, developer=developer)

        # Parse SQL and wire transformation + technical edges
        parsed = parse_sql(sql)
        builder.build_from_parsed_sql(metric_id, parsed)
        logger.info("Processed metric: %s (%s) — %d CTEs", metric_id, name, len(parsed.ctes))

    logger.info("Graph build complete: %d nodes, %d edges", len(builder.nodes), len(builder.edges))
    return builder
