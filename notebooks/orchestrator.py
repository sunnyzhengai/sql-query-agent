"""Fabric Notebook orchestrator v2.

Updated for real-world setup:
- Reads dictionary from CSV files (cross-workspace ABFS or local)
- Handles SQL sources from sql_sources Delta table or manual load
- Writes graph to Delta tables in the current lakehouse
- Includes dependency installation cell

To use in Fabric:
1. Create a new Notebook in your workspace
2. Copy each cell below into the notebook (cells are delimited by # %%)
3. Attach to your Lakehouse
4. Run all cells in order
"""

# %% Cell 1: Install dependencies
# Run this cell once per session. Fabric doesn't have these pre-installed.
%pip install pydantic pyyaml sqlglot sqlparse

# %% Cell 2: Setup
import json
import sys

# Point to the sql-query-agent library in your Lakehouse Files
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.parser.sql_parser import parse_sql
from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.dictionary import DataDictionary

# %% Cell 3: Load config
config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
print(f"Loaded config for: {config.org.name}")

# %% Cell 3b: Import SQL extractor
from src.parser.sql_extractor import extract_select_statements
print("SQL extractor ready (sqlparse-based, deterministic)")

# %% Cell 4: Load data dictionary
# Supports: managed tables, Delta paths, ABFS cross-workspace paths, and CSV files.
def read_source(name_or_path):
    """Read a data source by name or path. Auto-detects format."""
    if name_or_path.endswith(".csv"):
        # CSV file — read with header inference
        return spark.read.option("header", "true").option("inferSchema", "true").csv(name_or_path)
    elif "abfss://" in name_or_path or "/" in name_or_path:
        # Path-based Delta table (local or cross-workspace ABFS)
        return spark.read.format("delta").load(name_or_path)
    else:
        # Managed table name
        return spark.table(name_or_path)

dict_tables_df = read_source(config.lakehouse.dict_tables)
dict_columns_df = read_source(config.lakehouse.dict_columns)

# If dict_columns uses TABLE_ID instead of TABLE_NAME, join to resolve names
table_id_col = config.dictionary.table_id_col
if table_id_col:
    print(f"Joining dict_columns on {table_id_col} to resolve table names...")
    table_name_col = config.dictionary.table_name_col
    # Build a lookup: TABLE_ID -> TABLE_NAME from dict_tables
    tbl_lookup = dict_tables_df.select(table_id_col, table_name_col)
    # Join to add TABLE_NAME to dict_columns
    dict_columns_df = (
        dict_columns_df
        .join(tbl_lookup, on=table_id_col, how="left")
    )

# Convert to list-of-dicts for the pipeline
dict_tables = [row.asDict() for row in dict_tables_df.collect()]
dict_columns = [row.asDict() for row in dict_columns_df.collect()]

print(f"Loaded {len(dict_tables)} tables, {len(dict_columns)} columns from dictionary")
print(f"Table columns: {list(dict_tables[0].keys()) if dict_tables else 'empty'}")
print(f"Column columns: {list(dict_columns[0].keys()) if dict_columns else 'empty'}")

# %% Cell 5: Load SQL sources
sql_sources_df = read_source(config.lakehouse.sql_sources)
sql_sources = [row.asDict() for row in sql_sources_df.collect()]

print(f"Loaded {len(sql_sources)} SQL sources")
if sql_sources:
    print(f"SQL source keys: {list(sql_sources[0].keys())}")

# %% Cell 6: Build graph
builder = GraphBuilder()

# Step 1: Load data dictionary into technical nodes
dictionary = DataDictionary()
table_name_col = config.dictionary.table_name_col
column_name_col = config.dictionary.column_name_col
description_col = config.dictionary.description_col
table_description_col = config.dictionary.table_description_col

for row in dict_tables:
    dictionary.add_table(row[table_name_col], row.get(table_description_col, ""))
for row in dict_columns:
    dictionary.add_column(row[table_name_col], row[column_name_col], row.get(description_col, ""))

for table_name, table_info in dictionary.tables.items():
    builder.add_technical_node(table_name, description=table_info.description)
    for col_info in dictionary.get_columns_for_table(table_name):
        builder.add_technical_node(table_name, col_info.column_name, description=col_info.description)

print(f"Created {len(builder.nodes)} technical nodes from dictionary")

# Step 2: Extract clean SQL and parse into graph
# Uses sqlparse to extract SELECT/WITH statements (deterministic, instant, free)
# then sqlglot to parse the structure.
print("Step 2: Extracting and parsing SQL...")
parse_errors = []
parse_successes = []

