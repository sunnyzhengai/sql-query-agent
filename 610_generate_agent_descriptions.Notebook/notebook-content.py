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

"""Fabric Notebook: Generate Data-Agent Descriptions (derivation step)

Generation split from publishing (2026-08-18): this step OWNS
ops_agent_descriptions; 900 (Collibra) and 920 (PBI) are pure
publishers that consume it. Run AFTER 400 (needs the logic hashes);
re-run any time — unchanged metrics are skipped, rejected rows retry.

Reads from: graph_nodes, output_metric_logic (+ Fabric Data Agent)
Writes to:  ops_agent_descriptions
"""

# %% Cell 0: Setup
import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.24"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "610_generate_agent_descriptions")


from src.config import load_config
from src.steps.gates import precondition_gate

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
WORKSPACE_ID = config.fabric_graph.workspace_id
AGENT_ID = config.fabric_graph.data_agent_id

precondition_gate("610_generate_agent_descriptions",
                  table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count(),
                  columns_of=lambda t: spark.table(t).columns)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Plan — which metrics need (re)generation
from src.adapters.collibra_lineage_match import extract_match_key
from src.models import NodeLayer
from src.steps.agent_descriptions import plan_generation, sql_hash

# Scope: metrics with an extractable publish key (the _PBI convention).
# Set INCLUDE_ALL = True to generate for every canonical metric instead.
INCLUDE_ALL = False

metric_names = []
for row in spark.table(config.lakehouse.graph_nodes).collect():
    r = row.asDict()
    if r["layer"] != NodeLayer.CANONICAL.value:
        continue
    if INCLUDE_ALL or extract_match_key(r["name"]) is not None:
        metric_names.append(r["name"])
print(f"In scope: {len(metric_names)} metrics (INCLUDE_ALL={INCLUDE_ALL})")

# output_metric_logic is a REQUIRED input (400 writes it; the gate above
# enforced it). A swallowed read here once marked every metric "new" and
# re-generated everything — hours of Data Agent calls (audit 2026-08-15).
current_hashes = {}
for row in spark.table("output_metric_logic").collect():
    r = row.asDict()
    current_hashes[r["metric_name"]] = sql_hash(r.get("calculation_logic") or "")

existing_records = []
if spark.catalog.tableExists("ops_agent_descriptions"):
    existing_records = [row.asDict() for row in spark.table("ops_agent_descriptions").collect()]
else:
    print("No ops_agent_descriptions table yet (first run) — will generate all")

plan = plan_generation(metric_names, current_hashes, existing_records)
print(f"  {len(plan.reused)} current (skipped)")
print(f"  {len(plan.needs_generation)} need generation"
      + (f" (incl. {len(plan.retrying_rejected)} rejected retries)"
         if plan.retrying_rejected else ""))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Generate (incremental full-set saves — resume by re-running)
from pyspark.sql.types import StringType, StructField, StructType

from src.adapters.fabric_agent import FabricAgentClient
from src.steps.agent_descriptions import STATUS_OK, run_generation

# token_provider (not a one-shot token): re-fetched per request and forced
# on 401, so >1hr generation runs survive token expiry (audit 2026-08-15).
agent = FabricAgentClient(
    workspace_id=WORKSPACE_ID,
    agent_id=AGENT_ID,
    token_provider=lambda: notebookutils.credentials.getToken("https://api.fabric.microsoft.com"),  # noqa: F821
)
print(f"Data Agent tool: {agent.discover_tool_name()}")

desc_schema = StructType([
    StructField("metric_name", StringType(), False),
    StructField("description", StringType(), False),
    StructField("sql_hash", StringType(), True),
    StructField("status", StringType(), False),
])

# Full row set: start from EVERYTHING already persisted (ok + rejected)
rows = {r["metric_name"]: {
    "metric_name": r["metric_name"], "description": r["description"],
    "sql_hash": r.get("sql_hash", ""), "status": r.get("status", STATUS_OK)}
    for r in existing_records}

def save(all_rows):
    df = spark.createDataFrame(
        [(r["metric_name"], r["description"], r["sql_hash"], r["status"])
         for r in all_rows], schema=desc_schema)
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("ops_agent_descriptions")

def generate(name):
    resp = agent.generate_metric_description(name)
    if resp.status == "success" and resp.answer:
        return ("success", resp.answer)
    return ("error", resp.error or "no answer")

if plan.needs_generation:
    # Canary gate: one probe against an already-OK metric (or the first
    # planned one) before spending hundreds of calls (field find
    # 2026-08-18: stale agent data sources -> every call a refusal).
    from src.steps.agent_descriptions import canary_check

    known = next((m for m, r in rows.items() if r["status"] == STATUS_OK),
                 plan.needs_generation[0])
    ok, detail = canary_check(generate, known)
    print(f"Canary [{known}]: {detail}")
    if not ok:
        raise SystemExit("Canary gate failed — aborting before the batch.")

    result = run_generation(
        plan.needs_generation, generate, rows, current_hashes, save)
    print()
    for line in result.summary_lines():
        print(line)
else:
    print("All descriptions are current — nothing to generate.")

ok = sum(1 for r in rows.values() if r["status"] == STATUS_OK)
rej = len(rows) - ok
print(f"\nops_agent_descriptions now holds {len(rows)} rows "
      f"({ok} ok, {rej} rejected)")
print("Next: 900_publish_collibra and/or 920_publish_pbi consume this table.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
