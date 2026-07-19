"""Fabric Notebook: Generate Summaries for Graph Nodes

Run AFTER orchestrator_v2 to add LLM-generated summaries to the graph.
Uses OpenAI API to summarize each transformation step and each metric.

Run order:
1. load_clarity_dictionary.py (one-time)
2. load_sql_files.py (one-time)
3. orchestrator_v2.py (builds graph)
4. THIS NOTEBOOK (adds summaries to graph)
"""

# %% Cell 1: Install dependencies
%pip install openai

# %% Cell 2: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.parser.summary_generator import (
    generate_transform_summaries,
    generate_canonical_summaries,
    apply_summaries,
)
from src.parser.llm_extractor import AzureOpenAIBackend
from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.models import GraphNode, GraphEdge, NodeLayer, EdgeType

# %% Cell 3: Configure OpenAI
# OPTION A: Regular OpenAI (personal key)
import openai

class OpenAIBackend:
    def __init__(self, api_key, model="gpt-4o-mini", max_tokens=500):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a healthcare data analyst. Summarize SQL logic in plain English for business users."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=0,
        )
        return response.choices[0].message.content.strip()

# UPDATE THIS with your OpenAI API key
OPENAI_API_KEY = "REPLACE_WITH_YOUR_OPENAI_API_KEY"

# Use gpt-4o-mini for cost efficiency (summaries don't need GPT-4)
backend = OpenAIBackend(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

# Quick test
test = backend.generate("Summarize in one sentence: SELECT COUNT(*) FROM patients WHERE age > 65")
print(f"LLM test: {test}")

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

print(f"Loaded graph: {len(builder.nodes)} nodes, {len(builder.edges)} edges")

# Count nodes by layer
from collections import Counter
layer_counts = Counter(n.layer.value for n in builder.nodes.values())
print(f"Canonical: {layer_counts.get('canonical', 0)}")
print(f"Transformation: {layer_counts.get('transformation', 0)}")
print(f"Technical: {layer_counts.get('technical', 0)}")

# %% Cell 5: Generate transformation summaries
# This calls the LLM once per transformation node.
# With gpt-4o-mini at ~$0.15/1M tokens, 685 transforms ≈ $0.10-0.50
print("Generating transformation summaries...")
transform_summaries = generate_transform_summaries(builder, backend, batch_size=20)
print(f"Generated {len(transform_summaries)} transformation summaries")

# Preview a few
for node_id, summary in list(transform_summaries.items())[:3]:
    print(f"\n  {node_id}:")
    print(f"  {summary[:150]}")

# %% Cell 6: Generate canonical (metric) summaries
# This calls the LLM once per metric. Uses transform summaries as input.
# ~578 metrics ≈ $0.10-0.50 with gpt-4o-mini
print("Generating canonical summaries...")
canonical_summaries = generate_canonical_summaries(builder, backend, transform_summaries)
print(f"Generated {len(canonical_summaries)} canonical summaries")

# Preview a few
for node_id, summary in list(canonical_summaries.items())[:3]:
    print(f"\n  {node_id}:")
    print(f"  {summary[:200]}")

# %% Cell 7: Apply summaries to graph and re-write Delta tables
# Merge all summaries
all_summaries = {**transform_summaries, **canonical_summaries}
updated = apply_summaries(builder, all_summaries)
print(f"Applied summaries to {updated} nodes")

# Re-write graph_nodes with summaries included
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

# %% Cell 8: Verify — test a metric
traverser = GraphTraverser(builder.nodes, builder.edges)

# Find first canonical node with a summary
for node in builder.nodes.values():
    if node.layer == NodeLayer.CANONICAL and node.description:
        print(f"Metric: {node.name}")
        print(f"Description: {node.description}")
        print()

        # Show its transformation summaries
        metric_id = node.node_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)
        if subgraph:
            for t in subgraph["transformations"]:
                summary = t.properties.get("summary", "")
                if summary and t.name != "__final_select__":
                    print(f"  Step [{t.name}]: {summary}")
        break

print("\nDone! Re-test your Data Agent — it should now give instant, descriptive answers.")
