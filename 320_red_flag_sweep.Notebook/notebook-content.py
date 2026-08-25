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

"""Fabric Notebook: Governance Red-Flag Sweep (ADR 0054)

Reads from: graph_nodes, graph_edges (Delta); gov_flag_dispositions
            (optional — steward acts, absent until any are recorded)
Writes to:  gov_red_flags (overwrite)

Run 300_build_graph first. Flags DISCLOSE, never gate: misnomers
(same name, divergent logic hashes), duplicates (same hash, different
names), cousin conflicts (name families, divergent hashes) — with the
conservation partition asserted (clean + flagged + excluded = swept).
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
REQUIRES_ENGINE = "1.57"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "320_red_flag_sweep")


from src.config import load_config  # noqa: F401

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load the graph (+ optional disposition events)
from datetime import datetime, timezone

from src.steps.gates import precondition_gate

precondition_gate("320_red_flag_sweep",
                  table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count(),
                  columns_of=lambda t: spark.table(t).columns)

nodes_rows = [r.asDict() for r in spark.table("graph_nodes").collect()]
edges_rows = [r.asDict() for r in spark.table("graph_edges").collect()]

# APPEND-ONLY steward acts: absence is a legitimate state (no ruling
# yet); a FAILED read is not — it must raise (the steward-records
# lesson, audit 2026-08-15).
disposition_events = []
if spark.catalog.tableExists("gov_flag_dispositions"):
    disposition_events = sorted(
        (r.asDict() for r in spark.table("gov_flag_dispositions").collect()),
        key=lambda e: str(e.get("event_at") or ""))
else:
    print("No gov_flag_dispositions table — no steward rulings yet")

print(f"Loaded {len(nodes_rows)} nodes, {len(edges_rows)} edges, "
      f"{len(disposition_events)} disposition event(s)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Sweep (all logic in src/steps/red_flag_sweep.py)
from src.schemas import GOV_RED_FLAGS, to_spark_schema
from src.steps.red_flag_sweep import red_flag_sweep_step

run_at = datetime.now(timezone.utc).isoformat()
out = red_flag_sweep_step(nodes_rows, edges_rows,
                          disposition_events=disposition_events,
                          run_at=run_at)

for line in out.summary_lines():
    print(line)
if out.rejected_dispositions:
    for r in out.rejected_dispositions:
        print(f"  [!] rejected: {r.get('rejected')} :: "
              f"{r.get('flag_id')} {r.get('kind')}")

df = spark.createDataFrame(out.flags_rows,
                           schema=to_spark_schema(GOV_RED_FLAGS))
df.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable("gov_red_flags")
print(f"[+] Wrote {len(out.flags_rows)} flag(s) to gov_red_flags")
print("\nNext: 800_export_graph_tables (exports the flag surface), "
      "then 700_refresh_search_index.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
