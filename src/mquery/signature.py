"""Shape signatures with argument kinds, whitelist-anonymized.

Amendment 1 (field-proven): the same source function appears on BOTH the
parsed and missed sides — literal vs parameter vs concatenated arguments
is the discriminator, so signatures MUST carry argument kinds.

Amendment 2: anonymization is WHITELIST-based. Only names in M_STDLIB
appear verbatim; every unrecognized identifier becomes parameter /
ref(query) / ref(function). A custom query named SecretRevenueForecast
can never reach a signature — there is no strip list to be incomplete.
"""

from __future__ import annotations

from src.mquery.parser import (
    BinOp,
    Call,
    Each,
    FieldAccess,
    If,
    ItemAccess,
    Let,
    Lit,
    Lst,
    Opaque,
    Rec,
    Ref,
)

# Recognized M standard-library names — the ONLY identifiers allowed
# verbatim in a signature. Extend freely: adding a stdlib name can only
# make signatures more precise, never leak (customer identifiers are
# not stdlib names).
M_STDLIB = frozenset({
    "Odbc.Query", "Odbc.DataSource", "OleDb.Query", "OleDb.DataSource",
    "Sql.Database", "Sql.Databases", "Value.NativeQuery",
    "Snowflake.Databases", "GoogleBigQuery.Database",
    "AnalysisServices.Database", "AnalysisServices.Databases",
    "Databricks.Catalogs", "Oracle.Database", "PostgreSQL.Database",
    "MySQL.Database", "Teradata.Database",
    "Folder.Files", "File.Contents", "Excel.Workbook", "Csv.Document",
    "Json.Document", "Xml.Tables", "Web.Contents", "Web.BrowserContents",
    "SharePoint.Files", "SharePoint.Tables", "SharePoint.Contents",
    "ActiveDirectory.Domains", "PowerPlatform.Dataflows",
    "PowerBI.Dataflows", "Fabric.Warehouse", "Lakehouse.Contents",
    "Table.FromRows", "Table.FromRecords", "Table.FromColumns",
    "Table.Combine", "Table.NestedJoin", "Table.Join",
    "Table.TransformColumnTypes", "Table.SelectRows", "Table.SelectColumns",
    "Table.RenameColumns", "Table.AddColumn", "Table.RemoveColumns",
    "Table.ExpandTableColumn", "Table.PromoteHeaders", "Table.Sort",
    "Table.Distinct", "Table.Buffer", "Table.Schema",
    "List.Dates", "List.Numbers", "List.Transform",
    "DateTime.LocalNow", "DateTime.FixedLocalNow", "DateTime.Date",
    "Date.From", "Date.AddDays", "Duration.From",
    "Text.From", "Text.Combine", "Number.From", "Value.Type",
    "Binary.Decompress", "Binary.FromText",
    "#table", "#date", "#datetime", "#duration", "#time",
})

# Record keys that may appear verbatim (connector option names — API
# vocabulary, not customer data). Unrecognized keys become "field".
RECORD_KEYS = frozenset({
    "Query", "NativeQuery", "HierarchicalNavigation",
    "CreateNavigationProperties", "CommandTimeout", "Timeout",
    "MultiSubnetFailover", "Implementation", "EnableFolding",
    "UseNativeQuery", "ReturnSingleDatabase", "Name", "Kind", "Data",
    "Item", "Schema", "Catalog",
})

# Functions that acquire data from somewhere (vs transform it) — the
# census family is the FIRST of these found in the resolved chain.
SOURCE_FUNCTIONS = frozenset({
    "Odbc.Query", "Odbc.DataSource", "OleDb.Query", "OleDb.DataSource",
    "Sql.Database", "Sql.Databases", "Value.NativeQuery",
    "Snowflake.Databases", "GoogleBigQuery.Database",
    "AnalysisServices.Database", "AnalysisServices.Databases",
    "Databricks.Catalogs", "Oracle.Database", "PostgreSQL.Database",
    "MySQL.Database", "Teradata.Database",
    "Folder.Files", "File.Contents", "Excel.Workbook", "Web.Contents",
    "Web.BrowserContents", "SharePoint.Files", "SharePoint.Tables",
    "SharePoint.Contents", "ActiveDirectory.Domains",
    "PowerPlatform.Dataflows", "PowerBI.Dataflows", "Fabric.Warehouse",
    "Lakehouse.Contents", "Table.FromRows", "Table.FromRecords",
    "Table.FromColumns", "List.Dates", "DateTime.LocalNow",
    "DateTime.FixedLocalNow", "#table",
})


