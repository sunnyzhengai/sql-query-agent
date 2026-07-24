# Paste this as a new cell at the bottom of 02_parse.py
# Run after Cell 0 (ScriptDom is already loaded)

from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
from System.IO import StringReader
from src.parser.scriptdom_fabric import _get_fragment_text

METRIC_ID = "usp_PTA_CensusDashboard_PBI"
raw_sql = spark.sql(f"SELECT sql FROM sql_sources WHERE metric_id = '{METRIC_ID}'").collect()[0]["sql"]

parser = TSql160Parser(True)
reader = StringReader(raw_sql)
parse_result = parser.Parse(reader, None)
fragment = parse_result[0] if isinstance(parse_result, tuple) else parse_result

def walk_refs(node, tables, columns, depth=0):
    if node is None or depth > 10:
        return
    nt = node.GetType().Name
    if nt == "NamedTableReference":
        try:
            tables.append(node.SchemaObject.BaseIdentifier.Value)
        except Exception:
            pass
    elif nt == "ColumnReferenceExpression":
        try:
            multi = node.MultiPartIdentifier
            if multi and multi.Identifiers:
                parts = [multi.Identifiers[k].Value for k in range(multi.Identifiers.Count)]
                columns.append(".".join(parts))
        except Exception:
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
            except Exception:
                continue
    except Exception:
        pass

batch = fragment.Batches[0]
for i in range(batch.Statements.Count):
    stmt = batch.Statements[i]
    stmt_type = stmt.GetType().Name
    print(f"\nStatement {i+1}: {stmt_type}")

    if stmt_type == "SelectStatement" and stmt.WithCtesAndXmlNamespaces:
        ctes = stmt.WithCtesAndXmlNamespaces.CommonTableExpressions
        print(f"  CTEs: {ctes.Count}")
        for j in range(ctes.Count):
            cte = ctes[j]
            cte_name = cte.ExpressionName.Value
            cte_sql = _get_fragment_text(cte.QueryExpression)
            tables = []
            columns = []
            walk_refs(cte.QueryExpression, tables, columns)
            print(f"  CTE '{cte_name}': tables={tables}, columns(first 5)={columns[:5]}")
            print(f"    SQL: {cte_sql[:100]}...")

        tables = []
        columns = []
        walk_refs(stmt.QueryExpression, tables, columns)
        print(f"  Final SELECT: tables={tables}, columns(first 5)={columns[:5]}")

    elif stmt_type == "InsertStatement":
        spec = stmt.InsertSpecification
        target = spec.Target
        if target.GetType().Name == "NamedTableReference":
            print(f"  INTO: {target.SchemaObject.BaseIdentifier.Value}")
        tables = []
        columns = []
        walk_refs(spec.InsertSource, tables, columns)
        print(f"  FROM tables: {tables}")
        print(f"  Columns(first 5): {columns[:5]}")

    elif stmt_type == "SelectStatement":
        tables = []
        columns = []
        walk_refs(stmt, tables, columns)
        print(f"  Tables: {tables}")
        print(f"  Columns(first 5): {columns[:5]}")
