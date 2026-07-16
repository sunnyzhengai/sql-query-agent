"""Fabric Notebook orchestrator stub.

In Fabric, this would be a .ipynb notebook. Kept as .py for version control.
The Fabric Notebook is the orchestrator only — the library does the heavy lifting.

Usage in Fabric Notebook:
    %run orchestrator.py
"""

# %% Cell 1: Setup
# import sys
# sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
# from src.config import load_config
# from src.graph.builder import GraphBuilder
# from src.parser.sql_parser import parse_sql
# from src.dictionary import DataDictionary

# %% Cell 2: Load config
# config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# %% Cell 3: Load data dictionary from Delta tables
# dict_tables_df = spark.read.format("delta").load(config.lakehouse.dict_tables)
# dict_columns_df = spark.read.format("delta").load(config.lakehouse.dict_columns)

# %% Cell 4: Load SQL sources
# sql_sources_df = spark.read.format("delta").load(config.lakehouse.sql_sources)

# %% Cell 5: Build graph
# builder = GraphBuilder()
# # ... populate from DataFrames ...

# %% Cell 6: Write graph to Delta
# # Convert builder.nodes / builder.edges to DataFrames and write to Delta
