"""Fabric Notebook: Extract and Parse SQL Sources

Reads from: sql_sources (Delta table)
Writes to:  parse_results, parse_errors, parse_successes (Delta tables)

parse_results stores the full parsed output (CTEs as JSON) so
03_build_graph.py can rebuild the graph without re-parsing.
"""

# %% Cell 0: Install dependencies (triggers kernel restart — nothing else here)
%pip install pydantic pyyaml sqlglot sqlparse pythonnet

# %% Cell 1: Setup (run after kernel restart — pythonnet FIRST, before any Spark)
import os
os.environ["PYTHONNET_RUNTIME"] = "coreclr"

from pythonnet import load
try:
    load("coreclr")
except Exception:
    pass  # Already initialized

import clr
import sys
dll_path = "/lakehouse/default/Files/sql-query-agent/libs"
if dll_path not in sys.path:
    sys.path.append(dll_path)
clr.AddReference(os.path.join(dll_path, "Microsoft.SqlServer.TransactSql.ScriptDom.dll"))
print("ScriptDom loaded!")

# Now safe to import everything else
import json
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.schemas import to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# Build parse_with_scriptdom directly — ScriptDom is already loaded above
import re as _re
from src.parser.scriptdom_fabric import (
    _walk_for_selects, _walk_for_refs, _get_fragment_text,
    _get_into_target, _get_insert_target, _extract_table_ref,
)
from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
from System.IO import StringReader

scriptdom_available = True

def extract_with_scriptdom(raw_sql):
    parser = TSql160Parser(True)
    reader = StringReader(raw_sql)
    parse_result = parser.Parse(reader, None)
    fragment = parse_result[0] if isinstance(parse_result, tuple) else parse_result
    stmt_nodes = []
    _walk_for_selects(fragment, stmt_nodes, _get_fragment_text)
    queries = [_get_fragment_text(n) for n in stmt_nodes]
    return [_re.sub(r"@(\w+)", r"__param_\1__", q) for q in queries]

def parse_with_scriptdom(raw_sql):
    from src.parser.sql_parser import ParsedSQL, CTEInfo, ColumnRef, TableRef, normalize_sql_whitespace
    parser = TSql160Parser(True)
    reader = StringReader(raw_sql)
    parse_result = parser.Parse(reader, None)
    fragment = parse_result[0] if isinstance(parse_result, tuple) else parse_result

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
        if into_target:
            temp_name = into_target.lstrip("#")
            temp_table_names.add(temp_name)
            temp_table_names.add(into_target)

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
                cte_cols = []
                _walk_for_refs(cte_body, cte_tables, cte_cols)
                raw_entries.append((cte_name_val, cte_sql, cte_tables, cte_cols, True))

        tables = []
        columns = []
        if stmt_type == "SelectStatement":
            _walk_for_refs(stmt.QueryExpression, tables, columns)
        elif stmt_type == "InsertStatement":
            spec = stmt.InsertSpecification
            if spec.InsertSource:
                _walk_for_refs(spec.InsertSource, tables, columns)

        if temp_name:
            sql_text = normalize_sql_whitespace(_get_fragment_text(stmt))
            if len(sql_text) > 500:
                sql_text = sql_text[:500]
            raw_entries.append((temp_name, sql_text, tables, columns, False))
        else:
            raw_entries.append((None, "", tables, columns, False))

    stripped_temps = {tn.lstrip("#") for tn in temp_table_names}
    all_ctes = []
    all_final_tables = []
    all_final_cte_refs = []
    all_final_columns = []

    for entry_name, sql_frag, raw_tables, raw_cols, is_cte_entry in raw_entries:
        col_refs = [ColumnRef(table=t, column=c) for t, c in raw_cols]
        if entry_name is not None:
            physical = []
            depends = []
            seen_p = set()
            seen_d = set()
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
                name=entry_name, sql_fragment=sql_frag, column_refs=col_refs,
                table_refs=physical, depends_on=depends,
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

    return ParsedSQL(
        ctes=all_ctes, final_select_tables=all_final_tables,
        final_select_cte_refs=all_final_cte_refs,
        final_select_columns=all_final_columns, normalized_sql="",
    )

print(f"ScriptDom ready: {scriptdom_available}")

def read_source(name_or_path):
    """Read a data source by name or path."""
    if name_or_path.endswith(".csv"):
        return spark.read.option("header", "true").option("inferSchema", "true").csv(name_or_path)
    elif "abfss://" in name_or_path or "/" in name_or_path:
        return spark.read.format("delta").load(name_or_path)
    else:
        return spark.table(name_or_path)

# %% Cell 1: Load SQL sources
sql_sources_df = read_source(config.lakehouse.sql_sources)

sql_sources_df = sql_sources_df.selectExpr(
    "metric_id",
    "name",
    "sql",
    "cast(null as string) as steward",
    "cast(null as string) as developer",
)

sql_sources = [row.asDict() for row in sql_sources_df.limit(50).collect()]  # Remove .limit(50) for full run
print(f"Loaded {len(sql_sources)} SQL sources")

# %% Cell 2: Extract and parse each SQL source
import time as _time
from src.parser.sql_parser import parse_sql
from src.parser.error_classifier import classify_parse_error

extractor_name = "ScriptDom (Option B)" if scriptdom_available else "sqlparse + sqlglot"
print(f"Parsing SQL with {extractor_name}...")

