"""Fabric Notebook: Metadata Sync

Generates metadata from the knowledge graph and pushes it to configured
catalogs (Purview, Collibra, or both).

This is the "wedge" product — the Metadata Sync component of the
Data Empowerment Suite.

In Fabric, this would be a .ipynb notebook. Kept as .py for version control.

To use in Fabric:
1. Create a new Notebook in your workspace
2. Copy each cell below into the notebook (cells are delimited by # %%)
3. Attach to your Lakehouse and Environment (with sql-query-agent .whl)
4. Run all cells

Prerequisites:
- Run the orchestrator notebook first to build the graph
- Configure adapters section in org_config.yaml
- Install adapter dependencies: pip install azure-identity requests
"""

# %% Cell 1: Setup
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.adapters.metadata_generator import generate_all_records
from src.adapters.publisher import create_publisher_from_config
from src.graph.builder import GraphBuilder
from src.models import GraphNode, GraphEdge, NodeLayer, EdgeType

# %% Cell 2: Load config
config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
print(f"Loaded config for: {config.org.name}")

if not config.adapters:
    print("WARNING: No adapters configured in org_config.yaml.")
    print("Add a 'adapters:' section with 'purview:' and/or 'collibra:' settings.")
    print("See org_config.example.yaml for reference.")

# %% Cell 3: Load graph from Delta tables
def read_table(name):
    if "/" in name:
        return spark.read.format("delta").load(name)  # noqa: F821
    return spark.table(name)  # noqa: F821

nodes_df = read_table(config.lakehouse.graph_nodes)
edges_df = read_table(config.lakehouse.graph_edges)

# Reconstruct GraphBuilder from Delta tables
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

# %% Cell 4: Generate metadata records
records = generate_all_records(builder)

print(f"Generated {len(records)} metadata records:")
record_types = {}
for r in records:
    record_types[r.asset_type] = record_types.get(r.asset_type, 0) + 1
for rtype, count in sorted(record_types.items()):
    print(f"  {rtype}: {count}")

# %% Cell 5: Preview records before publishing
print("\n=== Sample Records ===")
for r in records[:5]:
    print(f"\n  ID: {r.asset_id}")
    print(f"  Type: {r.asset_type}")
    print(f"  Name: {r.name}")
    print(f"  Owner: {r.owner or '(none)'}")
    desc_preview = r.description[:100] + "..." if len(r.description) > 100 else r.description
    print(f"  Description: {desc_preview}")

if len(records) > 5:
    print(f"\n  ... and {len(records) - 5} more records")

# %% Cell 6: Publish to configured catalogs
if config.adapters:
    adapter_config = config.adapters.model_dump(exclude_none=True)
    publisher = create_publisher_from_config(adapter_config)

    print(f"Configured adapters: {publisher.adapter_names}")

    # Test connections first
    print("\nTesting connections...")
    conn_status = publisher.test_connections()
    for name, ok in conn_status.items():
        status = "OK" if ok else "FAILED"
        print(f"  {name}: {status}")

    # Only publish if all connections are healthy
    all_ok = all(conn_status.values())
    if all_ok:
        print(f"\nPublishing {len(records)} records...")
        results = publisher.publish_all(records)

        for adapter_name, result in results.items():
            print(f"\n  {adapter_name}: {result}")
    else:
        print("\nSkipping publish — one or more connections failed.")
        print("Check your org_config.yaml adapter settings and permissions.")
else:
    print("No adapters configured — skipping publish.")
    print("To enable, add adapters section to org_config.yaml.")

# %% Cell 7: Write sync log to Delta
sync_log_rows = []
now = datetime.now(timezone.utc).isoformat()

if config.adapters:
    for adapter_name, result in results.items():
        for pr in result.results:
            sync_log_rows.append((
                now,
                adapter_name,
                pr.asset_id,
                pr.status.value,
                pr.message,
            ))

if sync_log_rows:
    from pyspark.sql.types import StringType, StructField, StructType  # noqa: E402

    sync_log_schema = StructType([
        StructField("synced_at", StringType(), False),
        StructField("adapter", StringType(), False),
        StructField("asset_id", StringType(), False),
        StructField("status", StringType(), False),
        StructField("message", StringType(), True),
    ])

    sync_log_df = spark.createDataFrame(sync_log_rows, schema=sync_log_schema)  # noqa: F821

    # Append to sync_log (don't overwrite — we want history)
    sync_log_table = "Tables/sync_log"
    try:
        existing = spark.read.format("delta").load(sync_log_table)  # noqa: F821
        sync_log_df.write.format("delta").mode("append").save(sync_log_table)
        print(f"\nAppended {len(sync_log_rows)} records to sync_log")
    except Exception:
        sync_log_df.write.format("delta").mode("overwrite").save(sync_log_table)
        print(f"\nCreated sync_log with {len(sync_log_rows)} records")
else:
    print("\nNo sync results to log.")

# %% Cell 8: Summary
print("\n=== Metadata Sync Summary ===")
print(f"Records generated: {len(records)}")
if config.adapters:
    for adapter_name, result in results.items():
        print(f"  {adapter_name}: {result}")
else:
    print("  No adapters configured")
print(f"Sync log: {len(sync_log_rows)} entries written")
