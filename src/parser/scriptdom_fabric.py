"""ScriptDom extraction via pythonnet — for use in Fabric notebooks.

Loads Microsoft's ScriptDom DLL using pythonnet's CoreCLR runtime and
provides extract_with_scriptdom() to parse T-SQL and extract SELECT
statements from stored procedures.

This module only works in Fabric notebooks where pythonnet and the
ScriptDom DLL are available. Import will succeed anywhere, but
load_scriptdom() will raise if the DLL is not found.

Usage in Fabric notebooks:
    from src.parser.scriptdom_fabric import load_scriptdom
    scriptdom_available, extract_fn = load_scriptdom()
    if scriptdom_available:
        queries = extract_fn(raw_sql)
"""

from __future__ import annotations

import re
import sys


def _walk_for_selects(node, queries, _get_text_fn):
    """Recursively walk the ScriptDom AST and collect SELECT/INSERT...SELECT nodes."""
    if node is None:
        return
    node_type = node.GetType().Name
    if node_type == "SelectStatement":
        sql = _get_text_fn(node)
        if sql:
            queries.append(sql)
        return
    if node_type == "InsertStatement":
        spec = node.InsertSpecification
        if spec and spec.InsertSource and spec.InsertSource.GetType().Name == "SelectInsertSource":
            sql = _get_text_fn(node)
            if sql:
                queries.append(sql)
            return
    try:
        for prop in node.GetType().GetProperties():
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue
                if hasattr(value, "StartLine"):
                    _walk_for_selects(value, queries, _get_text_fn)
                elif hasattr(value, "Count"):
                    for j in range(value.Count):
                        item = value[j]
                        if hasattr(item, "StartLine"):
                            _walk_for_selects(item, queries, _get_text_fn)
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


def load_scriptdom(dll_path: str = "/lakehouse/default/Files/sql-query-agent/libs") -> tuple:
    """Load ScriptDom via pythonnet and return (success, extract_function).

    Args:
        dll_path: Path to the directory containing the ScriptDom DLL.

    Returns:
        (True, extract_with_scriptdom) if loaded successfully.
        (False, None) if ScriptDom is not available.
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

        def extract_with_scriptdom(raw_sql: str) -> list[str]:
            """Parse T-SQL with ScriptDom and extract SELECT statements.

            Returns a list of individual SQL query strings with @variables
            replaced by __param_X__ placeholders for sqlglot compatibility.
            """
            parser = TSql160Parser(True)
            reader = StringReader(raw_sql)
            parse_result = parser.Parse(reader, None)
            fragment = parse_result[0] if isinstance(parse_result, tuple) else parse_result
            queries = []
            _walk_for_selects(fragment, queries, _get_fragment_text)
            # Replace @variables with placeholders for sqlglot
            cleaned = [re.sub(r"@(\w+)", r"__param_\1__", q) for q in queries]
            return cleaned

        return True, extract_with_scriptdom

    except Exception as e:
        return False, None
