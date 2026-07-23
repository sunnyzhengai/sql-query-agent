"""Fabric Notebook: Debug a specific metric's edges and traversal

Change METRIC_NAME and run. Reads from Delta tables only.
"""

# %% Cell 1: Set the metric to investigate
METRIC_NAME = "REPLACE_WITH_METRIC_NAME"

# %% Cell 2: Check if canonical node exists
print(f"=== Investigating: {METRIC_NAME} ===\n")

spark.sql(f"""
    SELECT node_id, name, description, SUBSTRING(properties, 1, 200) as props
    FROM graph_nodes
    WHERE node_id = 'canonical:{METRIC_NAME}'
""").show(truncate=100)

# %% Cell 3: Check edges FROM this canonical node
print("Edges FROM canonical node:")
spark.sql(f"""
    SELECT source_id, target_id, edge_type
    FROM graph_edges
    WHERE source_id = 'canonical:{METRIC_NAME}'
""").show(truncate=80)

# %% Cell 4: Check ALL edges mentioning this metric
print("ALL edges mentioning this metric:")
spark.sql(f"""
    SELECT source_id, target_id, edge_type
    FROM graph_edges
    WHERE source_id LIKE '%{METRIC_NAME}%'
       OR target_id LIKE '%{METRIC_NAME}%'
""").show(20, truncate=80)

# %% Cell 5: Check transform nodes for this metric
print("Transform nodes:")
spark.sql(f"""
    SELECT node_id, name, SUBSTRING(properties, 1, 200) as props
    FROM graph_nodes
    WHERE node_id LIKE 'transform:{METRIC_NAME}%'
""").show(truncate=100)

# %% Cell 6: Check parse results
print("Parse result:")
spark.sql(f"""
    SELECT metric_id, cte_count, table_count, line_count
    FROM parse_successes
    WHERE metric_id = '{METRIC_NAME}'
""").show()

spark.sql(f"""
    SELECT metric_id, error
    FROM parse_errors
    WHERE metric_id = '{METRIC_NAME}'
""").show(truncate=200)