def _resolve(node, bindings: "dict[str, object]", depth: int = 0):
    """Follow let-binding references so `in Source` reaches the chain."""
    while isinstance(node, Ref) and node.name in bindings and depth < 50:
        node = bindings[node.name]
        depth += 1
    return node


def _flatten_concat(node) -> "list":
    if isinstance(node, BinOp) and node.op == "&":
        return _flatten_concat(node.left) + _flatten_concat(node.right)
    return [node]


def kind_of(node, bindings: "dict[str, object]" = {}) -> str:  # noqa: B006
    """The anonymized kind label for a node. Whitelisted stdlib names
    pass through; everything else is a kind, never a name."""
    node_r = node
    if isinstance(node, Ref) and node.name in bindings:
        node_r = _resolve(node, bindings)
        if node_r is node:  # self-reference guard
            node_r = node
    node = node_r
    if isinstance(node, Lit):
        return "literal"
    if isinstance(node, Ref):
        return node.name if node.name in M_STDLIB else "parameter"
    if isinstance(node, BinOp):
        if node.op == "&":
            parts = [kind_of(p, bindings) for p in _flatten_concat(node)]
            return f"concat({', '.join(parts)})"
        return "expr"
    if isinstance(node, Rec):
        fields = ", ".join(
            f"{k if k in RECORD_KEYS else 'field'}={kind_of(v, bindings)}"
            for k, v in node.fields
        )
        return f"record{{{fields}}}"
    if isinstance(node, Lst):
        return "list"
    if isinstance(node, Call):
        fn = node.name if node.name in M_STDLIB else "ref(function)"
        args = ", ".join(kind_of(a, bindings) for a in node.args)
        return f"{fn}({args})"
    if isinstance(node, (FieldAccess, ItemAccess)):
        steps = 0
        base = node
        while isinstance(base, (FieldAccess, ItemAccess)):
            base = base.base
            steps += 1
        base = _resolve(base, bindings)
        return f"{kind_of(base, bindings)}.nav"
    if isinstance(node, (Each, If)):
        return "expr"
    if isinstance(node, Let):
        inner = dict(bindings)
        inner.update({n: v for n, v in node.bindings})
        return kind_of(node.body, inner)
    if isinstance(node, Opaque):
        return "opaque"
    return "ref(query)"


def _find_source_call(node, bindings: "dict[str, object]", seen=None):
    """First SOURCE_FUNCTIONS call reachable from the node."""
    if seen is None:
        seen = set()
    if id(node) in seen:
        return None
    seen.add(id(node))
    if isinstance(node, Call):
        if node.name in SOURCE_FUNCTIONS:
            return node
        found = _find_source_call(node.func, bindings, seen)
        if found:
            return found
        for a in node.args:
            found = _find_source_call(a, bindings, seen)
            if found:
                return found
    if isinstance(node, Ref) and node.name in bindings:
        return _find_source_call(bindings[node.name], bindings, seen)
    if isinstance(node, Let):
        inner = dict(bindings)
        inner.update({n: v for n, v in node.bindings})
        return _find_source_call(node.body, inner, seen)
    if isinstance(node, BinOp):
        return (_find_source_call(node.left, bindings, seen)
                or _find_source_call(node.right, bindings, seen))
    if isinstance(node, (FieldAccess, ItemAccess)):
        return _find_source_call(node.base, bindings, seen)
    if isinstance(node, Rec):
        for _, v in node.fields:
            found = _find_source_call(v, bindings, seen)
            if found:
                return found
    if isinstance(node, Lst):
        for item in node.items:
            found = _find_source_call(item, bindings, seen)
            if found:
                return found
    if isinstance(node, (Each, If)):
        for child in ([node.body] if isinstance(node, Each)
                      else [node.cond, node.then, node.els]):
            found = _find_source_call(child, bindings, seen)
            if found:
                return found
    return None


def partition_shape(m_text: str) -> "tuple[str, str, list[str]]":
    """(family, signature, arg_kinds) for a partition M expression.

    family:    the source function name (whitelisted) | "ref" (custom
               query/function reference) | "opaque" (outside the subset)
    signature: whitelist-anonymized skeleton of the resolved chain
    arg_kinds: the source call's argument kinds (census discriminator)
    """
    from src.mquery.parser import parse_m

    ast = parse_m(m_text)
    if isinstance(ast, Opaque):
        return ("opaque", "opaque", [])
    bindings: "dict[str, object]" = {}
    if isinstance(ast, Let):
        bindings = {n: v for n, v in ast.bindings}
    src_call = _find_source_call(ast, bindings)
    signature = kind_of(ast, bindings)
    if src_call is None:
        return ("ref", signature, [])
    arg_kinds = [kind_of(a, bindings) for a in src_call.args]
    return (src_call.name, signature, arg_kinds)
