"""Fabric Notebook: Explore ScriptDom AST node types

Run this to see what the ScriptDom AST looks like for a real proc.
Helps us understand which node types to walk for CTEs, table refs,
and column refs — so we can extract structure directly from ScriptDom
without using sqlglot.

Prerequisite: Run 01_setup.py first (same session), or paste Cell 0 from 02_parse.
"""

# %% Cell 0: Setup
%pip install pydantic pyyaml sqlglot sqlparse pythonnet

import json
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.parser.scriptdom_fabric import load_scriptdom

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
scriptdom_available, extract_with_scriptdom = load_scriptdom()

def read_source(name_or_path):
    if name_or_path.endswith(".csv"):
        return spark.read.option("header", "true").option("inferSchema", "true").csv(name_or_path)
    elif "abfss://" in name_or_path or "/" in name_or_path:
        return spark.read.format("delta").load(name_or_path)
    else:
        return spark.table(name_or_path)

# %% Cell 1: Pick a proc and parse with ScriptDom
from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
from System.IO import StringReader

METRIC_ID = "usp_PTA_CensusDashboard_PBI"  # Change to any metric

raw_sql = spark.sql(f"SELECT sql FROM sql_sources WHERE metric_id = '{METRIC_ID}'").collect()[0]["sql"]
print(f"Raw SQL: {len(raw_sql)} chars")

parser = TSql160Parser(True)
reader = StringReader(raw_sql)
parse_result = parser.Parse(reader, None)
fragment = parse_result[0] if isinstance(parse_result, tuple) else parse_result

print(f"Root node type: {fragment.GetType().Name}")
print(f"Batches: {fragment.Batches.Count}")

# %% Cell 2: Walk the AST and print node types at each level
def dump_ast(node, depth=0, max_depth=5):
    """Print the AST structure with node types and key properties."""
    if node is None or depth > max_depth:
        return
    indent = "  " * depth
    node_type = node.GetType().Name

    # Collect key info about this node
    info = f"{indent}{node_type}"

    # For named references, show the name
    if node_type == "NamedTableReference":
        try:
            schema_obj = node.SchemaObject
            parts = []
            if schema_obj.ServerIdentifier:
                parts.append(schema_obj.ServerIdentifier.Value)
            if schema_obj.DatabaseIdentifier:
                parts.append(schema_obj.DatabaseIdentifier.Value)
            if schema_obj.SchemaIdentifier:
                parts.append(schema_obj.SchemaIdentifier.Value)
            if schema_obj.BaseIdentifier:
                parts.append(schema_obj.BaseIdentifier.Value)
            info += f" → {'.'.join(parts)}"
            if node.Alias:
                info += f" AS {node.Alias.Value}"
        except Exception:
            pass

    elif node_type == "ColumnReferenceExpression":
        try:
            multi = node.MultiPartIdentifier
            if multi and multi.Identifiers:
                parts = [multi.Identifiers[i].Value for i in range(multi.Identifiers.Count)]
                info += f" → {'.'.join(parts)}"
        except Exception:
            pass

    elif node_type == "CommonTableExpression":
        try:
            info += f" → name={node.ExpressionName.Value}"
        except Exception:
            pass

    elif node_type == "SelectStatement":
        try:
            if node.WithCtesAndXmlNamespaces:
                cte_count = node.WithCtesAndXmlNamespaces.CommonTableExpressions.Count
                info += f" (has {cte_count} CTEs)"
        except Exception:
            pass

    elif node_type == "InsertStatement":
        try:
            spec = node.InsertSpecification
            if spec and spec.Target:
                target_type = spec.Target.GetType().Name
                info += f" → target={target_type}"
                if target_type == "NamedTableReference":
                    info += f"({spec.Target.SchemaObject.BaseIdentifier.Value})"
        except Exception:
            pass

    print(info)

    # Walk children
    try:
        for prop in node.GetType().GetProperties():
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue
                if hasattr(value, "StartLine"):
                    dump_ast(value, depth + 1, max_depth)
                elif hasattr(value, "Count"):
                    for j in range(value.Count):
                        item = value[j]
                        if hasattr(item, "StartLine"):
                            dump_ast(item, depth + 1, max_depth)
            except Exception:
                continue
    except Exception:
        pass

# Dump the first batch
batch = fragment.Batches[0]
for i in range(batch.Statements.Count):
    stmt = batch.Statements[i]
    print(f"\n=== Statement {i+1}: {stmt.GetType().Name} ===")
    dump_ast(stmt, depth=0, max_depth=6)

