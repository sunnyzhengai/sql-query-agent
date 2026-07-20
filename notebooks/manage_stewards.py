"""Fabric Notebook: Manage Steward Assignments

Assign data stewards to metrics — individually, by pattern, or by department.
Steward assignments are stored in a Delta table and applied to graph nodes.

The Data Agent can also assign stewards via chat commands (/stewards),
but this notebook provides the bulk assignment and management interface.
"""

# %% Cell 1: Install dependencies
%pip install pydantic pyyaml sqlglot

# %% Cell 2: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.governance.steward import StewardManager
from src.graph.builder import GraphBuilder
from src.models import GraphNode, NodeLayer

# %% Cell 3: Load existing assignments and graph
manager = StewardManager()

# Load existing steward assignments if table exists
try:
    assignments_df = spark.table("steward_assignments")
    existing = [row.asDict() for row in assignments_df.collect()]
    manager.load_from_records(existing)
    print(f"Loaded {len(existing)} existing steward assignments")
except Exception:
    print("No existing steward_assignments table — starting fresh")

# Load canonical metrics from graph
nodes_df = spark.table("graph_nodes")
canonical_metrics = []
for row in nodes_df.filter("layer = 'canonical'").collect():
    r = row.asDict()
    canonical_metrics.append({"metric_id": r["name"], "name": r["name"]})

print(f"Found {len(canonical_metrics)} canonical metrics")

# Show current coverage
all_metric_ids = [m["metric_id"] for m in canonical_metrics]
unassigned = manager.get_unassigned(all_metric_ids)
print(f"\n{manager.summary(len(canonical_metrics))}")

# %% Cell 4: Assign steward by pattern
# Example: assign all census metrics to a steward
# UNCOMMENT AND MODIFY to use:

# results = manager.assign_by_pattern(
#     pattern="census",
#     steward_name="Dr. Smith",
#     steward_email="dr.smith@org.com",
#     department="Surgery",
#     all_metrics=canonical_metrics,
#     assigned_by="admin",
# )
# print(f"Assigned {len(results)} metrics")
# for r in results:
#     print(f"  {r.metric_name} → {r.steward_name}")

# %% Cell 5: Assign steward to individual metric
# UNCOMMENT AND MODIFY to use:

# manager.assign(
#     metric_id="USP_PTA_CensusDashboard_PBI",
#     metric_name="USP_PTA_CensusDashboard_PBI",
#     steward_name="Adam Smith",
#     steward_email="adam.smith@org.com",
#     department="Patient Access",
#     assigned_by="admin",
# )

# %% Cell 6: Bulk assign by department
# Example: assign all metrics to a department steward
# UNCOMMENT AND MODIFY to use:

# department_patterns = {
#     "Dr. Smith": ["census", "adt", "admission"],
#     "Dr. Jones": ["readmission", "discharge"],
#     "Dr. White": ["lote", "interpreter", "language"],
# }
#
# for steward, patterns in department_patterns.items():
#     for pattern in patterns:
#         results = manager.assign_by_pattern(
#             pattern=pattern,
#             steward_name=steward,
#             all_metrics=canonical_metrics,
#             assigned_by="admin",
#         )
#         if results:
#             print(f"  {steward}: {len(results)} metrics matching '{pattern}'")

# %% Cell 7: Review assignments
print("=== Current Assignments ===\n")
print(manager.summary(len(canonical_metrics)))

# Show first 20 assignments
records = manager.to_records()
print(f"\nAssignments ({len(records)} total):")
for r in records[:20]:
    print(f"  {r['metric_name']} → {r['steward_name']} ({r['department']})")
if len(records) > 20:
    print(f"  ... and {len(records) - 20} more")

# Show unassigned
unassigned = manager.get_unassigned(all_metric_ids)
print(f"\nUnassigned metrics ({len(unassigned)}):")
for mid in unassigned[:10]:
    print(f"  {mid}")
if len(unassigned) > 10:
    print(f"  ... and {len(unassigned) - 10} more")

# %% Cell 8: Save assignments to Delta table and update graph
from pyspark.sql.types import StringType, StructField, StructType

# Save steward_assignments table
assignments_schema = StructType([
    StructField("metric_id", StringType(), False),
    StructField("metric_name", StringType(), False),
    StructField("steward_name", StringType(), False),
    StructField("steward_email", StringType(), True),
    StructField("department", StringType(), True),
    StructField("assigned_date", StringType(), True),
    StructField("assigned_by", StringType(), True),
])

records = manager.to_records()
if records:
    assignments_df = spark.createDataFrame(records, schema=assignments_schema)
    assignments_df.write.format("delta").mode("overwrite").saveAsTable("steward_assignments")
    print(f"Saved {len(records)} assignments to steward_assignments table")
else:
    print("No assignments to save")

# Update graph nodes with steward info
builder = GraphBuilder()
for row in nodes_df.collect():
    r = row.asDict()
    props = json.loads(r.get("properties", "{}"))
    builder.nodes[r["node_id"]] = GraphNode(
        node_id=r["node_id"],
        layer=NodeLayer(r["layer"]),
        name=r["name"],
        description=r.get("description", ""),
        properties=props,
    )

updated = manager.apply_to_graph(builder)
print(f"Updated {updated} graph nodes with steward info")

# Re-write graph_nodes
nodes_rows = [
    (n.node_id, n.layer.value, n.name, n.description, json.dumps(n.properties))
    for n in builder.nodes.values()
]

nodes_schema = StructType([
    StructField("node_id", StringType(), False),
    StructField("layer", StringType(), False),
    StructField("name", StringType(), False),
    StructField("description", StringType(), True),
    StructField("properties", StringType(), True),
])

nodes_df_new = spark.createDataFrame(nodes_rows, schema=nodes_schema)
nodes_df_new.write.format("delta").mode("overwrite").saveAsTable("graph_nodes")
print(f"Wrote {nodes_df_new.count()} nodes to graph_nodes (with steward info)")
print("\nDone! The Data Agent can now answer 'who owns [metric]?' questions.")
