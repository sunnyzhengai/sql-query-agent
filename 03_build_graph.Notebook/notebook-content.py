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
import sys

# If the wheel is installed via Fabric Environment, src is already importable.
# Fallback to sys.path for dev mode or non-wheel deployments.
try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.18"
from src.engine_floor import require_engine
require_engine(src.__version__, REQUIRES_ENGINE, "03_build_graph")


from src.config import load_config
from src.schemas import GRAPH_EDGES, GRAPH_NODES, to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load parse results + dictionary from Delta
from src.steps.gates import precondition_gate

# Required inputs must exist (and be non-empty where the contract says so)
# BEFORE work starts — a missing table fails with a message naming the
# producing notebook, not a pyspark stack trace. Registry-driven; see
# src/steps/gates.py.
precondition_gate("03_build_graph", table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count())


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

# Optional enrichments: ABSENCE of the table is a legitimate state (not yet
# assigned); a FAILED read is not — it must raise, or a transient error
# silently rebuilds the graph with zero stewards (audit 2026-08-15).
metric_name_records = []
if spark.catalog.tableExists("input_metric_names"):
    metric_name_records = [r.asDict() for r in spark.table("input_metric_names").collect()]
else:
    print("No input_metric_names table — metrics display object names only")

steward_records = []
if spark.catalog.tableExists("gov_steward_assignments"):
    steward_records = [r.asDict() for r in spark.table("gov_steward_assignments").collect()]
else:
    print("No gov_steward_assignments table — run notebooks/utilities/manage_stewards to assign")

# Consumption layer (ADR 0040): PBI report lineage + DAX, written by 12
report_source_records = []
if spark.catalog.tableExists("input_report_sources"):
    report_source_records = [r.asDict() for r in spark.table("input_report_sources").collect()]
else:
    print("No input_report_sources table — run 12_ingest_semantic_models for report lineage")

dax_records = []
if spark.catalog.tableExists("input_dax_expressions"):
    dax_records = [r.asDict() for r in spark.table("input_dax_expressions").collect()]
else:
    print("No input_dax_expressions table — run 12_ingest_semantic_models for DAX measures")

out = build_graph_step(
    parse_results, dict_tables_rows, dict_columns_rows, steward_records,
    metric_name_records=metric_name_records,
    report_source_records=report_source_records,
    dax_records=dax_records,
    table_name_col=config.dictionary.table_name_col,
    column_name_col=config.dictionary.column_name_col,
    description_col=config.dictionary.description_col,
    table_description_col=config.dictionary.table_description_col,
)
print(f"Built graph: {out.node_count} nodes, {out.edge_count} edges")
if steward_records:
    print(f"Applied {out.stewards_applied} steward assignments to canonical nodes")
if metric_name_records:
    print(f"Applied {out.business_names_applied} business-friendly names")
    for issue in out.business_names_skipped:
        print(f"  [!] name skipped: {issue}")
if report_source_records or dax_records:
    print(f"Consumption layer: {out.reports_added} reports, {out.measures_added} measures")
    for issue in out.consumption_skipped[:10]:
        print(f"  [!] lineage skipped: {issue}")


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

nodes_df.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(config.lakehouse.graph_nodes)
edges_df.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(config.lakehouse.graph_edges)

print(f"Wrote {nodes_df.count()} nodes, {edges_df.count()} edges")

# Record setup completeness: proceeding without an optional enrichment is
# legitimate but DEGRADED (e.g. zero stewards) — queryable state, not just
# a printed line (ADR 0039 amendment / handoff item 3).
from datetime import datetime, timezone

from src.schemas import SETUP_COMPLETENESS
from src.steps.gates import setup_completeness_rows

completeness = setup_completeness_rows(
    "03_build_graph", table_exists=spark.catalog.tableExists,
    run_at=datetime.now(timezone.utc).isoformat(),
)
completeness_df = spark.createDataFrame(
    completeness, schema=to_spark_schema(SETUP_COMPLETENESS))
if spark.catalog.tableExists("ops_setup_completeness"):
    completeness_df.write.format("delta").mode("append").saveAsTable("ops_setup_completeness")
else:
    completeness_df.write.format("delta").saveAsTable("ops_setup_completeness")
for row in completeness:
    state = "present" if row["present"] else f"ABSENT — {row['remediation']}"
    print(f"[{'+' if row['present'] else '!'}] optional input {row['table_name']}: {state}")

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
