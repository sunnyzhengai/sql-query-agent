"""Load and query the data dictionary (dict_tables, dict_columns).

The data dictionary is the source of truth for table/column descriptions.
Descriptions are cached as node properties at graph build time.

Matching is case-insensitive (ADR 0016): lookups fold identifiers to the
canonical uppercase form, mirroring SQL Server's default collation. Stored
TableInfo/ColumnInfo keep the customer's original casing for display.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.parser.identity import fold_identifier

logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    table_name: str
    description: str


@dataclass
class ColumnInfo:
    table_name: str
    column_name: str
    description: str


class DataDictionary:
    """In-memory representation of the data dictionary.

    In Fabric, this will be loaded from Delta tables.
    For local dev/testing, loaded from seed data or fixtures.
    """

    def __init__(self) -> None:
        self.tables: dict[str, TableInfo] = {}
        self.columns: dict[str, list[ColumnInfo]] = {}  # keyed by table_name

    def add_table(self, table_name: str, description: str) -> None:
        self.tables[fold_identifier(table_name)] = TableInfo(
            table_name=table_name, description=description
        )

    def add_column(self, table_name: str, column_name: str, description: str) -> None:
        self.columns.setdefault(fold_identifier(table_name), []).append(
            ColumnInfo(table_name=table_name, column_name=column_name, description=description)
        )

    def get_table_description(self, table_name: str) -> str:
        info = self.tables.get(fold_identifier(table_name))
        return info.description if info else ""

    def get_column_description(self, table_name: str, column_name: str) -> str:
        folded_column = fold_identifier(column_name)
        for col in self.columns.get(fold_identifier(table_name), []):
            if fold_identifier(col.column_name) == folded_column:
                return col.description
        return ""

    def get_columns_for_table(self, table_name: str) -> list[ColumnInfo]:
        return self.columns.get(fold_identifier(table_name), [])


def find_cross_schema_collisions(
    schema_table_pairs: "list[tuple[str, str]]",
) -> "dict[str, list[str]]":
    """Detect bare table names claimed by more than one schema.

    The dictionary matches tables schema-agnostically (it has no schema
    column), so a bare name appearing in multiple schemas makes description
    attachment ambiguous. Returns {folded_table_name: sorted folded schemas}
    for each ambiguous name. Used by the 500_validate gate (ADR 0016).
    """
    schemas_by_table: "dict[str, set[str]]" = {}
    for schema, table in schema_table_pairs:
        schemas_by_table.setdefault(fold_identifier(table), set()).add(
            fold_identifier(schema)
        )
    return {
        table: sorted(schemas)
        for table, schemas in schemas_by_table.items()
        if len(schemas) > 1
    }


# SQL keywords that follow FROM/JOIN without being table names.
_NOT_TABLE_WORDS = frozenset({
    "SELECT", "WHERE", "SET", "BEGIN", "END", "AS", "ON", "AND", "OR",
    "NOT", "NULL", "TABLE", "VIEW", "PROCEDURE", "CASE", "WHEN", "THEN",
    "ELSE", "IN", "IS", "LIKE",
})

_TABLE_REF = None  # compiled lazily; regex belongs here, not in notebooks


def preview_table_references(sql_texts: "list[str]") -> "set[str]":
    """ROUGH table-name harvest from raw SQL, for the 100_install coverage
    PREVIEW only — 500_validate's dictionary_coverage (parse-based) is the
    authoritative, blocking check. Text-scanning is banned as a lineage
    source (native-parsers doctrine); this exists solely so the installer
    can say "your dictionary probably misses these" before the first
    parse ever runs."""
    global _TABLE_REF
    import re as _re

    if _TABLE_REF is None:
        _TABLE_REF = _re.compile(
            r"(?:FROM|JOIN)\s+(?:\[?\w+\]?\.)?(?:\[?\w+\]?\.)?\[?(\w+)\]?",
            _re.IGNORECASE,
        )
    refs: "set[str]" = set()
    for sql in sql_texts:
        for match in _TABLE_REF.finditer(sql or ""):
            name = match.group(1)
            if name.upper() not in _NOT_TABLE_WORDS and not name.startswith("#"):
                refs.add(name.upper())
    return refs
