"""Load and query the data dictionary (dict_tables, dict_columns).

The data dictionary is the source of truth for table/column descriptions.
Descriptions are cached as node properties at graph build time.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.config import Config


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
        self.tables[table_name] = TableInfo(table_name=table_name, description=description)

    def add_column(self, table_name: str, column_name: str, description: str) -> None:
        self.columns.setdefault(table_name, []).append(
            ColumnInfo(table_name=table_name, column_name=column_name, description=description)
        )

    def get_table_description(self, table_name: str) -> str:
        info = self.tables.get(table_name)
        return info.description if info else ""

    def get_column_description(self, table_name: str, column_name: str) -> str:
        for col in self.columns.get(table_name, []):
            if col.column_name == column_name:
                return col.description
        return ""

    def get_columns_for_table(self, table_name: str) -> list[ColumnInfo]:
        return self.columns.get(table_name, [])
