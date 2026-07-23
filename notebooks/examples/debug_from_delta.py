"""Fabric Notebook: Debug edges and traversal from Delta tables

No dependency on orchestrator session — reads everything from Delta tables.
Run anytime after orchestrator has completed.
"""

# %% Cell 1: Edge counts by type
print("=== Edge Analysis ===\n")
edges_df = spark.table("graph_edges")
print("Edges by type:")
edges_df.groupBy("edge_type").count().orderBy("edge_type").show()
print(f"Total edges: {edges_df.count()}")

# %% Cell 2: Canonical node coverage
nodes_df = spark.table("graph_nodes")

canonical_count = nodes_df.filter("layer = 'canonical'").count()
canonical_with_edges = edges_df.filter("edge_type = 'canonical_to_transform'").select("source_id").distinct().count()
transform_count = nodes_df.filter("layer = 'transformation'").count()
technical_count = nodes_df.filter("layer = 'technical'").count()

print(f"Canonical nodes: {canonical_count}")
print(f"Canonical WITH edges: {canonical_with_edges}")
print(f"Canonical WITHOUT edges: {canonical_count - canonical_with_edges}")
print(f"Transform nodes: {transform_count}")
print(f"Technical nodes: {technical_count}")

# %% Cell 3: Sample edges
print("\n=== Sample Edges ===")
edges_df.show(10, truncate=80)

# %% Cell 4: Sample canonical nodes with edges
print("\n=== Canonical Nodes WITH Edges ===")
spark.sql("""
    SELECT e.source_id, e.target_id, e.edge_type
    FROM graph_edges e
    WHERE e.edge_type = 'canonical_to_transform'
    LIMIT 10
""").show(truncate=80)

# %% Cell 5: Sample canonical nodes WITHOUT edges
print("\n=== Canonical Nodes WITHOUT Edges ===")
spark.sql("""
    SELECT n.node_id, n.name
    FROM graph_nodes n
    WHERE n.layer = 'canonical'
    AND n.node_id NOT IN (
        SELECT source_id FROM graph_edges WHERE edge_type = 'canonical_to_transform'
    )
    LIMIT 10
""").show(truncate=80)

# %% Cell 6: Parse errors
print("\n=== Parse Errors ===")
spark.sql("""
    SELECT metric_id, SUBSTRING(error, 1, 120) as error_preview
    FROM parse_errors
    ORDER BY metric_id
""").show(50, truncate=120)

# %% Cell 7: Parse successes — check if they have edges
print("\n=== Parsed OK but No Edges? ===")
spark.sql("""
    SELECT s.metric_id, s.cte_count, s.table_count
    FROM parse_successes s
    WHERE CONCAT('canonical:', s.metric_id) NOT IN (
        SELECT source_id FROM graph_edges WHERE edge_type = 'canonical_to_transform'
    )
    LIMIT 10
""").show(truncate=80)
