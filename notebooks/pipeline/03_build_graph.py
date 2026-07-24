"""Fabric Notebook: Build Knowledge Graph

Reads from: parse_results, sql_sources, dict_tables, dict_columns (Delta tables)
Writes to:  graph_nodes, graph_edges (Delta tables)

Prerequisite: Run 01_setup.py first (same session).
              Run 02_parse.py at least once (writes parse_results).

Rebuilds the three-layer graph from parse results and data dictionary.
Does NOT re-parse SQL — reads pre-parsed CTEs from parse_results table.
"""

# %% Cell 1: Load parse results from Delta
parse_results_df = spark.table("parse_results")
parse_results = [row.asDict() for row in parse_results_df.collect()]
print(f"Loaded {len(parse_results)} parse results")

# %% Cell 2: Load data dictionary
from src.dictionary import DataDictionary

dict_tables_df = read_source(config.lakehouse.dict_tables)
dict_columns_df = read_source(config.lakehouse.dict_columns)

table_id_col = config.dictionary.table_id_col
if table_id_col:
    print(f"Joining dict_columns on {table_id_col} to resolve table names...")
    table_name_col = config.dictionary.table_name_col
    tbl_lookup = dict_tables_df.select(table_id_col, table_name_col)
    dict_columns_df = dict_columns_df.join(tbl_lookup, on=table_id_col, how="left")

dict_tables = [row.asDict() for row in dict_tables_df.collect()]
dict_columns = [row.asDict() for row in dict_columns_df.collect()]
print(f"Loaded {len(dict_tables)} tables, {len(dict_columns)} columns from dictionary")

# %% Cell 3: Build graph
from src.graph.builder import GraphBuilder
from src.parser.sql_parser import ParsedSQL, CTEInfo

builder = GraphBuilder()

# Step 1: Technical nodes from dictionary
dictionary = DataDictionary()
table_name_col = config.dictionary.table_name_col
column_name_col = config.dictionary.column_name_col
description_col = config.dictionary.description_col
table_description_col = config.dictionary.table_description_col

for row in dict_tables:
    dictionary.add_table(row[table_name_col], row.get(table_description_col, ""))
for row in dict_columns:
    dictionary.add_column(row[table_name_col], row[column_name_col], row.get(description_col, ""))

for table_name, table_info in dictionary.tables.items():
    builder.add_technical_node(table_name, description=table_info.description)
    for col_info in dictionary.get_columns_for_table(table_name):
        builder.add_technical_node(table_name, col_info.column_name, description=col_info.description)

print(f"Created {len(builder.nodes)} technical nodes from dictionary")

# Step 2: Canonical + transformation nodes from parse results
for pr in parse_results:
    metric_id = pr["metric_id"]
    name = pr["name"]

    builder.add_canonical_node(metric_id, name)

    # Reconstruct ParsedSQL from stored JSON
    ctes = []
    for c in json.loads(pr["ctes_json"]):
        ctes.append(CTEInfo(
            name=c["name"],
            sql_fragment=c["sql_fragment"],
            table_refs=c["table_refs"],
            depends_on=c["depends_on"],
        ))

    parsed = ParsedSQL(
        ctes=ctes,
        final_select_tables=json.loads(pr["final_select_tables"]),
        final_select_cte_refs=json.loads(pr["final_select_cte_refs"]),
    )

    builder.build_from_parsed_sql(metric_id, parsed)

print(f"Built graph: {len(builder.nodes)} nodes, {len(builder.edges)} edges")

# %% Cell 4: Write graph to Delta
from src.schemas import GRAPH_NODES, GRAPH_EDGES, to_spark_schema

nodes_rows = [
    (n.node_id, n.layer.value, n.name, n.description, json.dumps(n.properties))
    for n in builder.nodes.values()
]
edges_rows = [
    (e.source_id, e.target_id, e.edge_type.value, json.dumps(e.properties))
    for e in builder.edges
]

nodes_df = spark.createDataFrame(nodes_rows, schema=to_spark_schema(GRAPH_NODES))
edges_df = spark.createDataFrame(edges_rows, schema=to_spark_schema(GRAPH_EDGES))

def write_table(df, name):
    if "/" in name:
        df.write.format("delta").mode("overwrite").save(name)
    else:
        df.write.format("delta").mode("overwrite").saveAsTable(name)

write_table(nodes_df, config.lakehouse.graph_nodes)
write_table(edges_df, config.lakehouse.graph_edges)

print(f"Wrote {nodes_df.count()} nodes to {config.lakehouse.graph_nodes}")
print(f"Wrote {edges_df.count()} edges to {config.lakehouse.graph_edges}")

# %% Cell 5: Quick traversal test
from src.graph.traversal import GraphTraverser

traverser = GraphTraverser(builder.nodes, builder.edges)

print("\n=== Traversal Test (first 5) ===")
for pr in parse_results[:5]:
    metric_id = pr["metric_id"]
    subgraph = traverser.get_metric_subgraph(metric_id)
    if subgraph:
        canonical = subgraph["canonical"]
        tables = [t.name for t in subgraph["technical"] if t.properties.get("column") is None]
        print(f"\n{canonical.name} ({metric_id})")
        print(f"  Transforms: {len(subgraph['transformations'])}")
        print(f"  Tables: {len(tables)} — {tables[:5]}{'...' if len(tables) > 5 else ''}")
    else:
        print(f"\n{metric_id} — no graph path found")

print("\n→ Next: run 04_build_metric_logic.py")