for i, source in enumerate(sql_sources):
    metric_id = source["metric_id"]
    name = source["name"]
    sql = source["sql"]
    steward = source.get("steward")
    developer = source.get("developer")

    builder.add_canonical_node(metric_id, name, steward=steward, developer=developer)

    try:
        # Extract clean SQL using sqlparse
        clean_sql = extract_select_statements(sql)
        # Parse the clean SQL using sqlglot
        parsed = parse_sql(clean_sql)
        builder.build_from_parsed_sql(metric_id, parsed)
        parse_successes.append({
            "metric_id": metric_id,
            "name": name,
            "cte_count": len(parsed.ctes),
            "table_count": len(parsed.final_select_tables),
            "line_count": sql.count("\n") + 1,
        })
        print(f"  Parsed: {metric_id} ({name}) — {len(parsed.ctes)} CTEs, {len(parsed.final_select_tables)} tables")
    except Exception as e:
        parse_errors.append({
            "metric_id": metric_id,
            "name": name,
            "error": str(e)[:200],
            "line_count": sql.count("\n") + 1,
        })
        print(f"  ERROR parsing {metric_id}: {e}")

    if (i + 1) % 100 == 0:
        print(f"  Progress: {i + 1}/{len(sql_sources)} ({len(parse_successes)} ok, {len(parse_errors)} errors)")

print(f"\nBuilt graph: {len(builder.nodes)} nodes, {len(builder.edges)} edges")
print(f"Parsed: {len(parse_successes)}/{len(sql_sources)} ({100 * len(parse_successes) // len(sql_sources)}%)")
print(f"Errors: {len(parse_errors)}")

# %% Cell 6b: Save parse errors for HITL review
# Developers are notified to manually review/fix these failed SQL sources.
from pyspark.sql.types import StringType, StructField, StructType, IntegerType