# %% Cell 3: Specifically explore CTE structure
print("\n=== CTE Deep Dive ===")
for i in range(batch.Statements.Count):
    stmt = batch.Statements[i]
    if stmt.GetType().Name != "SelectStatement":
        continue

    if not stmt.WithCtesAndXmlNamespaces:
        print("No CTEs in this SELECT")
        continue

    ctes = stmt.WithCtesAndXmlNamespaces.CommonTableExpressions
    print(f"Found {ctes.Count} CTEs:")

    for j in range(ctes.Count):
        cte = ctes[j]
        cte_name = cte.ExpressionName.Value
        cte_body = cte.QueryExpression

        # Get the SQL text of the CTE body
        from src.parser.scriptdom_fabric import _get_fragment_text
        cte_sql = _get_fragment_text(cte_body)

        print(f"\n  CTE {j+1}: {cte_name}")
        print(f"  Body type: {cte_body.GetType().Name}")
        print(f"  SQL preview: {cte_sql[:150]}...")

        # Find table references in this CTE
        tables = []
        columns = []
        def walk_for_refs(node, depth=0):
            if node is None or depth > 10:
                return
            nt = node.GetType().Name
            if nt == "NamedTableReference":
                try:
                    name = node.SchemaObject.BaseIdentifier.Value
                    tables.append(name)
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
                            walk_for_refs(value, depth + 1)
                        elif hasattr(value, "Count"):
                            for k in range(value.Count):
                                item = value[k]
                                if hasattr(item, "StartLine"):
                                    walk_for_refs(item, depth + 1)
                    except Exception:
                        continue
            except Exception:
                pass

        walk_for_refs(cte_body)
        print(f"  Tables: {tables}")
        print(f"  Columns (first 10): {columns[:10]}")

# %% Cell 4: Explore INSERT...SELECT INTO #temp structure
print("\n=== INSERT/SELECT INTO Deep Dive ===")
for i in range(batch.Statements.Count):
    stmt = batch.Statements[i]
    stmt_type = stmt.GetType().Name

    if stmt_type == "InsertStatement":
        spec = stmt.InsertSpecification
        target = spec.Target
        print(f"\nINSERT target: {target.GetType().Name}")
        if target.GetType().Name == "NamedTableReference":
            print(f"  Table: {target.SchemaObject.BaseIdentifier.Value}")

        source = spec.InsertSource
        print(f"  Source type: {source.GetType().Name}")
        if source.GetType().Name == "SelectInsertSource":
            query = source.Select
            print(f"  Query type: {query.GetType().Name}")

            # Find tables in the SELECT source
            tables = []
            def walk_tables(node, depth=0):
                if node is None or depth > 10:
                    return
                if node.GetType().Name == "NamedTableReference":
                    try:
                        tables.append(node.SchemaObject.BaseIdentifier.Value)
                    except Exception:
                        pass
                try:
                    for prop in node.GetType().GetProperties():
                        try:
                            value = prop.GetValue(node)
                            if value is None:
                                continue
                            if hasattr(value, "StartLine"):
                                walk_tables(value, depth + 1)
                            elif hasattr(value, "Count"):
                                for k in range(value.Count):
                                    item = value[k]
                                    if hasattr(item, "StartLine"):
                                        walk_tables(item, depth + 1)
                        except Exception:
                            continue
                except Exception:
                    pass

            walk_tables(query)
            print(f"  Tables in SELECT: {tables}")

# %% Cell 5: Explore final SELECT (after CTEs)
print("\n=== Final SELECT Deep Dive ===")
for i in range(batch.Statements.Count):
    stmt = batch.Statements[i]
    if stmt.GetType().Name != "SelectStatement":
        continue

    # The QueryExpression is the final SELECT (after WITH...CTEs)
    query = stmt.QueryExpression
    print(f"Final query type: {query.GetType().Name}")

    tables = []
    columns = []
    def walk_final(node, depth=0):
        if node is None or depth > 10:
            return
        nt = node.GetType().Name
        if nt == "NamedTableReference":
            try:
                name = node.SchemaObject.BaseIdentifier.Value
                alias = node.Alias.Value if node.Alias else None
                tables.append((name, alias))
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
                        walk_final(value, depth + 1)
                    elif hasattr(value, "Count"):
                        for k in range(value.Count):
                            item = value[k]
                            if hasattr(item, "StartLine"):
                                walk_final(item, depth + 1)
                except Exception:
                    continue
        except Exception:
            pass

    walk_final(query)
    print(f"Tables: {tables}")
    print(f"Columns (first 15): {columns[:15]}")
