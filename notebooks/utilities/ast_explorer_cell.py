# Paste this as a new cell at the bottom of the 200_parse notebook
# Run after Cell 0 (ScriptDom is already loaded)
# Change METRIC_ID to test different procs

from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
from System.IO import StringReader

from src.parser.scriptdom_fabric import _get_fragment_text

METRIC_ID = "usp_PTA_CensusDashboard_PBI"  # <- change to the proc you are debugging
raw_sql = spark.sql(f"SELECT sql FROM input_sql_sources WHERE metric_id = '{METRIC_ID}'").collect()[0]["sql"]

parser = TSql160Parser(True)
reader = StringReader(raw_sql)
parse_result = parser.Parse(reader, None)
fragment = parse_result[0] if isinstance(parse_result, tuple) else parse_result

def find_statements(node, results, depth=0):
    if node is None or depth > 20:
        return
    nt = node.GetType().Name
    if nt in ("SelectStatement", "InsertStatement"):
        results.append(node)
        return
    try:
        for prop in node.GetType().GetProperties():
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue
                if hasattr(value, "StartLine"):
                    find_statements(value, results, depth + 1)
                elif hasattr(value, "Count"):
                    for j in range(value.Count):
                        item = value[j]
                        if hasattr(item, "StartLine"):
                            find_statements(item, results, depth + 1)
            except Exception:  # noqa: BLE001, S110, S112 — best-effort AST exploration; tree may be truncated where reflection throws
                continue
    except Exception:  # noqa: BLE001, S110, S112 — best-effort AST exploration; tree may be truncated where reflection throws
        pass

def walk_refs(node, tables, columns, depth=0):
    if node is None or depth > 15:
        return
    nt = node.GetType().Name
    if nt == "NamedTableReference":
        try:
            tables.append(node.SchemaObject.BaseIdentifier.Value)
        except Exception:  # noqa: BLE001, S110, S112 — best-effort AST exploration; tree may be truncated where reflection throws
            pass
    elif nt == "ColumnReferenceExpression":
        try:
            multi = node.MultiPartIdentifier
            if multi and multi.Identifiers:
                parts = [multi.Identifiers[k].Value for k in range(multi.Identifiers.Count)]
                columns.append(".".join(parts))
        except Exception:  # noqa: BLE001, S110, S112 — best-effort AST exploration; tree may be truncated where reflection throws
            pass
    try:
        for prop in node.GetType().GetProperties():
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue
                if hasattr(value, "StartLine"):
                    walk_refs(value, tables, columns, depth + 1)
                elif hasattr(value, "Count"):
                    for k in range(value.Count):
                        item = value[k]
                        if hasattr(item, "StartLine"):
                            walk_refs(item, tables, columns, depth + 1)
            except Exception:  # noqa: BLE001, S110, S112 — best-effort AST exploration; tree may be truncated where reflection throws
                continue
    except Exception:  # noqa: BLE001, S110, S112 — best-effort AST exploration; tree may be truncated where reflection throws
        pass

stmts = []
find_statements(fragment, stmts)
print(f"Found {len(stmts)} statements\n")

for i, stmt in enumerate(stmts):
    nt = stmt.GetType().Name
    sql_preview = _get_fragment_text(stmt)[:100]
    print(f"--- Statement {i+1}: {nt} ({len(_get_fragment_text(stmt))} chars) ---")
    print(f"Preview: {sql_preview}...")

    if nt == "SelectStatement" and stmt.WithCtesAndXmlNamespaces:
        ctes = stmt.WithCtesAndXmlNamespaces.CommonTableExpressions
        print(f"CTEs: {ctes.Count}")
        for j in range(ctes.Count):
            cte = ctes[j]
            cte_name = cte.ExpressionName.Value
            t = []
            c = []
            walk_refs(cte.QueryExpression, t, c)
            print(f"  '{cte_name}': tables={t}, cols(5)={c[:5]}")

    if nt == "InsertStatement":
        spec = stmt.InsertSpecification
        if spec.Target and spec.Target.GetType().Name == "NamedTableReference":
            print(f"INTO: {spec.Target.SchemaObject.BaseIdentifier.Value}")

    tables = []
    columns = []
    walk_refs(stmt, tables, columns)
    print(f"All tables: {tables}")
    print(f"All columns (first 10): {columns[:10]}")
    print()
