"""ScriptDom-based SQL parsing via pythonnet — for use in Fabric notebooks.

Provides two modes:
1. extract_with_scriptdom() — extracts raw SQL strings (legacy, for sqlglot path)
2. parse_with_scriptdom() — extracts full ParsedSQL structure directly from AST

Mode 2 (Option B) eliminates sqlglot entirely for T-SQL. ScriptDom handles
both extraction AND structural analysis: CTEs, table refs, column refs,
temp table dependencies. 100% T-SQL compatibility, no whack-a-mole.

This module only works where pythonnet and the ScriptDom DLL are available
(Fabric notebooks; locally with a .NET runtime + libs/ DLL).

Usage (see 200_parse Cell 0): the caller initializes pythonnet + the DLL,
builds the AST with TSql160Parser, then calls parse_from_fragment(fragment)
to get a ParsedSQL directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.parser.sql_parser import ParsedSQL

import re

_suppressed = 0


def _note_suppressed() -> None:
    """Count a swallowed AST-walk exception.

    Reflection over .NET fragment objects throws per-property; skipping the
    property is the intended best-effort behavior, but the COUNT must
    surface — N suppressed extractions can mean table/column refs missing
    from a parse that still reports success (audit 2026-08-15). The total
    lands on ParsedSQL.extraction_suppressed.
    """
    global _suppressed
    _suppressed += 1


def _walk_for_selects(node, results, _get_text_fn):
    """Recursively walk the AST and collect SelectStatement/InsertStatement nodes.

    Stops descending into a branch once a SELECT/INSERT is found (they're
    leaf nodes for our purposes — we don't want nested subquery SELECTs).
    """
    if node is None:
        return
    node_type = node.GetType().Name
    if node_type == "SelectStatement":
        results.append(node)
        return  # don't descend into subqueries
    if node_type == "InsertStatement":
        spec = node.InsertSpecification
        if spec and spec.InsertSource and spec.InsertSource.GetType().Name == "SelectInsertSource":
            results.append(node)
            return
    try:
        for prop in node.GetType().GetProperties():
            if prop.Name in _SKIP_PROPERTIES:
                continue
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue
                if hasattr(value, "GetType") and hasattr(value, "StartLine"):
                    _walk_for_selects(value, results, _get_text_fn)
                elif hasattr(value, "Count"):
                    for j in range(value.Count):
                        item = value[j]
                        if hasattr(item, "StartLine"):
                            _walk_for_selects(item, results, _get_text_fn)
            except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
                _note_suppressed()
                continue
    except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
        _note_suppressed()


def _get_fragment_text(fragment):
    """Extract original SQL text from the ScriptDom token stream."""
    tokens = fragment.ScriptTokenStream
    if tokens is None:
        return ""
    start = fragment.FirstTokenIndex
    end = fragment.LastTokenIndex
    if start < 0 or end < 0:
        return ""
    parts = []
    for i in range(start, end + 1):
        if i < tokens.Count:
            parts.append(tokens[i].Text)
    return "".join(parts)


# Properties that never contain AST children — skip these during walks
_SKIP_PROPERTIES = frozenset({
    "StartLine", "StartColumn", "StartOffset", "FragmentLength",
    "FirstTokenIndex", "LastTokenIndex", "ScriptTokenStream",
    "Value", "LargeValue", "IsNot", "IsPrimaryExpression",
    "Collation", "Alias",
})


def _walk_children(node, visitor_fn, depth=0, max_depth=15):
    """Generic AST walker that calls visitor_fn on each node.

    Skips known scalar properties to avoid expensive reflection calls.
    """
    if node is None or depth > max_depth:
        return
    visitor_fn(node)
    try:
        for prop in node.GetType().GetProperties():
            if prop.Name in _SKIP_PROPERTIES:
                continue
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue
                if hasattr(value, "GetType") and hasattr(value, "StartLine"):
                    _walk_children(value, visitor_fn, depth + 1, max_depth)
                elif hasattr(value, "Count"):
                    for k in range(value.Count):
                        item = value[k]
                        if hasattr(item, "StartLine"):
                            _walk_children(item, visitor_fn, depth + 1, max_depth)
            except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
                _note_suppressed()
                continue
    except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
        _note_suppressed()


def _extract_table_ref(schema_object):
    """Extract a (database, schema, table) tuple from a ScriptDom SchemaObject.

    ScriptDom's SchemaObjectName has:
    - ServerIdentifier (linked server)
    - DatabaseIdentifier (database name)
    - SchemaIdentifier (schema name)
    - BaseIdentifier (table name)

    Returns (database, schema, table). Fills in 'dbo' when schema is omitted.
    """
    try:
        table = schema_object.BaseIdentifier.Value
    except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
        _note_suppressed()  # a LOST table reference, not a skipped property
        return None

    database = None
    schema = "dbo"  # SQL Server default

    try:
        if schema_object.DatabaseIdentifier:
            database = schema_object.DatabaseIdentifier.Value
    except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
        _note_suppressed()

    try:
        if schema_object.SchemaIdentifier:
            schema = schema_object.SchemaIdentifier.Value
    except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
        _note_suppressed()  # falls back to dbo — may attach lineage to the wrong schema

    return (database, schema, table)


def _walk_for_refs(node, tables, columns, depth=0):
    """Walk AST node and collect table and column references.

    tables: list of (database, schema, table) tuples
    columns: list of (table_or_alias, column) tuples
    """
    def visitor(n):
        nt = n.GetType().Name
        if nt == "NamedTableReference":
            ref = _extract_table_ref(n.SchemaObject)
            if ref:
                tables.append(ref)
        elif nt == "ColumnReferenceExpression":
            try:
                multi = n.MultiPartIdentifier
                if multi and multi.Identifiers:
                    count = multi.Identifiers.Count
                    if count == 1:
                        columns.append((None, multi.Identifiers[0].Value))
                    elif count >= 2:
                        columns.append((
                            multi.Identifiers[count - 2].Value,
                            multi.Identifiers[count - 1].Value,
                        ))
            except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
                _note_suppressed()  # a LOST column reference

    _walk_children(node, visitor)


def _get_into_target(stmt):
    """Get the #temp table name from a SELECT...INTO statement.

    ScriptDom represents SELECT...INTO as a SelectStatement with an
    Into property of type SchemaObjectName (not NamedTableReference).
    """
    try:
        into = getattr(stmt, 'Into', None)
        if into is not None:
            return into.BaseIdentifier.Value
    except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
        _note_suppressed()  # a SELECT...INTO whose temp-table link is lost
    return None


def _get_insert_target(stmt):
    """Get the #temp table name from an INSERT INTO statement."""
    try:
        spec = stmt.InsertSpecification
        if spec and spec.Target:
            if spec.Target.GetType().Name == "NamedTableReference":
                return spec.Target.SchemaObject.BaseIdentifier.Value
    except Exception:  # noqa: BLE001 — best-effort .NET reflection; counted + surfaced
        _note_suppressed()  # an INSERT whose temp-table link is lost
    return None


def parse_from_fragment(fragment) -> "ParsedSQL":
    """Parse a ScriptDom AST fragment into a ParsedSQL structure.

    This function contains the core AST-walking logic, separated from
    ScriptDom initialization. The notebook handles loading pythonnet and
    parsing raw SQL into a fragment; this function handles the structural
    extraction.

    Args:
        fragment: A ScriptDom TSqlFragment (output of TSql160Parser.Parse())

    Returns:
        ParsedSQL with CTEs, table refs, column refs, and temp table dependencies.
    """
    from src.parser.sql_parser import ColumnRef, CTEInfo, ParsedSQL, TableRef, normalize_sql_whitespace

    global _suppressed
    _suppressed = 0

    # Find all SELECT and INSERT...SELECT statements
    stmt_nodes = []
    _walk_for_selects(fragment, stmt_nodes, _get_fragment_text)

    if not stmt_nodes:
        raise ValueError("ScriptDom found no SELECT statements")

    raw_entries = []
    temp_table_names = set()
    cte_names = set()

    for stmt in stmt_nodes:
        stmt_type = stmt.GetType().Name

        if stmt_type == "SelectStatement":
            into_target = _get_into_target(stmt)
        elif stmt_type == "InsertStatement":
            into_target = _get_insert_target(stmt)
        else:
            into_target = None

        temp_name = None
        if into_target and into_target.startswith("#"):
            # Temp table: SELECT INTO #temp or INSERT INTO #temp
            temp_name = into_target.lstrip("#")
            temp_table_names.add(temp_name)
            temp_table_names.add(into_target)
        elif into_target:
            # Persistent table: INSERT INTO schema.table — treat as final SELECT
            # (don't set temp_name, so it falls into the "final" branch below)
            pass

        if stmt_type == "SelectStatement" and stmt.WithCtesAndXmlNamespaces:
            cte_list = stmt.WithCtesAndXmlNamespaces.CommonTableExpressions
            for j in range(cte_list.Count):
                cte_node = cte_list[j]
                cte_name_val = cte_node.ExpressionName.Value
                cte_names.add(cte_name_val)
                cte_body = cte_node.QueryExpression
                # FULL text, never truncated (2026-08-19): the 500-char cap fed the
                # description LLM amputated SQL (SELECT list only, no WHERE ->
                # fabricated filters) and made same-logic hashes blind past
                # char 500. Display capping is the DISPLAY layer's job.
                cte_sql = normalize_sql_whitespace(_get_fragment_text(cte_body))
                cte_tables, cte_cols = [], []
                _walk_for_refs(cte_body, cte_tables, cte_cols)
                raw_entries.append((cte_name_val, cte_sql, cte_tables, cte_cols, True))

        tables, columns = [], []
        if stmt_type == "SelectStatement":
            _walk_for_refs(stmt.QueryExpression, tables, columns)
        elif stmt_type == "InsertStatement":
            spec = stmt.InsertSpecification
            if spec.InsertSource:
                _walk_for_refs(spec.InsertSource, tables, columns)

        if temp_name:
            sql_text = normalize_sql_whitespace(_get_fragment_text(stmt))
            raw_entries.append((temp_name, sql_text, tables, columns, False))
        else:
            # Final SELECT or INSERT INTO persistent table — capture SQL text
            final_sql_text = normalize_sql_whitespace(_get_fragment_text(stmt))[:2000]
            raw_entries.append((None, final_sql_text, tables, columns, False))

    stripped_temps = {tn.lstrip("#") for tn in temp_table_names}

    all_ctes = []
    all_final_tables = []
    all_final_cte_refs = []
    all_final_columns = []
    all_final_sql_parts = []  # Collect SQL text from final SELECTs

    for entry_name, sql_frag, raw_tables, raw_cols, _ in raw_entries:
        col_refs = [ColumnRef(table=t, column=c) for t, c in raw_cols]

        if entry_name is not None:
            physical, depends = [], []
            seen_p, seen_d = set(), set()
            for db, sch, tbl in raw_tables:
                canonical = tbl.lstrip("#")
                if canonical == entry_name:
                    continue
                if canonical in stripped_temps or tbl in cte_names:
                    if canonical not in seen_d:
                        depends.append(canonical)
                        seen_d.add(canonical)
                else:
                    ref = TableRef(table=tbl, schema=sch, database=db)
                    if ref not in seen_p:
                        physical.append(ref)
                        seen_p.add(ref)
            all_ctes.append(CTEInfo(
                name=entry_name, sql_fragment=sql_frag,
                column_refs=col_refs, table_refs=physical, depends_on=depends,
            ))
        else:
            for db, sch, tbl in raw_tables:
                canonical = tbl.lstrip("#")
                if canonical in stripped_temps or tbl in cte_names:
                    if canonical not in all_final_cte_refs:
                        all_final_cte_refs.append(canonical)
                else:
                    ref = TableRef(table=tbl, schema=sch, database=db)
                    if ref not in all_final_tables:
                        all_final_tables.append(ref)
            all_final_columns.extend(col_refs)
            if sql_frag:
                all_final_sql_parts.append(sql_frag)

    # For procs with no CTEs, normalized_sql captures the full SELECT text
    # so the graph builder can use it as the __final_select__ fragment
    final_sql = "\n\n".join(all_final_sql_parts) if all_final_sql_parts else ""

    return ParsedSQL(
        ctes=all_ctes,
        final_select_tables=all_final_tables,
        final_select_cte_refs=all_final_cte_refs,
        final_select_columns=all_final_columns,
        normalized_sql=final_sql,
        extraction_suppressed=_suppressed,
    )


def extract_from_fragment(fragment) -> list:
    """Extract raw SQL query strings from a ScriptDom AST fragment.

    Legacy function for the sqlglot fallback path. Replaces @parameters
    with __param_X__ placeholders for sqlglot compatibility.

    Args:
        fragment: A ScriptDom TSqlFragment

    Returns:
        List of SQL query strings with parameter placeholders.
    """
    stmt_nodes = []
    _walk_for_selects(fragment, stmt_nodes, _get_fragment_text)
    return [re.sub(r"@(\w+)", r"__param_\1__", _get_fragment_text(s)) for s in stmt_nodes]


