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

"""Fabric Notebook: Publish Metric Descriptions onto Power BI Reports

The enrichment-out story (ADR 0040): the certified description a metric
earned in the graph is published back onto the report built on it — the
answer becomes the report's caption. Matching is LINEAGE-EXACT via
report_to_canonical edges (from 12's TMDL extraction); nothing is ever
matched by name similarity.

Reads from: graph_nodes, graph_edges (+ Fabric REST: workspace reports)
Writes to:  gov_publish_log (append; target=fabric_pbi)

Run AFTER 07 (descriptions) — and after 12 + 03 (report lineage).
"""

# %% Cell 0: Setup
import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from src.config import load_config

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# Workspace whose reports receive descriptions — the workspace this
# notebook runs in, via its id in the notebook context.
WORKSPACE_ID = notebookutils.runtime.context.get("currentWorkspaceId")  # noqa: F821
print(f"Workspace: {WORKSPACE_ID}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Load graph, list workspace reports, match by lineage
from src.adapters.fabric_pbi import FabricPBIUpdater, match_reports_by_lineage

nodes_rows = [r.asDict() for r in spark.table("graph_nodes").collect()]

# Prefer Data-Agent descriptions where 07b generated them (optional —
# without the table, 07's graph descriptions publish as before). 13 is
# a pure publisher either way (split verdict 2026-08-18).
if spark.catalog.tableExists("ops_agent_descriptions"):
    from src.steps.agent_descriptions import STATUS_OK

    agent_descs = {
        r["metric_name"]: r["description"]
        for r in (row.asDict() for row in spark.table("ops_agent_descriptions").collect())
        if r.get("status", STATUS_OK) == STATUS_OK
    }
    overlaid = 0
    for n in nodes_rows:
        if n.get("layer") == "canonical" and n["name"] in agent_descs:
            n["description"] = agent_descs[n["name"]]
            overlaid += 1
    print(f"Agent-description overlay: {overlaid} canonical nodes")
else:
    print("No ops_agent_descriptions — publishing 07 graph descriptions")
edges_rows = [r.asDict() for r in spark.table("graph_edges").collect()]

updater = FabricPBIUpdater(workspace_id=WORKSPACE_ID)
reports = updater.list_reports()
print(f"Workspace reports: {len(reports)}")

updates, skipped = match_reports_by_lineage(reports, nodes_rows, edges_rows)
print(f"Lineage-matched: {len(updates)}")
for u in updates:
    print(f"  {u['report_name']} <- {u['matched_metric']}")
for reason in skipped:
    print(f"  [i] skipped: {reason}")

# STOP HERE and review the matches before running the next cell.

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Publish descriptions and append the durable publish log
import uuid
from datetime import datetime, timezone

from src.adapters.fabric_pbi import to_publish_results
from src.governance.publish_log import publish_log_rows
from src.schemas import PUBLISH_LOG, to_spark_schema

result = updater.update_descriptions_bulk(updates)
print(result)

log_rows = publish_log_rows(
    to_publish_results(result),
    target="fabric_pbi",
    kind="report_description",
    run_id=str(uuid.uuid4()),
    published_at=datetime.now(timezone.utc).isoformat(),
)
if log_rows:
    spark.createDataFrame(log_rows, schema=to_spark_schema(PUBLISH_LOG)) \
        .write.format("delta").mode("append").saveAsTable("gov_publish_log")
    print(f"Appended {len(log_rows)} rows to gov_publish_log")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
