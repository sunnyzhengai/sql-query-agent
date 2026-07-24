"""Fabric Notebook: Pipeline Setup

Run once per session. Installs dependencies, loads ScriptDom, and
sets up shared variables used by all pipeline notebooks.

After running this, run any of the other pipeline notebooks:
- 02_parse.py — extract and parse SQL sources
- 03_build_graph.py — build graph from parse results + dictionary
- 04_build_metric_logic.py — flatten graph for the Data Agent
- 05_validate.py — validate pipeline health

Each notebook reads from and writes to Delta tables, so you only
need to rerun the stage that changed.
"""

# %% Cell 1: Install dependencies
%pip install pydantic pyyaml sqlglot sqlparse pythonnet

# %% Cell 2: Setup paths and imports
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.schemas import to_spark_schema

# %% Cell 3: Load config
config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
print(f"Loaded config for: {config.org.name}")

# %% Cell 4: Load ScriptDom parser
from src.parser.scriptdom_fabric import load_scriptdom

scriptdom_available, extract_with_scriptdom = load_scriptdom()

if scriptdom_available:
    print("ScriptDom loaded! (Microsoft's native T-SQL parser via pythonnet)")
else:
    print("ScriptDom not available, falling back to sqlparse extractor")
    from src.parser.sql_extractor import extract_select_statements

# %% Cell 5: Shared helper
def read_source(name_or_path):
    """Read a data source by name or path. Auto-detects format."""
    if name_or_path.endswith(".csv"):
        return spark.read.option("header", "true").option("inferSchema", "true").csv(name_or_path)
    elif "abfss://" in name_or_path or "/" in name_or_path:
        return spark.read.format("delta").load(name_or_path)
    else:
        return spark.table(name_or_path)

print("\n=== Setup Complete ===")
print("Run the pipeline notebooks in order, or rerun only the stage that changed.")
print("  02_parse.py      — extract and parse SQL")
print("  03_build_graph.py — build knowledge graph")
print("  04_build_metric_logic.py — flatten for agent")
print("  05_validate.py   — pipeline health check")
