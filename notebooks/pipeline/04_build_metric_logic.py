"""Fabric Notebook: Build Metric Logic Table

Reads from: graph_nodes, graph_edges (Delta tables)
Writes to:  metric_logic (Delta table)

Prerequisite: Run 01_setup.py first (same session).
              Run 03_build_graph.py at least once (writes graph tables).

Flattens the graph into a single table the Data Agent can query
without multi-hop traversal. One row per metric with calculation
logic, source tables, and descriptions pre-joined.
"""

# %% Cell 1: Load graph from Delta
from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.models import GraphNode, NodeLayer, GraphEdge, EdgeType
from src.parser.sql_parser import normalize_sql_whitespace

# Reconstruct in-memory graph from Delta tables
nodes_df = spark.table(config.lakehouse.graph_nodes)
edges_df = spark.table(config.lakehouse.graph_edges)

nodes = {}
for row in nodes_df.collect():
    r = row.asDict()
    props = json.loads(r["properties"]) if r["properties"] else {}
    nodes[r["node_id"]] = GraphNode(
        node_id=r["node_id"],
        layer=NodeLayer(r["layer"]),
        name=r["name"],
        description=r["description"] or "",
        properties=props,
    )

edges = []
for row in edges_df.collect():
    r = row.asDict()
    props = json.loads(r["properties"]) if r["properties"] else {}
    edges.append(GraphEdge(
        source_id=r["source_id"],
        target_id=r["target_id"],
        edge_type=EdgeType(r["edge_type"]),
        properties=props,
    ))

print(f"Loaded {len(nodes)} nodes, {len(edges)} edges from Delta")

# %% Cell 2: Build metric_logic table
traverser = GraphTraverser(nodes, edges)

# Get all canonical metrics
canonical_nodes = [n for n in nodes.values() if n.layer == NodeLayer.CANONICAL]
print(f"Found {len(canonical_nodes)} canonical metrics")

metric_logic_rows = []
for canonical in canonical_nodes:
    metric_id = canonical.node_id.replace("canonical:", "")
    subgraph = traverser.get_metric_subgraph(metric_id)
    if not subgraph:
        continue

    steward = canonical.properties.get("steward")
    developer = canonical.properties.get("developer")

    # Collect transformation logic
    transforms = subgraph.get("transformations", [])
    sql_fragments = []
    for t in transforms:
        frag = t.properties.get("sql_fragment", "")
        if frag:
            frag = normalize_sql_whitespace(frag)
            sql_fragments.append(f"-- {t.name}\n{frag}")

    combined_logic = "\n\n".join(sql_fragments) if sql_fragments else None

    # Collect source tables
    tech_nodes = subgraph.get("technical", [])
    tables = sorted(set(
        t.name for t in tech_nodes if t.properties.get("column") is None
    ))
    tables_str = ", ".join(tables) if tables else None

    # Collect table descriptions
    table_descs = []
    for t in tech_nodes:
        if t.properties.get("column") is None and t.description:
            table_descs.append(f"{t.name}: {t.description}")
    table_descs_str = "; ".join(table_descs) if table_descs else None

    metric_logic_rows.append((
        metric_id, canonical.name, canonical.description,
        steward, developer,
        len(transforms), combined_logic,
        tables_str, table_descs_str,
    ))

print(f"Built {len(metric_logic_rows)} metric logic rows")

# %% Cell 3: Save to Delta
from src.schemas import METRIC_LOGIC, to_spark_schema

ml_df = spark.createDataFrame(metric_logic_rows, schema=to_spark_schema(METRIC_LOGIC))
ml_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("metric_logic")
print(f"Saved {len(metric_logic_rows)} rows to metric_logic table")
print("→ Add 'metric_logic' as a data source in your Fabric Data Agent")

# %% Cell 4: Quick stats
with_logic = sum(1 for r in metric_logic_rows if r[6] is not None)  # combined_logic
with_tables = sum(1 for r in metric_logic_rows if r[7] is not None)  # tables_str
print(f"\nCoverage:")
print(f"  With calculation logic: {with_logic}/{len(metric_logic_rows)}")
print(f"  With source tables:     {with_tables}/{len(metric_logic_rows)}")
