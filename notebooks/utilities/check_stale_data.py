# Paste as a cell in any notebook after setup (tables: output_metric_logic, graph_nodes)
# Checks if census reports have stale data from earlier runs

# Check if census reports have descriptions that other metrics don't
spark.sql("""
    SELECT metric_id, metric_name,
           LENGTH(description) as desc_len,
           LENGTH(calculation_logic) as logic_len,
           source_tables
    FROM output_metric_logic
    WHERE metric_name LIKE '%Census%'
""").show(truncate=100)

# Compare with a metric you know fails
spark.sql("""
    SELECT metric_id, metric_name,
           LENGTH(description) as desc_len,
           LENGTH(calculation_logic) as logic_len,
           source_tables
    FROM output_metric_logic
    WHERE metric_name LIKE '%ED_CHART%'
""").show(truncate=100)

# Check graph_nodes for descriptions
spark.sql("""
    SELECT node_id, description, SUBSTRING(properties, 1, 100) as props
    FROM graph_nodes
    WHERE layer = 'canonical'
    AND (name LIKE '%Census%' OR name LIKE '%ED_CHART%')
""").show(truncate=100)
