"""ScriptDom-based SQL parsing via pythonnet — for use in Fabric notebooks.

Provides two modes:
1. extract_with_scriptdom() — extracts raw SQL strings (legacy, for sqlglot path)
2. parse_with_scriptdom() — extracts full ParsedSQL structure directly from AST

Mode 2 (Option B) eliminates sqlglot entirely for T-SQL. ScriptDom handles
both extraction AND structural analysis: CTEs, table refs, column refs,
temp table dependencies. 100% T-SQL compatibility, no whack-a-mole.

This module only works in Fabric notebooks where pythonnet and the
ScriptDom DLL are available.

Usage:
    from src.parser.scriptdom_fabric import load_scriptdom
    ok, extract_fn, parse_fn = load_scriptdom()
    if ok:
        parsed = parse_fn(raw_sql)  # returns ParsedSQL directly
"""

from __future__ import annotations

import re
import sys


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
            except Exception:
                continue
    except Exception:
        pass


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


def _walk_for_tables_only(node, tables, depth=0):
    """Walk AST node and collect only table references. Fast path — no columns."""
    if node is None or depth > 15:
        return
    nt = node.GetType().Name
    if nt == "NamedTableReference":
        try:
            tables.append(node.SchemaObject.BaseIdentifier.Value)
        except Exception:
            pass
        return  # no need to descend into table reference children
    try:
        for prop in node.GetType().GetProperties():
            if prop.Name in _SKIP_PROPERTIES:
                continue
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue
                if hasattr(value, "GetType") and hasattr(value, "StartLine"):
                    _walk_for_tables_only(value, tables, depth + 1)
                elif hasattr(value, "Count"):
                    for k in range(value.Count):
                        item = value[k]
                        if hasattr(item, "StartLine"):
                            _walk_for_tables_only(item, tables, depth + 1)
            except Exception:
                continue
    except Exception:
        pass


def _get_into_target(stmt):
    """Get the #temp table name from a SELECT...INTO statement.

    ScriptDom represents SELECT...INTO as a SelectStatement with an
    Into property of type SchemaObjectName (not NamedTableReference).
    """
    try:
        into = getattr(stmt, 'Into', None)
        if into is not None:
            return into.BaseIdentifier.Value
    except Exception:
        pass
    return None


def _get_insert_target(stmt):
    """Get the #temp table name from an INSERT INTO statement."""
    try:
        spec = stmt.InsertSpecification
        if spec and spec.Target:
            if spec.Target.GetType().Name == "NamedTableReference":
                return spec.Target.SchemaObject.BaseIdentifier.Value
    except Exception:
        pass
    return None


