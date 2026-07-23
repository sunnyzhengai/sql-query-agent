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

# %% Cell 7: Check if sql_fragment is actually populated in transform nodes
# This is what the agent needs to answer "how is X calculated?"
print("=== sql_fragment check ===")
spark.sql(f"""
    SELECT
        node_id,
        name,
        LENGTH(properties) as props_len,
        LENGTH(get_json_object(properties, '$.sql_fragment')) as fragment_len,
        SUBSTRING(get_json_object(properties, '$.sql_fragment'), 1, 100) as fragment_preview
    FROM graph_nodes
    WHERE node_id LIKE 'transform:{METRIC_NAME}%'
""").show(truncate=120)

# %% Cell 8: Simulate the exact query the agent would need to run
# This is the multi-hop traversal: canonical → edges → transform nodes → properties JSON
print("=== Agent simulation: full traversal ===")
spark.sql(f"""
    SELECT
        n.node_id,
        n.name as transform_name,
        e.edge_type,
        SUBSTRING(get_json_object(n.properties, '$.sql_fragment'), 1, 200) as sql_logic
    FROM graph_edges e
    JOIN graph_nodes n ON e.target_id = n.node_id
    WHERE e.source_id = 'canonical:{METRIC_NAME}'
    AND e.edge_type = 'canonical_to_transform'
""").show(truncate=120)

# %% Cell 9: Compare working vs non-working metric
# Run this with a metric that WORKS in the agent, then one that DOESN'T
# Look for differences in: fragment_len, edge count, node structure
print("=== Quick comparison stats ===")
spark.sql(f"""
    SELECT
        '{METRIC_NAME}' as metric,
        (SELECT COUNT(*) FROM graph_edges WHERE source_id = 'canonical:{METRIC_NAME}') as edge_count,
        (SELECT COUNT(*) FROM graph_nodes WHERE node_id LIKE 'transform:{METRIC_NAME}%') as transform_count,
        (SELECT COUNT(*) FROM graph_nodes WHERE node_id LIKE 'transform:{METRIC_NAME}%'
         AND get_json_object(properties, '$.sql_fragment') IS NOT NULL
         AND LENGTH(get_json_object(properties, '$.sql_fragment')) > 0) as transforms_with_sql,
        (SELECT COUNT(*) FROM graph_nodes WHERE node_id LIKE 'transform:{METRIC_NAME}%'
         AND (get_json_object(properties, '$.sql_fragment') IS NULL
              OR LENGTH(get_json_object(properties, '$.sql_fragment')) = 0)) as transforms_empty_sql
"""
).show()
