"""Fabric Notebook: Test ScriptDom directly in Fabric via pythonnet

Uses Microsoft's ScriptDom parser INSIDE the Fabric notebook — no
external microservice needed. The DLL runs natively on the Fabric
Spark pool's .NET runtime via pythonnet.

Prerequisites:
1. Download Microsoft.SqlServer.TransactSql.ScriptDom NuGet package
2. Extract the .dll from the package (rename .nupkg to .zip, find lib/net6.0/)
3. Upload Microsoft.SqlServer.TransactSql.ScriptDom.dll to
   Lakehouse Files/libs/
"""

# %% Cell 1: Install pythonnet
%pip install pythonnet

# %% Cell 2: Load ScriptDom DLL
# Must load CoreCLR before importing clr (Fabric Linux uses .NET Core, not Mono)
from pythonnet import load
load("coreclr")

import clr
import sys

# Point to the DLL location in your Lakehouse
dll_path = "/lakehouse/default/Files/libs"
if dll_path not in sys.path:
    sys.path.append(dll_path)

# Load Microsoft's ScriptDom
clr.AddReference("Microsoft.SqlServer.TransactSql.ScriptDom")

from Microsoft.SqlServer.TransactSql.ScriptDom import (
    TSql160Parser,
    TSqlFragmentVisitor,
    SelectStatement,
    InsertStatement,
    SelectInsertSource,
)
from System.IO import StringReader

print("ScriptDom loaded successfully!")

# %% Cell 3: Build the extractor (manual AST walk, no visitor subclass)

def extract_with_scriptdom(raw_sql):
    """Parse T-SQL with ScriptDom and extract SELECT statements."""
    parser = TSql160Parser(True)
    reader = StringReader(raw_sql)
    parse_result = parser.Parse(reader, None)

    # pythonnet may return a tuple (fragment, errors) or just the fragment
    if isinstance(parse_result, tuple):
        fragment = parse_result[0]
    else:
        fragment = parse_result

    queries = []
    _walk_for_selects(fragment, queries)
    return queries


def _walk_for_selects(node, queries):
    """Recursively walk the AST and collect SELECT/INSERT...SELECT nodes."""
    if node is None:
        return

    node_type = node.GetType().Name

    if node_type == "SelectStatement":
        sql = _get_fragment_text(node)
        if sql:
            queries.append({
                "type": "SELECT",
                "start_line": node.StartLine,
                "sql": sql,
            })
        return  # Don't walk into children (subqueries are part of this SQL)

    if node_type == "InsertStatement":
        spec = node.InsertSpecification
        if spec and spec.InsertSource and spec.InsertSource.GetType().Name == "SelectInsertSource":
            sql = _get_fragment_text(node)
            if sql:
                queries.append({
                    "type": "INSERT_SELECT",
                    "start_line": node.StartLine,
                    "sql": sql,
                })
            return

    # Walk children using reflection
    try:
        for prop in node.GetType().GetProperties():
            try:
                value = prop.GetValue(node)
                if value is None:
                    continue

                # If it's a TSqlFragment, recurse
                if hasattr(value, "StartLine"):
                    _walk_for_selects(value, queries)

                # If it's a collection, iterate
                elif hasattr(value, "Count"):
                    for j in range(value.Count):
                        item = value[j]
                        if hasattr(item, "StartLine"):
                            _walk_for_selects(item, queries)
            except Exception:
                continue
    except Exception:
        pass


def _get_fragment_text(fragment):
    """Extract original SQL text from the token stream."""
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


print("Extractor ready!")

# %% Cell 4: Test with a simple query
test_sql = """
CREATE PROCEDURE [dbo].[TestProc]
    @StartDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @x DATE = GETDATE();

    SELECT col1, col2
    FROM my_table
    WHERE date_col >= @x;
END
"""

queries = extract_with_scriptdom(test_sql)
print(f"Queries found: {len(queries)}")
for q in queries:
    print(f"  [{q['type']}] line {q['start_line']}: {q['sql'][:80]}...")

# %% Cell 5: Test with real SQL sources
# Load one proc from sql_sources and test
sql_sources_df = spark.table("sql_sources")
first_row = sql_sources_df.limit(1).collect()[0]
raw_sql = first_row["sql"]
metric_id = first_row["metric_id"]

print(f"Testing: {metric_id} ({len(raw_sql)} chars)")
queries = extract_with_scriptdom(raw_sql)
print(f"Queries found: {len(queries)}")
for q in queries[:5]:
    print(f"  [{q['type']}] line {q['start_line']}: {q['sql'][:80]}...")
if len(queries) > 5:
    print(f"  ... and {len(queries) - 5} more")

# %% Cell 6: Run ScriptDom on ALL sql_sources
import time

sql_sources = [row.asDict() for row in sql_sources_df.collect()]
print(f"Processing {len(sql_sources)} SQL sources with ScriptDom...\n")

results = []
start_time = time.time()

for i, source in enumerate(sql_sources):
    metric_id = source["metric_id"]
    raw_sql = source["sql"]

    try:
        queries = extract_with_scriptdom(raw_sql)
        results.append({
            "metric_id": metric_id,
            "query_count": len(queries),
            "success": True,
            "error": "",
        })
    except Exception as e:
        results.append({
            "metric_id": metric_id,
            "query_count": 0,
            "success": False,
            "error": str(e)[:200],
        })

    if (i + 1) % 100 == 0:
        elapsed = time.time() - start_time
        ok = sum(1 for r in results if r["success"])
        print(f"  {i+1}/{len(sql_sources)} ({ok} ok, {elapsed:.0f}s)")

elapsed = time.time() - start_time
total_queries = sum(r["query_count"] for r in results)
succeeded = sum(1 for r in results if r["success"] and r["query_count"] > 0)
failed = sum(1 for r in results if not r["success"])
no_queries = sum(1 for r in results if r["success"] and r["query_count"] == 0)

print(f"\n=== ScriptDom Results ===")
print(f"Total procs: {len(sql_sources)}")
print(f"Extracted queries: {succeeded} procs ({total_queries} total queries)")
print(f"No queries found: {no_queries}")
print(f"Parse errors: {failed}")
print(f"Time: {elapsed:.0f}s ({elapsed/len(sql_sources):.1f}s per proc)")
print(f"Success rate: {100 * succeeded // len(sql_sources)}%")

# %% Cell 7: Show failures (if any)
failures = [r for r in results if not r["success"]]
if failures:
    print(f"\n=== {len(failures)} Failures ===")
    for r in failures[:10]:
        print(f"  {r['metric_id']}: {r['error'][:100]}")
else:
    print("\nNo failures! ScriptDom parsed everything.")