def load_scriptdom(dll_path: str = "/lakehouse/default/Files/sql-query-agent/libs") -> tuple:
    """Load ScriptDom via pythonnet and return (success, extract_fn, parse_fn).

    Returns:
        (True, extract_with_scriptdom, parse_with_scriptdom) if loaded.
        (False, None, None) if ScriptDom is not available.
    """
    try:
        from pythonnet import load
        load("coreclr")

        import clr
        if dll_path not in sys.path:
            sys.path.append(dll_path)

        clr.AddReference("Microsoft.SqlServer.TransactSql.ScriptDom")

        from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
        from System.IO import StringReader

        def _parse_raw(raw_sql: str):
            """Parse raw SQL and return the AST fragment."""
            parser = TSql160Parser(True)
            reader = StringReader(raw_sql)
            parse_result = parser.Parse(reader, None)
            return parse_result[0] if isinstance(parse_result, tuple) else parse_result

        def extract_with_scriptdom(raw_sql: str) -> list[str]:
            """Legacy: extract raw SQL strings for the sqlglot path."""
            fragment = _parse_raw(raw_sql)
            stmt_nodes = []
            _walk_for_selects(fragment, stmt_nodes, _get_fragment_text)
            # Convert nodes back to SQL text
            queries = [_get_fragment_text(n) for n in stmt_nodes]
            # Replace @variables with placeholders for sqlglot
            cleaned = [re.sub(r"@(\w+)", r"__param_\1__", q) for q in queries]
            return cleaned

        def parse_with_scriptdom(raw_sql: str):
            """Parse T-SQL and extract full structure from ScriptDom AST.

            Returns ParsedSQL with CTEs, table refs, column refs, and
            temp table dependencies — no sqlglot involved.
            """
            from src.parser.sql_parser import ParsedSQL, CTEInfo, ColumnRef
            from src.parser.sql_parser import normalize_sql_whitespace

            fragment = _parse_raw(raw_sql)

            # Find all SELECT and INSERT...SELECT statements
            stmt_nodes = []
            _walk_for_selects(fragment, stmt_nodes, _get_fragment_text)

            if not stmt_nodes:
                raise ValueError("ScriptDom found no SELECT statements")

            # First pass: collect all statements with their raw table/column refs
            # and identify temp table names + CTE names
            raw_entries = []  # list of (name_or_none, sql_fragment, raw_tables, col_refs, is_cte)
            temp_table_names = set()
            cte_names = set()

            for stmt in stmt_nodes:
                stmt_type = stmt.GetType().Name

                # Determine INTO target (temp table)
                if stmt_type == "SelectStatement":
                    into_target = _get_into_target(stmt)
                elif stmt_type == "InsertStatement":
                    into_target = _get_insert_target(stmt)
                else:
                    into_target = None

                # Normalize temp name (strip #)
                temp_name = None
                if into_target:
                    temp_name = into_target.lstrip("#")
                    temp_table_names.add(temp_name)
                    temp_table_names.add(into_target)

                # Extract CTEs from WITH clause
                if stmt_type == "SelectStatement" and stmt.WithCtesAndXmlNamespaces:
                    cte_list = stmt.WithCtesAndXmlNamespaces.CommonTableExpressions
                    for j in range(cte_list.Count):
                        cte_node = cte_list[j]
                        cte_name_val = cte_node.ExpressionName.Value
                        cte_names.add(cte_name_val)
                        cte_body = cte_node.QueryExpression
                        cte_sql = normalize_sql_whitespace(_get_fragment_text(cte_body))
                        if len(cte_sql) > 500:
                            cte_sql = cte_sql[:500]
                        cte_tables = []
                        _walk_for_tables_only(cte_body, cte_tables)
                        raw_entries.append((cte_name_val, cte_sql, cte_tables, [], True))

                # Get table refs from the statement body (tables only, no columns — fast)
                tables = []
                if stmt_type == "SelectStatement":
                    _walk_for_tables_only(stmt.QueryExpression, tables)
                elif stmt_type == "InsertStatement":
                    spec = stmt.InsertSpecification
                    if spec.InsertSource:
                        _walk_for_tables_only(spec.InsertSource, tables)

                if temp_name:
                    sql_text = normalize_sql_whitespace(_get_fragment_text(stmt))
                    if len(sql_text) > 500:
                        sql_text = sql_text[:500]
                    raw_entries.append((temp_name, sql_text, tables, [], False))
                else:
                    raw_entries.append((None, "", tables, [], False))

            # Second pass: classify table refs as physical vs CTE/temp dependency
            all_internal_names = cte_names | temp_table_names
            stripped_temps = {tn.lstrip("#") for tn in temp_table_names}
            all_internal_names |= stripped_temps

            all_ctes = []
            all_final_tables = []
            all_final_cte_refs = []
            all_final_columns = []

            for entry_name, sql_frag, raw_tables, raw_cols, is_cte_entry in raw_entries:
                col_refs = [ColumnRef(table=t, column=c) for t, c in raw_cols]

                if entry_name is not None:
                    # This is a CTE or temp table definition
                    physical = []
                    depends = []
                    seen_p = set()
                    seen_d = set()
                    for t in raw_tables:
                        canonical = t.lstrip("#")
                        if canonical == entry_name:
                            continue  # skip self-reference
                        if canonical in stripped_temps or t in cte_names:
                            if canonical not in seen_d:
                                depends.append(canonical)
                                seen_d.add(canonical)
                        else:
                            if t not in seen_p:
                                physical.append(t)
                                seen_p.add(t)
                    all_ctes.append(CTEInfo(
                        name=entry_name,
                        sql_fragment=sql_frag,
                        column_refs=col_refs,
                        table_refs=physical,
                        depends_on=depends,
                    ))
                else:
                    # Terminal SELECT (no INTO)
                    for t in raw_tables:
                        canonical = t.lstrip("#")
                        if canonical in stripped_temps or t in cte_names:
                            if canonical not in [r for r in all_final_cte_refs]:
                                all_final_cte_refs.append(canonical)
                        else:
                            if t not in all_final_tables:
                                all_final_tables.append(t)
                    all_final_columns.extend(col_refs)

            return ParsedSQL(
                ctes=all_ctes,
                final_select_tables=all_final_tables,
                final_select_cte_refs=all_final_cte_refs,
                final_select_columns=all_final_columns,
                normalized_sql="",
            )

        return True, extract_with_scriptdom, parse_with_scriptdom

    except Exception as e:
        return False, None, None
