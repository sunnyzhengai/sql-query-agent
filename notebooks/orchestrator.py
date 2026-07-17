"""Fabric Notebook orchestrator.

In Fabric, this would be a .ipynb notebook. Kept as .py for version control.
The Fabric Notebook is the orchestrator only — the library does the heavy lifting.

To use in Fabric:
1. Create a new Notebook in your workspace
2. Copy each cell below into the notebook (cells are delimited by # %%)
3. Attach to your Lakehouse
4. Run all cells
"""

# %% Cell 1: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.pipeline import build_graph

# %% Cell 2: Load config
config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
print(f"Loaded config for: {config.org.name}")

# %% Cell 3: Load data dictionary from Delta tables
# Use spark.table() for managed tables (e.g. "dict_tables")
# Use spark.read.format("delta").load() for path-based tables (e.g. "Tables/dict_tables")
def read_table(name):
    if "/" in name:
        return spark.read.format("delta").load(name)  # noqa: F821
    return spark.table(name)  # noqa: F821

dict_tables_df = read_table(config.lakehouse.dict_tables)
dict_columns_df = read_table(config.lakehouse.dict_columns)

# Convert to list-of-dicts for the pipeline
dict_tables = [row.asDict() for row in dict_tables_df.collect()]
dict_columns = [row.asDict() for row in dict_columns_df.collect()]

print(f"Loaded {len(dict_tables)} tables, {len(dict_columns)} columns from dictionary")

# %% Cell 4: Load SQL sources
sql_sources_df = read_table(config.lakehouse.sql_sources)
sql_sources = [row.asDict() for row in sql_sources_df.collect()]

print(f"Loaded {len(sql_sources)} SQL sources")

# %% Cell 5: Build graph
builder = build_graph(
    dict_tables,
    dict_columns,
    sql_sources,
    table_name_col=config.dictionary.table_name_col,
    column_name_col=config.dictionary.column_name_col,
    description_col=config.dictionary.description_col,
)

print(f"Built graph: {len(builder.nodes)} nodes, {len(builder.edges)} edges")

# %% Cell 6: Write graph to Delta tables
from pyspark.sql.types import StringType, StructField, StructType  # noqa: E402

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

nodes_df = spark.createDataFrame(nodes_rows, schema=nodes_schema)  # noqa: F821
edges_df = spark.createDataFrame(edges_rows, schema=edges_schema)  # noqa: F821

def write_table(df, name):
    if "/" in name:
        df.write.format("delta").mode("overwrite").save(name)
    else:
        df.write.format("delta").mode("overwrite").saveAsTable(name)

write_table(nodes_df, config.lakehouse.graph_nodes)
write_table(edges_df, config.lakehouse.graph_edges)

print(f"Wrote {nodes_df.count()} nodes to {config.lakehouse.graph_nodes}")
print(f"Wrote {edges_df.count()} edges to {config.lakehouse.graph_edges}")

# %% Cell 7: Summary
from collections import Counter  # noqa: E402

layer_counts = Counter(n.layer.value for n in builder.nodes.values())
edge_type_counts = Counter(e.edge_type.value for e in builder.edges)

print("\n=== Graph Summary ===")
print(f"Nodes by layer:")
for layer, count in sorted(layer_counts.items()):
    print(f"  {layer}: {count}")
print(f"Edges by type:")
for etype, count in sorted(edge_type_counts.items()):
    print(f"  {etype}: {count}")
