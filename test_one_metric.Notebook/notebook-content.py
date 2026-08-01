# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

# Test one metric end-to-end: parse → graph → metric_logic
# Run this to diagnose why a proc has no calculation_logic

import os, json
try:
    import src
except ImportError:
    import sys
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src

from src.parser.scriptdom_fabric import parse_from_fragment
from src.graph.builder import GraphBuilder
from src.graph.metric_logic import build_metric_logic_rows

# Load pythonnet + ScriptDom
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

# --- Pick the file to test ---
sql_path = "/lakehouse/default/Files/sql-query-agent/sql_input/USP_IP_Sepsis_Details.sql"

with open(sql_path, encoding="utf-8-sig") as f:
    sql = f.read()
print(f"Loaded {len(sql)} chars from {os.path.basename(sql_path)}")

# Step 1: ScriptDom parse
parser = TSql160Parser(True)
reader = StringReader(sql)
result = parser.Parse(reader, None)
fragment = result[0] if isinstance(result, tuple) else result

parsed = parse_from_fragment(fragment)

print(f"\n=== PARSE RESULTS ===")
print(f"CTEs: {len(parsed.ctes)}")
print(f"Final tables: {[t.table for t in parsed.final_select_tables]}")
print(f"Final CTE refs: {parsed.final_select_cte_refs}")
print(f"Normalized SQL length: {len(parsed.normalized_sql)}")
if parsed.normalized_sql:
    print(f"Normalized SQL preview: {parsed.normalized_sql[:300]}")
else:
    print("Normalized SQL: EMPTY <-- PROBLEM: parser didn't capture final SELECT text")

# Step 2: Build graph
builder = GraphBuilder()
builder.add_technical_node("IP_SEPSIS", description="Sepsis staging table")
metric_id = "reporting.USP_IP_Sepsis_Details"
builder.add_canonical_node(metric_id, "USP_IP_Sepsis_Details")
builder.build_from_parsed_sql(metric_id, parsed)

print(f"\n=== GRAPH ===")
print(f"Nodes: {len(builder.nodes)}")
for nid, n in builder.nodes.items():
    frag = n.properties.get("sql_fragment", "")
    print(f"  {nid}: fragment={'YES (' + str(len(frag)) + ' chars)' if frag else 'EMPTY'}")

print(f"Edges: {len(builder.edges)}")
for e in builder.edges:
    print(f"  {e.source_id} -> {e.target_id} ({e.edge_type.value})")

# Step 3: Build metric logic
rows = build_metric_logic_rows(builder.nodes, builder.edges)
print(f"\n=== METRIC LOGIC ===")
for r in rows:
    has_logic = r[6] is not None
    print(f"metric_id={r[0]}, has_logic={has_logic}, tables={r[7]}")
    if r[6]:
        print(f"Logic preview: {r[6][:300]}...")
    else:
        print("Logic: NULL <-- THIS IS THE BUG")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
