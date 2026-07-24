"""Fabric Notebook: Pipeline Setup

Run once per session. Installs dependencies, loads ScriptDom, and
defines shared helper functions used by all pipeline notebooks.

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
scriptdom_available = False
try:
    from pythonnet import load
    load("coreclr")

    import clr
    dll_path = "/lakehouse/default/Files/sql-query-agent/libs"
    if dll_path not in sys.path:
        sys.path.append(dll_path)

    clr.AddReference("Microsoft.SqlServer.TransactSql.ScriptDom")

    from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
    from System.IO import StringReader
    import re as _re

    def _walk_for_selects(node, queries):
        """Recursively walk the AST and collect SELECT/INSERT...SELECT nodes."""
        if node is None:
            return
        node_type = node.GetType().Name
        if node_type == "SelectStatement":
            sql = _get_fragment_text(node)
            if sql:
                queries.append(sql)
            return
        if node_type == "InsertStatement":
            spec = node.InsertSpecification
            if spec and spec.InsertSource and spec.InsertSource.GetType().Name == "SelectInsertSource":
                sql = _get_fragment_text(node)
                if sql:
                    queries.append(sql)
                return
        try:
            for prop in node.GetType().GetProperties():
                try:
                    value = prop.GetValue(node)
                    if value is None:
                        continue
                    if hasattr(value, "StartLine"):
                        _walk_for_selects(value, queries)
                    elif hasattr(value, "Count"):
                        for j in range(value.Count):
                            item = value[j]
                            if hasattr(item, "StartLine"):
                                _walk_for_selects(item, queries)
                except Exception:
                    continue
        except Exception:
            pass

    def _get_fragment_text(fragment):
        """Extract original SQL text from the token stream."""
        tokens = fragment.ScriptTokenStream
        if tokens is None:
            return ""
        start = fragment.FirstTokenIndex
        end = fragment.LastTokenIndex
        if start < 0 or end < 0:
            return ""
        parts = []
        for i in range(start, end + 1):
            if i < tokens.Count:
                parts.append(tokens[i].Text)
        return "".join(parts)

    def extract_with_scriptdom(raw_sql):
        """Parse T-SQL with ScriptDom and extract SELECT statements."""
        parser = TSql160Parser(True)
        reader = StringReader(raw_sql)
        parse_result = parser.Parse(reader, None)
        fragment = parse_result[0] if isinstance(parse_result, tuple) else parse_result
        queries = []
        _walk_for_selects(fragment, queries)
        cleaned = [_re.sub(r"@(\w+)", r"__param_\1__", q) for q in queries]
        return cleaned

    scriptdom_available = True
    print("ScriptDom loaded! (Microsoft's native T-SQL parser via pythonnet)")

except Exception as e:
    print(f"ScriptDom not available ({e}), falling back to sqlparse extractor")
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
