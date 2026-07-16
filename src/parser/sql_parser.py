"""Parse SQL into structured representations for graph building.

Uses sqlglot to parse SQL and extract:
- CTE structure (transformation nodes)
- Table/column references (technical nodes)
- SQL fragments (minimal logic snippets, NOT full SQL blobs)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp


@dataclass
class ColumnRef:
    table: str | None
    column: str


@dataclass
class CTEInfo:
    """A single CTE extracted from a SQL statement."""

    name: str
    sql_fragment: str
    column_refs: list[ColumnRef] = field(default_factory=list)
    table_refs: list[str] = field(default_factory=list)  # actual table names (not aliases, not CTEs)
    depends_on: list[str] = field(default_factory=list)  # other CTE names


@dataclass
class ParsedSQL:
    """Result of parsing a SQL statement."""

    ctes: list[CTEInfo] = field(default_factory=list)
    final_select_tables: list[str] = field(default_factory=list)
    final_select_columns: list[ColumnRef] = field(default_factory=list)


def parse_sql(sql: str, dialect: str = "tsql") -> ParsedSQL:
    """Parse a SQL statement and extract structure.

    Args:
        sql: The SQL statement to parse.
        dialect: SQL dialect (default: tsql for SQL Server / Fabric).

    Returns:
        ParsedSQL with extracted CTEs, tables, and columns.
    """
    try:
        parsed = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Failed to parse SQL: {e}") from e

    result = ParsedSQL()

    # Extract CTEs
    for cte in parsed.find_all(exp.CTE):
        cte_name = cte.alias
        cte_body = cte.this

        # Extract column references from the CTE body
        col_refs = _extract_column_refs(cte_body)

        # Find dependencies on other CTEs and actual table references
        all_table_refs = [t.name for t in cte_body.find_all(exp.Table)]
        cte_names = [c.alias for c in parsed.find_all(exp.CTE)]
        depends_on = [t for t in all_table_refs if t in cte_names]
        physical_tables = [t for t in all_table_refs if t not in cte_names]

        result.ctes.append(
            CTEInfo(
                name=cte_name,
                sql_fragment=cte_body.sql(dialect=dialect),
                column_refs=col_refs,
                table_refs=physical_tables,
                depends_on=depends_on,
            )
        )

    # Extract final SELECT table/column references
    # (the main query after all CTEs)
    main_select = parsed.find(exp.Select)
    if main_select:
        # Get tables from the final select (excluding CTE-defined tables)
        for table in parsed.find_all(exp.Table):
            if table.name not in [c.name for c in result.ctes]:
                if table.name not in result.final_select_tables:
                    result.final_select_tables.append(table.name)

        result.final_select_columns = _extract_column_refs(main_select)

    return result


def _extract_column_refs(node: exp.Expression) -> list[ColumnRef]:
    """Extract column references from an expression node."""
    refs = []
    for col in node.find_all(exp.Column):
        table = col.table if col.table else None
        refs.append(ColumnRef(table=table, column=col.name))
    return refs
