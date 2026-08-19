"""The parse model + the ONE parse entry point (native parser only).

History (2026-08-19): this module used to hold a ~400-line
sqlparse/sqlglot fallback parser for dev machines. It was the source
of the environment-fragile golden failures, produced different
structure than production on hard cases, and kept resurfacing as an
expedient default. Sunny's ruling: "under no circumstances" — the
native-parser law (ADR 0001). parse_sql now delegates to ScriptDom
everywhere (Fabric, dev, CI) via src/parser/scriptdom_loader; where
ScriptDom cannot load, parsing FAILS with the remediation instead of
silently degrading to a different grammar.

What remains here is the shared parse MODEL (ParsedSQL/CTEInfo/
TableRef/ColumnRef), text normalization, and parse_sql itself.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ColumnRef:
    table: str | None
    column: str


@dataclass
class TableRef:
    """A fully qualified table reference: database.schema.table.

    SQL Server forms: table, schema.table, db.schema.table, db..table
    Default schema is 'dbo' when omitted.
    """

    table: str
    schema: str = "dbo"
    database: str | None = None

    @property
    def qualified_name(self) -> str:
        """schema.table (e.g., 'dbo.PATIENT')."""
        return f"{self.schema}.{self.table}"

    @property
    def full_name(self) -> str:
        """database.schema.table if database known, else schema.table."""
        if self.database:
            return f"{self.database}.{self.schema}.{self.table}"
        return self.qualified_name

    def __str__(self) -> str:
        return self.qualified_name

    def __eq__(self, other) -> bool:
        if isinstance(other, TableRef):
            return self.table == other.table and self.schema == other.schema
        if isinstance(other, str):
            # Allow string comparison for backward compatibility
            return self.table == other or self.qualified_name == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.schema, self.table))


@dataclass
class CTEInfo:
    """A single CTE extracted from a SQL statement."""

    name: str
    sql_fragment: str
    column_refs: list[ColumnRef] = field(default_factory=list)
    table_refs: list[TableRef] = field(default_factory=list)  # physical tables (fully qualified)
    depends_on: list[str] = field(default_factory=list)  # other CTE/temp table names


@dataclass
class ParsedSQL:
    """Result of parsing a SQL statement."""

    ctes: list[CTEInfo] = field(default_factory=list)
    final_select_tables: list[TableRef] = field(default_factory=list)    # physical tables only
    final_select_cte_refs: list[str] = field(default_factory=list)  # CTEs referenced by final SELECT
    final_select_columns: list[ColumnRef] = field(default_factory=list)
    normalized_sql: str = ""  # the SQL after normalization (for debugging/review)
    # Count of AST-walk exceptions suppressed during extraction. Nonzero means
    # refs may be MISSING from an otherwise-successful parse — surface it, or
    # "parse success" overstates what was captured (audit 2026-08-15).
    extraction_suppressed: int = 0


def normalize_sql_whitespace(sql: str) -> str:
    """Normalize whitespace in SQL text for clean storage and readability.

    Raw SQL from ScriptDom extraction preserves original formatting with
    \\r\\n\\t characters. Also handles non-breaking spaces (\\xa0) from
    copy-paste in SSMS or web editors.
    """
    # Replace all Unicode whitespace variants with ASCII equivalents
    # Sources: copy-paste from web/Word/PDF, BOM markers, SSMS quirks
    sql = sql.replace('\ufeff', '')      # BOM (byte order mark)
    sql = sql.replace('\u200b', '')      # zero-width space
    sql = sql.replace('\xa0', ' ')       # non-breaking space
    sql = sql.replace('\x0b', '\n')      # vertical tab
    sql = sql.replace('\x0c', '\n')      # form feed
    # Normalize all line ending variants (\r\r\n, \r\n, \r) to \n
    sql = sql.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse multiple spaces/tabs to single space
    sql = re.sub(r'[ \t]+', ' ', sql)
    sql = '\n'.join(line.strip() for line in sql.split('\n') if line.strip())
    return sql


def parse_sql(sql: str, dialect: str = "tsql") -> ParsedSQL:
    """Parse T-SQL into a ParsedSQL structure with the NATIVE parser.

    Raises ValueError on parse errors (callers like parse_step record
    them as ops_parse_errors rows — counted, never silently partial)
    and ScriptDomUnavailable where the runtime cannot host ScriptDom.
    """
    if dialect != "tsql":
        raise ValueError(
            f"unsupported dialect '{dialect}' — per ADR 0001 each dialect "
            f"gets its NATIVE parser; only T-SQL (ScriptDom) is implemented")
    # Lazy imports: scriptdom_fabric imports this module's dataclasses.
    from src.parser.scriptdom_fabric import parse_from_fragment
    from src.parser.scriptdom_loader import parse_tsql

    fragment, errors = parse_tsql(normalize_sql_whitespace(sql))
    if errors:
        raise ValueError(
            f"T-SQL parse errors ({len(errors)}): " + " | ".join(errors[:3]))
    return parse_from_fragment(fragment)