parse_errors = []
parse_successes = []
parse_results_data = []
start_time = _time.time()

for i, source in enumerate(sql_sources):
    metric_id = source["metric_id"]
    name = source["name"]
    sql = source["sql"]

    try:
        if scriptdom_available:
            # Option B: ScriptDom extracts structure directly from AST
            # No sqlglot, no cleanup rules, 100% T-SQL compatibility
            parsed = parse_with_scriptdom(sql)
        else:
            # Fallback: sqlparse extraction + sqlglot parsing
            parsed = parse_sql(sql)

        # Store parse result as JSON for downstream notebooks
        ctes_json = json.dumps([{
            "name": c.name,
            "sql_fragment": c.sql_fragment,
            "table_refs": [{"table": t.table, "schema": t.schema, "database": t.database}
                           if hasattr(t, 'schema') else {"table": t, "schema": "dbo", "database": None}
                           for t in c.table_refs],
            "depends_on": c.depends_on,
            "column_refs": [{"table": cr.table, "column": cr.column} for cr in c.column_refs],
        } for c in parsed.ctes])

        parse_results_data.append({
            "metric_id": metric_id,
            "name": name,
            "ctes_json": ctes_json,
            "final_select_tables": json.dumps([
                {"table": t.table, "schema": t.schema, "database": t.database}
                if hasattr(t, 'schema') else {"table": t, "schema": "dbo", "database": None}
                for t in parsed.final_select_tables
            ]),
            "final_select_cte_refs": json.dumps(parsed.final_select_cte_refs),
            "cte_count": len(parsed.ctes),
            "table_count": len(parsed.final_select_tables),
            "line_count": sql.count("\n") + 1,
        })

        parse_successes.append({
            "metric_id": metric_id,
            "name": name,
            "cte_count": len(parsed.ctes),
            "table_count": len(parsed.final_select_tables),
            "line_count": sql.count("\n") + 1,
        })
        print(f"  Parsed: {metric_id} — {len(parsed.ctes)} CTEs, {len(parsed.final_select_tables)} tables")

    except Exception as e:
        lc = sql.count("\n") + 1
        classification = classify_parse_error(str(e), metric_id, lc)
        parse_errors.append({
            "metric_id": metric_id,
            "name": name,
            "error": str(e)[:200],
            "error_category": classification["error_category"],
            "user_explanation": classification["user_explanation"],
            "suggested_action": classification["suggested_action"],
            "line_count": lc,
        })
        print(f"  ERROR: {metric_id} [{classification['error_category']}] {str(e)[:100]}")

    if (i + 1) % 100 == 0:
        elapsed = _time.time() - start_time
        print(f"  Progress: {i + 1}/{len(sql_sources)} ({len(parse_successes)} ok, {len(parse_errors)} errors, {elapsed:.0f}s)")

elapsed = _time.time() - start_time
print(f"\nDone in {elapsed:.0f}s")
print(f"Parsed: {len(parse_successes)}/{len(sql_sources)} ({100 * len(parse_successes) // max(len(sql_sources), 1)}%)")
print(f"Errors: {len(parse_errors)}")

# %% Cell 3: Save results to Delta tables
from src.schemas import PARSE_ERRORS, PARSE_SUCCESSES, to_spark_schema
from pyspark.sql.types import StringType, StructField, StructType, IntegerType

# Save parse results (intermediate table for 03_build_graph)
if parse_results_data:
    pr_schema = StructType([
        StructField("metric_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("ctes_json", StringType(), True),
        StructField("final_select_tables", StringType(), True),
        StructField("final_select_cte_refs", StringType(), True),
        StructField("cte_count", IntegerType(), True),
        StructField("table_count", IntegerType(), True),
        StructField("line_count", IntegerType(), True),
    ])
    pr_rows = [(r["metric_id"], r["name"], r["ctes_json"], r["final_select_tables"],
                r["final_select_cte_refs"], r["cte_count"], r["table_count"], r["line_count"])
               for r in parse_results_data]
    pr_df = spark.createDataFrame(pr_rows, schema=pr_schema)
    pr_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("parse_results")
    print(f"Saved {len(parse_results_data)} parse results to 'parse_results' table")

# Save parse errors
if parse_errors:
    errors_rows = [(e["metric_id"], e["name"], e["error"], e.get("error_category"),
                    e.get("user_explanation"), e.get("suggested_action"), e["line_count"])
                   for e in parse_errors]
    errors_df = spark.createDataFrame(errors_rows, schema=to_spark_schema(PARSE_ERRORS))
    errors_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("parse_errors")
    print(f"Saved {len(parse_errors)} parse errors to 'parse_errors' table")
    print("\nTop errors:")
    for e in sorted(parse_errors, key=lambda x: x["line_count"], reverse=True)[:5]:
        print(f"  {e['metric_id']} ({e['line_count']} lines): [{e['error_category']}] {e['error'][:80]}")

# Save parse successes
if parse_successes:
    success_rows = [(s["metric_id"], s["name"], s["cte_count"], s["table_count"], s["line_count"])
                    for s in parse_successes]
    success_df = spark.createDataFrame(success_rows, schema=to_spark_schema(PARSE_SUCCESSES))
    success_df.write.format("delta").mode("overwrite").saveAsTable("parse_successes")
    print(f"Saved {len(parse_successes)} parse successes to 'parse_successes' table")

print("\n→ Next: run 03_build_graph.py (no need to rerun this unless SQL sources changed)")
