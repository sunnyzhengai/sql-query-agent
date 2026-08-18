"""Fabric Notebook (utility): Manage Steward Assignments

Assign data stewards to metrics — individually, by pattern, or by department.
Assignments are saved to the gov_steward_assignments Delta table (this
notebook is its contract owner). They flow into the graph on the next
300_build_graph run, which applies them to canonical nodes; 04 then projects
them into output_metric_logic, where the agent reads them.

Requires the sql-logic-env Environment (no %pip installs — they break the
ScriptDom runtime and are banned in production notebooks).
"""

# %% Cell 1: Setup
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.governance.steward import StewardManager
from src.schemas import STEWARD_ASSIGNMENTS, to_spark_schema

# %% Cell 2: Load existing assignments and canonical metrics
manager = StewardManager()

# Existence checked explicitly: Cell 6 OVERWRITES this table, so a swallowed
# read error here would erase every existing assignment (audit 2026-08-15).
if spark.catalog.tableExists("gov_steward_assignments"):
    existing = [r.asDict() for r in spark.table("gov_steward_assignments").collect()]
    manager.load_from_records(existing)
    print(f"Loaded {len(existing)} existing steward assignments")
else:
    print("No gov_steward_assignments table yet — starting fresh")

canonical_metrics = []
for row in spark.table("graph_nodes").filter("layer = 'canonical'").collect():
    r = row.asDict()
    metric_id = r["node_id"].replace("canonical:", "")
    canonical_metrics.append({"metric_id": metric_id, "name": r["name"]})

all_metric_ids = [m["metric_id"] for m in canonical_metrics]
print(f"Found {len(canonical_metrics)} canonical metrics")
print(f"\n{manager.summary(len(canonical_metrics))}")

# %% Cell 3: Assign steward by pattern
# UNCOMMENT AND MODIFY to use:
#
# results = manager.assign_by_pattern(
#     pattern="census",
#     steward_name="Dr. Smith",
#     steward_email="dr.smith@org.com",
#     department="Surgery",
#     all_metrics=canonical_metrics,
#     assigned_by="admin",
# )
# print(f"Assigned {len(results)} metrics")

# %% Cell 4: Assign steward to an individual metric
# UNCOMMENT AND MODIFY to use:
#
# manager.assign(
#     metric_id="reporting.USP_PTA_CensusDashboard_PBI",
#     metric_name="USP_PTA_CensusDashboard_PBI",
#     steward_name="Adam Smith",
#     steward_email="adam.smith@org.com",
#     department="Patient Access",
#     assigned_by="admin",
# )

# %% Cell 5: Review coverage and unassigned metrics
print(manager.summary(len(canonical_metrics)))

unassigned = manager.get_unassigned(all_metric_ids)
print(f"\nUnassigned metrics ({len(unassigned)}):")
for mid in unassigned[:15]:
    print(f"  {mid}")
if len(unassigned) > 15:
    print(f"  ... and {len(unassigned) - 15} more")

# %% Cell 6: Save assignments (contract: gov_steward_assignments)
records = manager.to_records()
if records:
    df = spark.createDataFrame(records, schema=to_spark_schema(STEWARD_ASSIGNMENTS))
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("gov_steward_assignments")
    print(f"Saved {len(records)} assignments to gov_steward_assignments")
    print("\nRe-run 300_build_graph → 400_build_metric_logic to apply them to the")
    print("graph and the agent's metric_logic table.")
else:
    print("No assignments to save")
