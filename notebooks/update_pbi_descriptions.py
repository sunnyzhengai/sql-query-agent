"""Fabric Notebook: Update Power BI Report Descriptions

Reads the graph's canonical node summaries and pushes them to
Power BI report description fields via the Fabric REST API.

Prerequisites:
- Run orchestrator_v2 (builds graph)
- Run generate_summaries (adds descriptions to canonical nodes)
- You need Contributor or Admin role on the target workspace

Run order:
1. orchestrator_v2.py
2. generate_summaries.py
3. THIS NOTEBOOK
"""

# %% Cell 1: Install dependencies
%pip install pydantic pyyaml sqlglot requests

# %% Cell 2: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.adapters.fabric_pbi import FabricPBIUpdater, match_reports_to_metrics
from src.graph.builder import GraphBuilder
from src.models import GraphNode, NodeLayer

# %% Cell 3: Configure
# UPDATE THIS with your workspace ID
# To find it: go to your workspace in Fabric, look at the URL:
# https://app.fabric.microsoft.com/groups/YOUR-WORKSPACE-ID-HERE/...
WORKSPACE_ID = "REPLACE_WITH_YOUR_WORKSPACE_ID"

updater = FabricPBIUpdater(workspace_id=WORKSPACE_ID)

# %% Cell 4: List reports in the workspace
reports = updater.list_reports()
print(f"Found {len(reports)} reports in workspace\n")
for r in reports[:20]:
    desc_preview = r.description[:50] + "..." if r.description else "(no description)"
    print(f"  {r.name}: {desc_preview}")
if len(reports) > 20:
    print(f"  ... and {len(reports) - 20} more")

# %% Cell 5: Load graph nodes (with summaries)
nodes_df = spark.table("graph_nodes")

graph_nodes = {}
for row in nodes_df.collect():
    row_dict = row.asDict()
    props = json.loads(row_dict.get("properties", "{}"))
    graph_nodes[row_dict["node_id"]] = GraphNode(
        node_id=row_dict["node_id"],
        layer=NodeLayer(row_dict["layer"]),
        name=row_dict["name"],
        description=row_dict.get("description", ""),
        properties=props,
    )

canonical_count = sum(1 for n in graph_nodes.values() if n.layer == NodeLayer.CANONICAL)
with_desc = sum(1 for n in graph_nodes.values() if n.layer == NodeLayer.CANONICAL and n.description)
print(f"Loaded {len(graph_nodes)} nodes ({canonical_count} canonical, {with_desc} with descriptions)")

# %% Cell 6: Match reports to graph metrics
matches = match_reports_to_metrics(reports, graph_nodes)
print(f"Matched {len(matches)} reports to graph metrics\n")
for m in matches[:10]:
    print(f"  Report: {m['report_name']}")
    print(f"  Metric: {m['matched_metric']}")
    print(f"  Description: {m['description'][:100]}...")
    print()
if len(matches) > 10:
    print(f"  ... and {len(matches) - 10} more matches")

# %% Cell 7: Preview — what would be updated (DRY RUN)
print("=== DRY RUN — these descriptions would be updated ===\n")
for m in matches:
    print(f"  [{m['report_name']}]")
    print(f"    Current: {next((r.description for r in reports if r.report_id == m['report_id']), '(none)')[:80]}")
    print(f"    New: {m['description'][:80]}...")
    print()

print(f"Total: {len(matches)} reports would be updated")
print("\nIf this looks right, run Cell 8 to apply the updates.")

# %% Cell 8: Apply updates (UNCOMMENT TO RUN)
# WARNING: This will modify report descriptions in your workspace.
# Review Cell 7 output first.

# result = updater.update_descriptions_bulk(matches)
# print(f"\n{result}")
# for r in result.results:
#     print(f"  {r.report_name}: {r.status} — {r.message}")
