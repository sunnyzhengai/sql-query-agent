"""Fabric Notebook: Generate Summaries for Graph Nodes

Run AFTER orchestrator to add LLM-generated summaries to the graph.
Uses OpenAI API to summarize each metric and its transformation steps.

Two modes:
- COMBINED (default, recommended): One LLM call per metric — generates
  both metric-level and step-level summaries. ~3x faster.
- SEPARATE: Two passes — one for transforms, one for canonicals.
  Slower but produces transform summaries even for unlinked transforms.

Run order:
1. load_clarity_dictionary.py (one-time)
2. load_sql_files.py (one-time)
3. orchestrator.py (builds graph)
4. THIS NOTEBOOK (adds summaries to graph)
"""

# %% Cell 1: Install dependencies
%pip install openai pydantic pyyaml sqlglot

# %% Cell 2: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.parser.summary_generator import (
    generate_all_summaries_combined,
    apply_summaries,
)
from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.models import GraphNode, GraphEdge, NodeLayer, EdgeType

# %% Cell 3: Configure OpenAI
import openai

class OpenAIBackend:
    def __init__(self, api_key, model="gpt-4o-mini", max_tokens=1000):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a healthcare data analyst. Summarize SQL logic in plain English for business users. When asked for JSON, respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=0,
        )
        return response.choices[0].message.content.strip()

# UPDATE THIS with your OpenAI API key
OPENAI_API_KEY = "REPLACE_WITH_YOUR_OPENAI_API_KEY"

backend = OpenAIBackend(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

# Quick test
test = backend.generate("Say OK")
print(f"LLM backend ready: {test}")

# %% Cell 4: Load existing graph from Delta tables
nodes_df = spark.table("graph_nodes")
edges_df = spark.table("graph_edges")

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

for row in edges_df.collect():
    row_dict = row.asDict()
    props = json.loads(row_dict.get("properties", "{}"))
    builder.edges.append(GraphEdge(
        source_id=row_dict["source_id"],
        target_id=row_dict["target_id"],
        edge_type=EdgeType(row_dict["edge_type"]),
        properties=props,
    ))

from collections import Counter
layer_counts = Counter(n.layer.value for n in builder.nodes.values())
print(f"Loaded graph: {len(builder.nodes)} nodes, {len(builder.edges)} edges")
print(f"Canonical: {layer_counts.get('canonical', 0)}, Transformation: {layer_counts.get('transformation', 0)}")

# %% Cell 5: Generate combined summaries (one LLM call per metric)
# Estimated time: ~12-15 minutes for ~400 metrics
# Estimated cost: ~$0.50-1.00 with gpt-4o-mini
print("Generating combined summaries (metric + step summaries in one call)...")
canonical_summaries, transform_summaries = generate_all_summaries_combined(
    builder, backend, batch_log_interval=20
)
print(f"\nCanonical summaries: {len(canonical_summaries)}")
print(f"Transform summaries: {len(transform_summaries)}")

# Preview a few canonical summaries
print("\n=== Sample Metric Summaries ===")
for node_id, summary in list(canonical_summaries.items())[:3]:
    name = builder.nodes[node_id].name if node_id in builder.nodes else node_id
    print(f"\n  {name}:")
    print(f"  {summary[:200]}...")

# Preview a few transform summaries
print("\n=== Sample Step Summaries ===")
for node_id, summary in list(transform_summaries.items())[:3]:
    name = builder.nodes[node_id].name if node_id in builder.nodes else node_id
    print(f"\n  {name}: {summary[:150]}")

# %% Cell 6: Apply summaries to graph and re-write Delta tables
all_summaries = {**canonical_summaries, **transform_summaries}
updated = apply_summaries(builder, all_summaries)
print(f"Applied summaries to {updated} nodes")

# Re-write graph_nodes with summaries
from pyspark.sql.types import StringType, StructField, StructType

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

nodes_df = spark.createDataFrame(nodes_rows, schema=nodes_schema)
nodes_df.write.format("delta").mode("overwrite").saveAsTable("graph_nodes")
print(f"Wrote {nodes_df.count()} nodes to graph_nodes (with summaries)")

# %% Cell 7: Verify — test a metric
traverser = GraphTraverser(builder.nodes, builder.edges)

for node in builder.nodes.values():
    if node.layer == NodeLayer.CANONICAL and node.description:
        print(f"Metric: {node.name}")
        print(f"Description: {node.description}")
        print()

        metric_id = node.node_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)
        if subgraph:
            for t in subgraph["transformations"]:
                summary = t.properties.get("summary", "")
                if summary and t.name != "__final_select__":
                    print(f"  Step [{t.name}]: {summary}")
        break

print("\nDone! Re-test your Data Agent — answers should be instant and descriptive.")
