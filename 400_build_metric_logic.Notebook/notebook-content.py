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

"""Fabric Notebook: Build Metric Logic Table

Reads from: graph_nodes, graph_edges (Delta)
Writes to:  output_metric_logic (Delta)

Run 300_build_graph.py at least once before this.
Flattens the graph into a single table the Data Agent can query.
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
REQUIRES_ENGINE = "1.22"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "400_build_metric_logic")


from src.config import load_config
from src.schemas import METRIC_LOGIC, to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load graph and build metric_logic (logic in src/steps/metric_logic.py)
from src.steps.gates import precondition_gate

# Required inputs must exist (and be non-empty where the contract says so)
# BEFORE work starts — a missing table fails with a message naming the
# producing notebook, not a pyspark stack trace. Registry-driven; see
# src/steps/gates.py.
precondition_gate("400_build_metric_logic", table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count())


from datetime import datetime, timezone

from src.steps.metric_logic import metric_logic_step

nodes_rows = [r.asDict() for r in spark.table(config.lakehouse.graph_nodes).collect()]
edges_rows = [r.asDict() for r in spark.table(config.lakehouse.graph_edges).collect()]
print(f"Loaded {len(nodes_rows)} nodes, {len(edges_rows)} edges")

# Freshness inputs (Trust family): the PREVIOUS card table is the memory
# for logic-change detection; the extraction tracker (route 00c) carries
# source_extracted_at. Both are legitimately absent on a first run or a
# file-drop route — a FAILED read is not, and must raise.
previous_rows = []
if spark.catalog.tableExists("output_metric_logic"):
    previous_rows = [r.asDict() for r in spark.table("output_metric_logic").collect()]
else:
    print("No previous output_metric_logic — all logic_last_changed_at = now")

extraction_records = []
tracking_table = config.extractor.tracking_table if config.extractor else "ops_extraction_tracking"
if spark.catalog.tableExists(tracking_table):
    extraction_records = [r.asDict() for r in spark.table(tracking_table).collect()]
else:
    print("No extraction tracker (file-drop route) — source_extracted_at stays null")

metric_logic_rows = metric_logic_step(
    nodes_rows, edges_rows,
    previous_rows=previous_rows,
    extraction_records=extraction_records,
    run_at=datetime.now(timezone.utc).isoformat(),
)
print(f"Built {len(metric_logic_rows)} metric logic rows")
changed = sum(1 for r in metric_logic_rows
              if r["logic_last_changed_at"] and previous_rows
              and not any(p["metric_id"].lower() == r["metric_id"].lower()
                          and p.get("logic_last_changed_at") == r["logic_last_changed_at"]
                          for p in previous_rows))
if previous_rows:
    print(f"Logic changed since last run: {changed} metric(s)")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Save to Delta and run the postcondition gate
from src.steps.gates import postcondition_gate

ml_df = spark.createDataFrame(metric_logic_rows, schema=to_spark_schema(METRIC_LOGIC))
ml_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("output_metric_logic")

with_logic = sum(1 for r in metric_logic_rows if r["calculation_logic"] is not None)
with_tables = sum(1 for r in metric_logic_rows if r["source_tables"] is not None)
print(f"Saved {len(metric_logic_rows)} rows. Logic: {with_logic}, Tables: {with_tables}")

# Twin divergence cache (family F, ADR 0043): same-bare-name groups get
# the diff kernel's verdict precomputed. Written UNCONDITIONALLY — an
# empty table means "no twins exist", absence means 400 never ran.
from src.graph.decomposition_diff import twin_divergence_rows
from src.schemas import METRIC_TWINS

twin_rows = twin_divergence_rows(
    nodes_rows, edges_rows,
    run_at=datetime.now(timezone.utc).isoformat(),
)
twins_df = spark.createDataFrame(
    [(r["group_key"], r["metric_ids"], r["member_count"], r["verdict"],
      r["divergent_steps"], r["missing_steps"], r["summary"],
      r["computed_at"]) for r in twin_rows],
    schema=to_spark_schema(METRIC_TWINS))
twins_df.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable("output_metric_twins")
divergent = sum(1 for r in twin_rows if r["verdict"] == "divergent")
print(f"output_metric_twins: {len(twin_rows)} same-name groups "
      f"({divergent} divergent)")
for r in twin_rows:
    if r["verdict"] == "divergent":
        print(f"  [!] {r['group_key']}: {r['summary'][:160]}")

checked = postcondition_gate(
    "400_build_metric_logic",
    fetch=lambda t, cols: [r.asDict() for r in spark.table(t).select(*cols).collect()],
    table_exists=spark.catalog.tableExists,
)
print(f"[+] Postcondition gate passed for: {', '.join(checked)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
