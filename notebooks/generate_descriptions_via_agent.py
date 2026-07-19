"""Fabric Notebook: Generate Metric Descriptions via Data Agent

Uses the Fabric Data Agent API to generate business descriptions
for each metric. The agent produces better descriptions than direct
LLM calls because it traverses the knowledge graph and applies
persona instructions.

Run AFTER orchestrator.py has built the graph and the Data Agent
is configured with graph_nodes + graph_edges.

Run order:
1. orchestrator.py (builds graph)
2. Configure Data Agent in Fabric portal (add graph tables + instructions)
3. THIS NOTEBOOK (generates descriptions via agent API)
4. update_pbi_descriptions.py or metadata_sync.py (push to catalogs)
"""

# %% Cell 1: Install dependencies
%pip install pydantic pyyaml sqlglot requests

# %% Cell 2: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.adapters.fabric_agent import FabricAgentClient
from src.graph.builder import GraphBuilder
from src.models import GraphNode, NodeLayer

# %% Cell 3: Configure
# UPDATE THESE with your workspace and agent IDs from the Fabric URL
WORKSPACE_ID = "REPLACE_WITH_YOUR_WORKSPACE_ID"   # the fxxxxx-xxxxx from the URL
AGENT_ID = "REPLACE_WITH_YOUR_AGENT_ID"            # the dxxxxx-xxxxx from the URL

client = FabricAgentClient(workspace_id=WORKSPACE_ID, agent_id=AGENT_ID)

# Discover the tool name automatically
print("Discovering Data Agent tool name...")
tool_name = client.discover_tool_name()
print(f"Tool name: {tool_name}")

# Quick test
print("\nTesting Data Agent connection...")
test_response = client.query("List 3 business metrics that are available in the system")
print(f"Status: {test_response.status}")
if test_response.status == "success":
    print(f"Response preview: {test_response.answer[:300]}...")
else:
    print(f"Error: {test_response.error}")
    print("Check your workspace_id and agent_id. Make sure the agent is published.")

# %% Cell 4: Load canonical metrics from graph
nodes_df = spark.table("graph_nodes")

canonical_metrics = []
for row in nodes_df.filter("layer = 'canonical'").collect():
    canonical_metrics.append(row.asDict())

print(f"Found {len(canonical_metrics)} canonical metrics")
for m in canonical_metrics[:5]:
    print(f"  {m['name']}")

# %% Cell 5: Generate descriptions for a small test batch
TEST_BATCH_SIZE = 3

print(f"Testing with first {TEST_BATCH_SIZE} metrics...\n")
test_names = [m["name"] for m in canonical_metrics[:TEST_BATCH_SIZE]]
test_results = client.generate_descriptions_bulk(test_names)

for name, response in test_results.items():
    print(f"\n{'='*60}")
    print(f"Metric: {name}")
    print(f"Status: {response.status}")
    if response.status == "success":
        print(f"Description:\n{response.answer}")
    else:
        print(f"Error: {response.error}")

# %% Cell 6: Generate descriptions for ALL metrics
# WARNING: This sends one API call per metric. May take a while.
# Estimated time: ~2-5 seconds per metric
print(f"Generating descriptions for all {len(canonical_metrics)} metrics...")

all_names = [m["name"] for m in canonical_metrics]
all_results = client.generate_descriptions_bulk(all_names, batch_log_interval=20)

succeeded = sum(1 for r in all_results.values() if r.status == "success")
failed = sum(1 for r in all_results.values() if r.status == "failed")
print(f"\nDone: {succeeded} succeeded, {failed} failed")

# %% Cell 7: Write descriptions back to graph_nodes
from pyspark.sql.types import StringType, StructField, StructType
from src.parser.summary_generator import apply_summaries

# Build a summaries dict: canonical node_id -> description
builder = GraphBuilder()
for row in nodes_df.collect():
    row_dict = row.asDict()
    props = json.loads(row_dict.get("properties", "{}"))
    builder.nodes[row_dict["node_id"]] = GraphNode(
        node_id=row_dict["node_id"],
        layer=NodeLayer(row_dict["layer"]),
        name=row_dict["name"],
        description=row_dict.get("description", ""),
        properties=props,
    )

# Map metric names back to node IDs
name_to_node_id = {
    n.name: n.node_id for n in builder.nodes.values()
    if n.layer == NodeLayer.CANONICAL
}

agent_summaries = {}
for name, response in all_results.items():
    if response.status == "success" and name in name_to_node_id:
        agent_summaries[name_to_node_id[name]] = response.answer

updated = apply_summaries(builder, agent_summaries)
print(f"Applied {updated} agent-generated descriptions to graph nodes")

# Re-write graph_nodes
nodes_schema = StructType([
    StructField("node_id", StringType(), False),
    StructField("layer", StringType(), False),
    StructField("name", StringType(), False),
    StructField("description", StringType(), True),
    StructField("properties", StringType(), True),
])

nodes_rows = [
    (n.node_id, n.layer.value, n.name, n.description, json.dumps(n.properties))
    for n in builder.nodes.values()
]

nodes_df_new = spark.createDataFrame(nodes_rows, schema=nodes_schema)
nodes_df_new.write.format("delta").mode("overwrite").saveAsTable("graph_nodes")
print(f"Wrote {nodes_df_new.count()} nodes to graph_nodes (with agent descriptions)")

# %% Cell 8: Preview results
print("\n=== Sample Descriptions ===")
count = 0
for node in builder.nodes.values():
    if node.layer == NodeLayer.CANONICAL and node.description and count < 3:
        print(f"\nMetric: {node.name}")
        print(f"Description: {node.description[:300]}...")
        count += 1

print(f"\nDone! Descriptions ready for Collibra/Purview/PBI sync.")
