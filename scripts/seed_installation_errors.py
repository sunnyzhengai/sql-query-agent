"""Seed the installation_errors Delta table with known error signatures.

Run this in a Fabric notebook to populate the error knowledge base.
The Fabric Data Agent can then answer "why am I getting this error?"
by querying this table.

Usage in Fabric:
    Copy and paste into a notebook cell, or run via:
    %run scripts/seed_installation_errors
"""

INSTALLATION_ERRORS = [
    {
        "error_signature": "This property must be set before runtime is initialized",
        "error_category": "pythonnet_initialization",
        "root_cause": "%pip install restarts the Fabric notebook kernel. After restart, PySpark's .NET bridge initializes before pythonnet can call load('coreclr'). Once the .NET runtime is initialized, pythonnet cannot re-configure it.",
        "fix": "Use a Fabric Environment with pre-installed packages instead of %pip install. See environment/README.md for setup. If you must use %pip, run it in a separate notebook, close it, then open your pipeline notebook in a fresh session.",
        "prevention": "Never use %pip install in notebooks that use pythonnet/ScriptDom. Always use Fabric Environments for dependency management.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "No module named 'Microsoft.SqlServer'",
        "error_category": "dll_not_found",
        "root_cause": "The ScriptDom DLL file is missing from the libs/ folder, has the wrong filename (e.g., double dot: '.dll' vs '..dll'), or the path in the notebook doesn't match the actual file location.",
        "fix": "1. Verify the DLL exists: check Files/sql-query-agent/libs/ in your Lakehouse. 2. Verify the filename is exactly 'Microsoft.SqlServer.TransactSql.ScriptDom.dll' (no double dots). 3. If missing, download from NuGet, rename .nupkg to .zip, extract lib/netstandard2.0/Microsoft.SqlServer.TransactSql.ScriptDom.dll.",
        "prevention": "Include DLL verification in the deployment checklist. Run the validate_deployment script before first pipeline execution.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "Could not load file or assembly 'Microsoft.SqlServer.TransactSql.ScriptDom, Culture=neutral, PublicKeyToken=null'",
        "error_category": "dll_not_found",
        "root_cause": "clr.AddReference() uses assembly name lookup which fails after kernel restart. The DLL path is not in sys.path or the assembly resolver can't find it.",
        "fix": "Use the full file path instead of assembly name: clr.AddReference('/full/path/to/Microsoft.SqlServer.TransactSql.ScriptDom.dll'). The load_scriptdom() function in scriptdom_fabric.py handles this automatically.",
        "prevention": "Always use Fabric Environment. The load_scriptdom() function tries full file path first, assembly name as fallback.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "Object of type TableRef is not JSON serializable",
        "error_category": "version_mismatch",
        "root_cause": "The notebook code expects plain strings for table references but the src/ library returns TableRef objects (introduced in v1.1.0). The notebook and src/ library are different versions.",
        "fix": "Re-upload the entire src/ folder and notebooks/pipeline/ folder from the latest release. Ensure the notebook's parse_results serialization converts TableRef to dict before json.dumps().",
        "prevention": "Always deploy src/ and notebooks/ together as a matched set. Use version check: import src; assert src.__version__ == '1.1.0'",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "Error tokenizing",
        "error_category": "sql_parsing",
        "root_cause": "sqlglot's tokenizer cannot handle certain T-SQL syntax. Common triggers: long IN(...) lists with inline comments, non-breaking spaces (\\xa0), \\r\\r\\n line endings from Windows SQL files.",
        "fix": "This is resolved in v1.1.0 which uses ScriptDom (Option B) instead of sqlglot for T-SQL parsing. If you see this error, ensure ScriptDom is loaded (check Cell 0 output for 'ScriptDom loaded!').",
        "prevention": "Use ScriptDom (Option B) for all T-SQL parsing. sqlglot is only a fallback for non-Fabric environments.",
        "first_seen": "2026-07-23",
    },
    {
        "error_signature": "no SELECT statements",
        "error_category": "sql_parsing",
        "root_cause": "The SQL file contains no SELECT queries. Common causes: the file is a utility procedure (INSERT/UPDATE/DELETE only), an EXEC wrapper, DDL-only, or the file is corrupted/empty.",
        "fix": "Check the parse_errors table — the user_explanation column describes why in plain English. These procedures are not report sources and can be excluded from the knowledge graph.",
        "prevention": "Expected behavior for non-report procedures. The error classifier categorizes these as 'no_query' with appropriate user explanations.",
        "first_seen": "2026-07-24",
    },
    {
        "error_signature": "no documented calculation logic",
        "error_category": "agent_response",
        "root_cause": "The Data Agent finds the metric in the graph but cannot find its calculation logic. Root causes: 1) metric_logic table not added as agent data source, 2) stale data from a previous pipeline run, 3) hardcoded examples in agent instructions causing pattern matching instead of data queries.",
        "fix": "1. Verify metric_logic is listed as a data source in the Data Agent configuration. 2. Rerun the pipeline (02→03→04) to refresh data. 3. Ensure agent instructions do not contain hardcoded metric-specific examples.",
        "prevention": "Never hardcode metric-specific translations in agent instructions. Always add metric_logic as the primary data source.",
        "first_seen": "2026-07-23",
    },
    {
        "error_signature": "ScriptDom not available, using sqlparse",
        "error_category": "pythonnet_initialization",
        "root_cause": "pythonnet failed to load, falling back to sqlparse extractor. This results in ~50% parse rate instead of 99%+. Usually caused by %pip install restarting the kernel.",
        "fix": "Use Fabric Environment instead of %pip install. Stop the session, attach the sql-logic-env Environment, and rerun the notebook.",
        "prevention": "Never use %pip install in pipeline notebooks. Use Fabric Environments exclusively.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "Warning: PySpark kernel has been restarted",
        "error_category": "pythonnet_initialization",
        "root_cause": "%pip installed new package versions, triggering a kernel restart. Any code after %pip in the same cell ran before the restart, setting incorrect state.",
        "fix": "If you must use %pip, put it alone in its own cell with nothing else. Run the next cell after the restart completes. Better: use Fabric Environment.",
        "prevention": "Pin exact dependency versions in %pip to prevent unnecessary installs. Best: use Fabric Environment.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "\\\\r\\\\n|\\\\r\\\\r\\\\n|\\\\xa0",
        "error_category": "sql_parsing",
        "root_cause": "SQL files from Windows (SSMS) contain \\r\\n or \\r\\r\\n line endings and \\xa0 non-breaking spaces. These break comment stripping and sqlglot tokenization.",
        "fix": "Resolved automatically by normalize_sql_whitespace() which runs at the entry point of parse_extracted_queries(). All Unicode whitespace variants are handled.",
        "prevention": "Automatic — the normalization gate handles all known whitespace variants including BOM, zero-width spaces, vertical tabs, and form feeds.",
        "first_seen": "2026-07-23",
    },
    {
        "error_signature": "Schema mismatch|overwriteSchema",
        "error_category": "delta_table",
        "root_cause": "A pipeline notebook is writing to a Delta table that has a different schema than expected. This happens when the table was created by an older version of the code with fewer columns.",
        "fix": "Add .option('overwriteSchema', 'true') to the Delta write operation. The pipeline notebooks already include this for tables that may change schema across versions.",
        "prevention": "Always use centralized schemas from src/schemas.py. Use to_spark_schema() for DataFrame creation.",
        "first_seen": "2026-07-23",
    },
    {
        "error_signature": "No module named 'src'",
        "error_category": "path_configuration",
        "root_cause": "sys.path does not include the sql-query-agent directory. The notebook cannot find the src/ package.",
        "fix": "Add this line before any src imports: sys.path.insert(0, '/lakehouse/default/Files/sql-query-agent'). Verify the sql-query-agent folder exists in your Lakehouse Files.",
        "prevention": "Every notebook Cell 0 includes the sys.path.insert line. Verify the folder path matches your Lakehouse structure.",
        "first_seen": "2026-07-24",
    },
]


def seed_to_delta(spark):
    """Write installation errors to Delta table. Call from a Fabric notebook."""
    from src.schemas import INSTALLATION_ERRORS, to_spark_schema
    schema = to_spark_schema(INSTALLATION_ERRORS)
    rows = [(e["error_signature"], e["error_category"], e["root_cause"],
             e["fix"], e["prevention"], e["first_seen"])
            for e in INSTALLATION_ERRORS]
    df = spark.createDataFrame(rows, schema=schema)
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("ops_installation_errors")
    print(f"Seeded {len(rows)} installation errors to 'installation_errors' table")


if __name__ == "__main__":
    # Print as readable text when run locally
    for e in INSTALLATION_ERRORS:
        print(f"\n{'=' * 60}")
        print(f"Error: {e['error_signature'][:80]}")
        print(f"Category: {e['error_category']}")
        print(f"Root cause: {e['root_cause'][:200]}")
        print(f"Fix: {e['fix'][:200]}")
        print(f"Prevention: {e['prevention'][:200]}")
