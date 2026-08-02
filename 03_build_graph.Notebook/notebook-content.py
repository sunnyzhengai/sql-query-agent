# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "f7c297eb-4659-4600-ab89-0e860638fb6c",
# META       "default_lakehouse_name": "sql_query_lh",
# META       "default_lakehouse_workspace_id": "1f55e1c1-b660-4715-9b56-4140edce3940",
# META       "known_lakehouses": [
# META         {
# META           "id": "f7c297eb-4659-4600-ab89-0e860638fb6c"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "0776fc8d-1451-838d-47e6-f5c7a0bd174b",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# CELL ********************

"""Fabric Notebook: Build Knowledge Graph

Reads from: ops_parse_results, input_dict_tables, input_dict_columns (Delta)
Writes to:  graph_nodes, graph_edges (Delta)

Run 02_parse.py at least once before this.
"""

# %% Cell 0: Setup
# Prerequisites: Attach 'sql-logic-env' Fabric Environment. No %pip install.
import json
import sys
# If the wheel is installed via Fabric Environment, src is already importable.
# Fallback to sys.path for dev mode or non-wheel deployments.
try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from src.config import load_config
from src.schemas import GRAPH_NODES, GRAPH_EDGES, to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load parse results + dictionary from Delta
parse_results = [r.asDict() for r in spark.table("ops_parse_results").collect()]

dict_tables_rows = [r.asDict() for r in spark.table(config.lakehouse.dict_tables).collect()]
dict_columns_rows = [r.asDict() for r in spark.table(config.lakehouse.dict_columns).collect()]

print(f"Loaded {len(parse_results)} parse results, {len(dict_tables_rows)} tables, {len(dict_columns_rows)} columns")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Build graph (all logic in src/steps/build_graph.py)
from src.steps.build_graph import build_graph_step

steward_records = []
try:
    steward_records = [r.asDict() for r in spark.table("gov_steward_assignments").collect()]
except Exception:
    print("No gov_steward_assignments table — run notebooks/utilities/manage_stewards to assign")

out = build_graph_step(
    parse_results, dict_tables_rows, dict_columns_rows, steward_records,
    table_name_col=config.dictionary.table_name_col,
    column_name_col=config.dictionary.column_name_col,
    description_col=config.dictionary.description_col,
    table_description_col=config.dictionary.table_description_col,
)
print(f"Built graph: {out.node_count} nodes, {out.edge_count} edges")
if steward_records:
    print(f"Applied {out.stewards_applied} steward assignments to canonical nodes")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Write to Delta and run the postcondition gate
from src.steps.gates import postcondition_gate

nodes_df = spark.createDataFrame(out.nodes_rows, schema=to_spark_schema(GRAPH_NODES))
edges_df = spark.createDataFrame(out.edges_rows, schema=to_spark_schema(GRAPH_EDGES))

nodes_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(config.lakehouse.graph_nodes)
edges_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(config.lakehouse.graph_edges)

print(f"Wrote {nodes_df.count()} nodes, {edges_df.count()} edges")

checked = postcondition_gate(
    "03_build_graph",
    fetch=lambda t, cols: [r.asDict() for r in spark.table(t).select(*cols).collect()],
    table_exists=spark.catalog.tableExists,
)
print(f"[+] Postcondition gate passed for: {', '.join(checked)}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 4: Quick traversal test
from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.graph.traversal import GraphTraverser

traverser = GraphTraverser(rows_to_nodes(out.nodes_rows), rows_to_edges(out.edges_rows))
for pr in parse_results[:3]:
    subgraph = traverser.get_metric_subgraph(pr["metric_id"])
    if subgraph:
        tables = [t.name for t in subgraph["technical"] if t.properties.get("column") is None]
        print(f"  {subgraph['canonical'].name}: {len(subgraph['transformations'])} transforms, {len(tables)} tables")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