if parse_errors:
    errors_schema = StructType([
        StructField("metric_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("error", StringType(), True),
        StructField("line_count", IntegerType(), True),
    ])
    errors_rows = [(e["metric_id"], e["name"], e["error"], e["line_count"]) for e in parse_errors]
    errors_df = spark.createDataFrame(errors_rows, schema=errors_schema)
    errors_df.write.format("delta").mode("overwrite").saveAsTable("parse_errors")
    print(f"Saved {len(parse_errors)} parse errors to 'parse_errors' table")
    print("→ Developers: review this table and fix the source SQL for these procs")
    print("\nTop errors by line count (largest procs):")
    for e in sorted(parse_errors, key=lambda x: x["line_count"], reverse=True)[:5]:
        print(f"  {e['metric_id']} ({e['line_count']} lines): {e['error'][:80]}")

# Save parse successes for validation
if parse_successes:
    success_schema = StructType([
        StructField("metric_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("cte_count", IntegerType(), True),
        StructField("table_count", IntegerType(), True),
        StructField("line_count", IntegerType(), True),
    ])
    success_rows = [(s["metric_id"], s["name"], s["cte_count"], s["table_count"], s["line_count"])
                    for s in parse_successes]
    success_df = spark.createDataFrame(success_rows, schema=success_schema)
    success_df.write.format("delta").mode("overwrite").saveAsTable("parse_successes")
    print(f"Saved {len(parse_successes)} parse successes to 'parse_successes' table")

# %% Cell 7: Write graph to Delta tables
from pyspark.sql.types import StringType, StructField, StructType

nodes_schema = StructType([
    StructField("node_id", StringType(), False),
    StructField("layer", StringType(), False),
    StructField("name", StringType(), False),
    StructField("description", StringType(), True),
    StructField("properties", StringType(), True),
])

edges_schema = StructType([
    StructField("source_id", StringType(), False),
    StructField("target_id", StringType(), False),
    StructField("edge_type", StringType(), False),
    StructField("properties", StringType(), True),
])

nodes_rows = [
    (n.node_id, n.layer.value, n.name, n.description, json.dumps(n.properties))
    for n in builder.nodes.values()
]

edges_rows = [
    (e.source_id, e.target_id, e.edge_type.value, json.dumps(e.properties))
    for e in builder.edges
]

nodes_df = spark.createDataFrame(nodes_rows, schema=nodes_schema)
edges_df = spark.createDataFrame(edges_rows, schema=edges_schema)

def write_table(df, name):
    if "/" in name:
        df.write.format("delta").mode("overwrite").save(name)
    else:
        df.write.format("delta").mode("overwrite").saveAsTable(name)

write_table(nodes_df, config.lakehouse.graph_nodes)
write_table(edges_df, config.lakehouse.graph_edges)

print(f"Wrote {nodes_df.count()} nodes to {config.lakehouse.graph_nodes}")
print(f"Wrote {edges_df.count()} edges to {config.lakehouse.graph_edges}")

# %% Cell 8: Test traversal
traverser = GraphTraverser(builder.nodes, builder.edges)

print("\n=== Traversal Test ===")
for source in sql_sources[:5]:  # test first 5
    metric_id = source["metric_id"]
    subgraph = traverser.get_metric_subgraph(metric_id)
    if subgraph:
        canonical = subgraph["canonical"]
        tables = [t.name for t in subgraph["technical"] if t.properties.get("column") is None]
        print(f"\n{canonical.name} ({metric_id})")
        print(f"  Steward: {canonical.properties.get('steward', 'N/A')}")
        print(f"  Transforms: {len(subgraph['transformations'])}")
        print(f"  Tables: {len(tables)} — {tables[:5]}{'...' if len(tables) > 5 else ''}")
    else:
        print(f"\n{metric_id} — no graph path found")

# %% Cell 9: Save build summary to Delta table
from collections import Counter
from datetime import datetime, timezone

layer_counts = Counter(n.layer.value for n in builder.nodes.values())
edge_type_counts = Counter(e.edge_type.value for e in builder.edges)

now = datetime.now(timezone.utc).isoformat()

summary_rows = []

# Overall stats
summary_rows.append((now, "total_nodes", str(len(builder.nodes)), ""))
summary_rows.append((now, "total_edges", str(len(builder.edges)), ""))
summary_rows.append((now, "total_metrics", str(len(sql_sources)), ""))
summary_rows.append((now, "parse_errors", str(len(parse_errors)), ""))

# Nodes by layer
for layer, count in sorted(layer_counts.items()):
    summary_rows.append((now, f"nodes_{layer}", str(count), ""))

# Edges by type
for etype, count in sorted(edge_type_counts.items()):
    summary_rows.append((now, f"edges_{etype}", str(count), ""))

# Per-metric summary
traverser_summary = GraphTraverser(builder.nodes, builder.edges)
for source in sql_sources:
    metric_id = source["metric_id"]
    subgraph = traverser_summary.get_metric_subgraph(metric_id)
    if subgraph:
        tables = [t.name for t in subgraph["technical"] if t.properties.get("column") is None]
        summary_rows.append((now, f"metric_{metric_id}", str(len(tables)),
                            f"transforms={len(subgraph['transformations'])}, tables={len(tables)}"))

# Parse errors
for mid, err in parse_errors:
    summary_rows.append((now, f"error_{mid}", "parse_failed", err[:200]))

from pyspark.sql.types import StringType, StructField, StructType

summary_schema = StructType([
    StructField("build_time", StringType(), False),
    StructField("metric_key", StringType(), False),
    StructField("value", StringType(), False),
    StructField("detail", StringType(), True),
])

summary_df = spark.createDataFrame(summary_rows, schema=summary_schema)

# Append to build_summary (keep history of each run)
try:
    existing = spark.table("build_summary")
    summary_df.write.format("delta").mode("append").saveAsTable("build_summary")
except Exception:
    summary_df.write.format("delta").mode("overwrite").saveAsTable("build_summary")

print(f"Saved {len(summary_rows)} summary records to build_summary")

# %% Cell 10: Print summary
print("\n=== Graph Summary ===")
print(f"Total nodes: {len(builder.nodes)}")
print(f"Nodes by layer:")
for layer, count in sorted(layer_counts.items()):
    print(f"  {layer}: {count}")
print(f"Total edges: {len(builder.edges)}")
print(f"Edges by type:")
for etype, count in sorted(edge_type_counts.items()):
    print(f"  {etype}: {count}")
if parse_errors:
    print(f"\nParse errors: {len(parse_errors)} (see Cell 6 output)")
print(f"\nOutput tables:")
print(f"  {config.lakehouse.graph_nodes} — nodes for Data Agent")
print(f"  {config.lakehouse.graph_edges} — edges for Data Agent")
print(f"  build_summary — build history (append-only)")
print(f"\nNext step: Point your Fabric Data Agent at '{config.lakehouse.graph_nodes}' "
      f"and '{config.lakehouse.graph_edges}'")
