"""Discover views and stored procedures from SQL Server system catalogs.

Queries sys.sql_modules + sys.objects + sys.schemas to find SQL definitions,
and sys.sql_expression_dependencies to filter by referenced base tables.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.config import DomainFilterConfig
from src.extractor.connection import SqlConnection

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredObject:
    schema_name: str
    object_name: str
    object_type: str
    sql_definition: str


# Map config object_types to SQL Server type_desc values
_TYPE_MAP = {
    "VIEW": "VIEW",
    "SQL_STORED_PROCEDURE": "SQL_STORED_PROCEDURE",
    "SQL_INLINE_TABLE_VALUED_FUNCTION": "SQL_INLINE_TABLE_VALUED_FUNCTION",
    "SQL_SCALAR_FUNCTION": "SQL_SCALAR_FUNCTION",
}


def _quote_list(values: list[str]) -> str:
    """Safely quote a list of strings for SQL IN clause."""
    return ", ".join(f"'{v}'" for v in values)


def build_discovery_query(domain: DomainFilterConfig) -> str:
    """Build the SQL query to discover objects matching the domain filter."""
    type_descs = [_TYPE_MAP.get(t, t) for t in domain.object_types]
    type_filter = f"o.type_desc IN ({_quote_list(type_descs)})"

    if domain.base_tables and domain.schemas:
        # Combined: objects in these schemas that reference these tables
        return f"""
SELECT DISTINCT
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    m.definition AS sql_definition
FROM sys.sql_expression_dependencies d
JOIN sys.objects o ON d.referencing_id = o.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
JOIN sys.sql_modules m ON m.object_id = o.object_id
WHERE d.referenced_entity_name IN ({_quote_list(domain.base_tables)})
  AND s.name IN ({_quote_list(domain.schemas)})
  AND {type_filter}
ORDER BY s.name, o.name
""".strip()

    if domain.base_tables:
        # Table-only filter
        return f"""
SELECT DISTINCT
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    m.definition AS sql_definition
FROM sys.sql_expression_dependencies d
JOIN sys.objects o ON d.referencing_id = o.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
JOIN sys.sql_modules m ON m.object_id = o.object_id
WHERE d.referenced_entity_name IN ({_quote_list(domain.base_tables)})
  AND {type_filter}
ORDER BY s.name, o.name
""".strip()

    if domain.schemas:
        # Schema-only filter
        return f"""
SELECT
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    m.definition AS sql_definition
FROM sys.sql_modules m
JOIN sys.objects o ON m.object_id = o.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE s.name IN ({_quote_list(domain.schemas)})
  AND {type_filter}
ORDER BY s.name, o.name
""".strip()

    # No filters — get everything of the specified types
    return f"""
SELECT
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    m.definition AS sql_definition
FROM sys.sql_modules m
JOIN sys.objects o ON m.object_id = o.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE {type_filter}
ORDER BY s.name, o.name
""".strip()


def discover_objects(conn: SqlConnection, domain: DomainFilterConfig) -> list[DiscoveredObject]:
    """Query SQL Server sys catalogs and return matching views/procs."""
    query = build_discovery_query(domain)
    rows = conn.execute_query(query)

    results = []
    for row in rows:
        sql_def = row.get("sql_definition", "")
        if not sql_def:
            continue
        results.append(
            DiscoveredObject(
                schema_name=row["schema_name"],
                object_name=row["object_name"],
                object_type=row["object_type"],
                sql_definition=sql_def,
            )
        )
    return results
