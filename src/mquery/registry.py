"""The shape registry — one entry per known partition shape.

A peer of TABLE_REGISTRY and INTEGRATION_REGISTRY: the declarative
authority on which M partition shapes the product handles. CI enforces
that every `supported` shape has a fixture that BOTH classifies to its
entry AND yields a source through parse_tmdl_partition — a supported
claim without a passing fixture is a lie the tests reject.

Statuses:
  supported                the extractor produces lineage for this shape
  recognized_unsupported   correct to skip; must land as a fallout row
  (unknown)                anything matching no entry — signature
                           attached to its fallout row so the shape can
                           be filed, fixed, and shipped (support loop:
                           signature in -> fixture added -> handler in
                           the next wheel; no on-site troubleshooting)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Shape:
    name: str
    status: str          # "supported" | "recognized_unsupported"
    match: "Callable[[str, str, list[str]], bool]"  # (family, sig, arg_kinds)
    notes: str = ""


def _query_arg_ok(kind: str) -> bool:
    # the exec target lives in the first literal chunk — a literal, or a
    # concatenation whose HEAD is a literal, is extractable
    return kind == "literal" or kind.startswith("concat(literal")


def _record_query_ok(kind: str) -> bool:
    if not kind.startswith("record{"):
        return False
    for part in kind[7:-1].split(", "):
        if part.startswith("Query="):
            return _query_arg_ok(part[len("Query="):])
    return False


_NON_SQL_FAMILIES = {
    "Snowflake.Databases": "live Snowflake estates exist (21 at one "
                           "customer) — connector-roadmap datapoint",
    "GoogleBigQuery.Database": "connector-roadmap datapoint",
    "Databricks.Catalogs": "connector-roadmap datapoint",
    "AnalysisServices.Database": "AS/live-connect — no SQL lineage",
    "AnalysisServices.Databases": "AS/live-connect — no SQL lineage",
    "Folder.Files": "file-drop source, not SQL",
    "File.Contents": "file source, not SQL",
    "Excel.Workbook": "spreadsheet source, not SQL",
    "Web.Contents": "web source, not SQL",
    "Web.BrowserContents": "web source, not SQL",
    "SharePoint.Files": "SharePoint source, not SQL",
    "SharePoint.Tables": "SharePoint source, not SQL",
    "SharePoint.Contents": "SharePoint source, not SQL",
    "ActiveDirectory.Domains": "directory source, not SQL",
    "PowerPlatform.Dataflows": "dataflow indirection — future traversal",
    "PowerBI.Dataflows": "dataflow indirection — future traversal",
    "Table.FromRows": "hand-entered rows (parameter/config tables)",
    "Table.FromRecords": "hand-entered rows",
    "Table.FromColumns": "hand-entered rows",
    "List.Dates": "generated calendar",
    "DateTime.LocalNow": "generated timestamp",
    "DateTime.FixedLocalNow": "generated timestamp",
    "#table": "hand-entered inline table",
}


SHAPE_REGISTRY: "list[Shape]" = [
    Shape(
        "odbc_datasource_navigation", "supported",
        lambda fam, sig, args: fam == "Odbc.DataSource" and ".nav" in sig,
        "DSN + Name/Kind navigation (pattern 1); 99.5% field parse rate",
    ),
    Shape(
        "odbc_query", "supported",
        lambda fam, sig, args: fam == "Odbc.Query" and len(args) >= 2
        and _query_arg_ok(args[1]),
        "Odbc.Query(server-arg, query) — server may be literal, "
        "parameter, or quoted identifier; query may be concatenated "
        "(first literal chunk carries the exec target)",
    ),
    Shape(
        "sql_database_query", "supported",
        lambda fam, sig, args: fam == "Sql.Database" and len(args) >= 3
        and _record_query_ok(args[2]),
        "Sql.Database(server-arg, db, [Query=...]) incl. the three field "
        "pattern-breakers (param server / brackets / concat)",
    ),
    Shape(
        "sql_database_navigation", "supported",
        lambda fam, sig, args: fam == "Sql.Database" and ".nav" in sig
        and (len(args) < 3 or not _record_query_ok(args[2])),
        "Sql.Database with Name/Kind navigation instead of Query",
    ),
    Shape(
        "sql_databases_navigation", "supported",
        lambda fam, sig, args: fam == "Sql.Databases",
        "Sql.Databases(server) + navigation (pattern 4)",
    ),
] + [
    Shape(
        f"non_sql:{family}", "recognized_unsupported",
        (lambda fam_, sig, args, _f=family: fam_ == _f),
        notes,
    )
    for family, notes in _NON_SQL_FAMILIES.items()
] + [
    Shape(
        "custom_reference", "recognized_unsupported",
        lambda fam, sig, args: fam == "ref" and sig in
        ("parameter", "ref(query)", "parameter.nav", "ref(query).nav"),
        "reference to a customer-defined shared query — lineage lives in "
        "the referenced query, not this partition",
    ),
]


def classify_shape(family: str, signature: str,
                   arg_kinds: "list[str]") -> "tuple[str, str]":
    """(shape_name, status); unknown shapes -> ('unknown', 'unknown')."""
    for shape in SHAPE_REGISTRY:
        if shape.match(family, signature, arg_kinds):
            return (shape.name, shape.status)
    return ("unknown", "unknown")
