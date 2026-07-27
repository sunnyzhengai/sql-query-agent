"""Fabric Notebook: Extract and Parse SQL Sources

Reads from: sql_sources (Delta table)
Writes to:  parse_results, parse_errors, parse_successes (Delta tables)

parse_results stores the full parsed output (CTEs as JSON) so
03_build_graph.py can rebuild the graph without re-parsing.
"""

# %% Cell 0: Setup
# Prerequisites: Attach 'aivia-env' Fabric Environment. DO NOT use %pip install.
import json
import sys
import os

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

import src
print(f"AIVIA v{src.__version__}")

# Load pythonnet + ScriptDom directly (do not call load_scriptdom — it re-triggers init)
from pythonnet import load
try:
    load("coreclr")
except Exception:
    pass

import clr
from System.Reflection import Assembly
Assembly.LoadFrom("/lakehouse/default/Files/sql-query-agent/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll")
from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
from System.IO import StringReader
print("ScriptDom loaded!")

# Import helper functions from scriptdom_fabric (but NOT load_scriptdom)
from src.parser.scriptdom_fabric import (
    _walk_for_selects, _walk_for_refs, _get_fragment_text,
    _get_into_target, _get_insert_target, _extract_table_ref,
)
from src.parser.sql_parser import ParsedSQL, CTEInfo, ColumnRef, TableRef, normalize_sql_whitespace
from src.config import load_config
from src.schemas import to_spark_schema
import re as _re

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
scriptdom_available = True

def extract_with_scriptdom(raw_sql):
    parser = TSql160Parser(True)
    reader = StringReader(raw_sql)
    fragment = parser.Parse(reader, None)
    fragment = fragment[0] if isinstance(fragment, tuple) else fragment
    stmts = []
    _walk_for_selects(fragment, stmts, _get_fragment_text)
    return [_re.sub(r"@(\w+)", r"__param_\1__", _get_fragment_text(s)) for s in stmts]

def parse_with_scriptdom(raw_sql):
    parser = TSql160Parser(True)
    reader = StringReader(raw_sql)
    fragment = parser.Parse(reader, None)
    fragment = fragment[0] if isinstance(fragment, tuple) else fragment
    stmts = []
    _walk_for_selects(fragment, stmts, _get_fragment_text)
    if not stmts:
        raise ValueError("ScriptDom found no SELECT statements")
    raw_entries = []
    temp_table_names = set()
    cte_names = set()
    for stmt in stmts:
        st = stmt.GetType().Name
        into_target = _get_into_target(stmt) if st == "SelectStatement" else _get_insert_target(stmt) if st == "InsertStatement" else None
        temp_name = into_target.lstrip("#") if into_target else None
        if temp_name:
            temp_table_names.add(temp_name)
            temp_table_names.add(into_target)
        if st == "SelectStatement" and stmt.WithCtesAndXmlNamespaces:
            for j in range(stmt.WithCtesAndXmlNamespaces.CommonTableExpressions.Count):
                c = stmt.WithCtesAndXmlNamespaces.CommonTableExpressions[j]
                cn = c.ExpressionName.Value
                cte_names.add(cn)
                cs = normalize_sql_whitespace(_get_fragment_text(c.QueryExpression))[:500]
                ct, cc = [], []
                _walk_for_refs(c.QueryExpression, ct, cc)
                raw_entries.append((cn, cs, ct, cc, True))
        tables, columns = [], []
        if st == "SelectStatement":
            _walk_for_refs(stmt.QueryExpression, tables, columns)
        elif st == "InsertStatement" and stmt.InsertSpecification.InsertSource:
            _walk_for_refs(stmt.InsertSpecification.InsertSource, tables, columns)
        if temp_name:
            st_sql = normalize_sql_whitespace(_get_fragment_text(stmt))[:500]
            raw_entries.append((temp_name, st_sql, tables, columns, False))
        else:
            raw_entries.append((None, "", tables, columns, False))
    stripped = {t.lstrip("#") for t in temp_table_names}
    all_ctes, all_ft, all_fcr, all_fc = [], [], [], []
    for en, sf, rt, rc, _ in raw_entries:
        cr = [ColumnRef(table=t, column=c) for t, c in rc]
        if en is not None:
            phys, deps, sp, sd = [], [], set(), set()
            for db, sch, tbl in rt:
                can = tbl.lstrip("#")
                if can == en: continue
                if can in stripped or tbl in cte_names:
                    if can not in sd: deps.append(can); sd.add(can)
                else:
                    r = TableRef(table=tbl, schema=sch, database=db)
                    if r not in sp: phys.append(r); sp.add(r)
            all_ctes.append(CTEInfo(name=en, sql_fragment=sf, column_refs=cr, table_refs=phys, depends_on=deps))
        else:
            for db, sch, tbl in rt:
                can = tbl.lstrip("#")
                if can in stripped or tbl in cte_names:
                    if can not in all_fcr: all_fcr.append(can)
                else:
                    r = TableRef(table=tbl, schema=sch, database=db)
                    if r not in all_ft: all_ft.append(r)
            all_fc.extend(cr)
    return ParsedSQL(ctes=all_ctes, final_select_tables=all_ft, final_select_cte_refs=all_fcr, final_select_columns=all_fc, normalized_sql="")

print(f"ScriptDom ready: {scriptdom_available}")

def read_source(name_or_path):
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
