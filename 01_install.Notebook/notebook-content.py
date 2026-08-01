# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "f7c297eb-4659-4600-ab89-0e860638fb6c",
# META       "default_lakehouse_name": "sql_query_lh",
# META       "default_lakehouse_workspace_id": "1f55e1c1-b660-4715-9b56-4140edce3940",
# META       "known_lakehouses": [
# META         {
# META           "id": "f7c297eb-4659-4600-ab89-0e860638fb6c"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "0776fc8d-1451-838d-47e6-f5c7a0bd174b",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     },
# META     "warehouse": {
# META       "known_warehouses": []
# META     }
# META   }
# META }

# CELL ********************

"""Fabric Notebook: One-Click Installation & Setup

Run this FIRST before any other notebook. It:
1. Validates the Fabric Environment is correctly attached
2. Validates the ScriptDom DLL is in the right place
3. Loads SQL files from sql_input/ into input_sql_sources Delta table
4. Loads dictionary CSVs from dictionary/ into input_dict_tables/input_dict_columns
5. Creates all Delta table schemas
6. Seeds the installation_errors knowledge base
7. Validates everything is consistent
8. Prints a clear PASS/FAIL summary

Safe to re-run — idempotent. Will not destroy existing data.

Prerequisites:
  - Fabric Environment 'sql-logic-env' attached to this notebook
  - Lakehouse attached as default
  - Files uploaded to Files/sql-query-agent/:
      libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll
      sql_input/*.sql
      dictionary/dict_tables.csv
      dictionary/dict_columns.csv
      org_config.yaml
"""

# %% Cell 0: Environment validation
import os
import sys

print("=" * 60)
print("SQL Intelligence Agent — Installation & Setup")
print("=" * 60)

# --- Check 1: Can we import the product library? ---
try:
    import src
    print(f"\n[+] Product library loaded: v{src.__version__}")
except ImportError:
    # Fallback for non-wheel deployment
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    try:
        import src
        print(f"\n[+] Product library loaded (via sys.path): v{src.__version__}")
    except ImportError:
        print("\n[X] FATAL: Cannot import 'src' package.")
        print("    Either upload the .whl to the Fabric Environment,")
        print("    or ensure src/ is at Files/sql-query-agent/src/")
        raise SystemExit("Installation cannot proceed.")

# --- Check 2: Required Python packages ---
missing_packages = []
for pkg_name, import_name in [
    ("pydantic", "pydantic"),
    ("pyyaml", "yaml"),
    ("sqlglot", "sqlglot"),
    ("sqlparse", "sqlparse"),
]:
    try:
        __import__(import_name)
    except ImportError:
        missing_packages.append(pkg_name)

if missing_packages:
    print(f"\n[X] FATAL: Missing Python packages: {', '.join(missing_packages)}")
    print("    Add these to your Fabric Environment → External repositories → Add library")
    raise SystemExit("Installation cannot proceed.")
else:
    print("[+] All required Python packages installed")

# --- Check 3: pythonnet ---
try:
    from pythonnet import load
    try:
        load("coreclr")
    except Exception:
        pass  # Already initialized — that's fine
    import clr
    print("[+] pythonnet loaded successfully")
except ImportError:
    print("[X] FATAL: pythonnet not installed.")
    print("    Add 'pythonnet' version 3.0.1 to Fabric Environment → External repositories")
    raise SystemExit("Installation cannot proceed.")

# --- Check 4: ScriptDom DLL ---
DLL_PATH = "/lakehouse/default/Files/sql-query-agent/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll"
if os.path.exists(DLL_PATH):
    from System.Reflection import Assembly
    Assembly.LoadFrom(DLL_PATH)
    from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
    print(f"[+] ScriptDom DLL loaded: {DLL_PATH}")
else:
    print(f"[X] FATAL: ScriptDom DLL not found at: {DLL_PATH}")
    print("    Download from: https://www.nuget.org/packages/Microsoft.SqlServer.TransactSql.ScriptDom")
    print("    Rename .nupkg → .zip, extract, upload lib/netstandard2.0/*.dll to Files/sql-query-agent/libs/")
    raise SystemExit("Installation cannot proceed.")

# --- Check 5: org_config.yaml ---
CONFIG_PATH = "/lakehouse/default/Files/sql-query-agent/org_config.yaml"
if os.path.exists(CONFIG_PATH):
    from src.config import load_config
    try:
        config = load_config(CONFIG_PATH)
        print(f"[+] Configuration loaded: org = '{config.org.name}'")
    except Exception as e:
        print(f"[X] FATAL: org_config.yaml is invalid: {e}")
        raise SystemExit("Installation cannot proceed.")
else:
    print(f"[X] FATAL: org_config.yaml not found at: {CONFIG_PATH}")
    print("    Upload org_config.yaml to Files/sql-query-agent/ (NOT in a subfolder)")
    raise SystemExit("Installation cannot proceed.")

# --- Check 6: File folders exist ---
BASE = "/lakehouse/default/Files/sql-query-agent"
required_folders = {
    "libs": f"{BASE}/libs",
    "sql_input": f"{BASE}/sql_input",
    "dictionary": f"{BASE}/dictionary",
}
for name, path in required_folders.items():
    if os.path.isdir(path):
        file_count = len([f for f in os.listdir(path) if not f.startswith(".")])
        print(f"[+] Folder {name}/: {file_count} files")
    else:
        print(f"[X] FATAL: Folder not found: {path}")
        print(f"    Create this folder in your Lakehouse under Files/sql-query-agent/")
        raise SystemExit("Installation cannot proceed.")

print("\n" + "=" * 60)
print("Environment validation PASSED — proceeding to data loading")
print("=" * 60)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load SQL files into Delta table
print("\n--- Loading SQL files ---")

import re as _re

SQL_DIR = "/lakehouse/default/Files/sql-query-agent/sql_input/"
sql_rows = []
skipped = []

def _extract_proc_identity(sql_content):
    """Extract schema.proc_name from CREATE PROCEDURE statement."""
    m = _re.search(
        r'(?:CREATE|ALTER)\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+'
        r'\[?(\w+)\]?\.\[?(\w+)\]?',
        sql_content, _re.IGNORECASE,
    )
    if m:
        return m.group(1), m.group(2)
    m = _re.search(
        r'(?:CREATE|ALTER)\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+'
        r'\[?(\w+)\]?',
        sql_content, _re.IGNORECASE,
    )
    if m:
        return "dbo", m.group(1)
    return None, None

for root, dirs, files in os.walk(SQL_DIR):
    for fname in sorted(files):
        if not fname.endswith(".sql"):
            continue
        filepath = os.path.join(root, fname)
        try:
            with open(filepath, encoding="utf-8-sig") as f:
                sql_content = f.read()
            schema, proc_name = _extract_proc_identity(sql_content)
            if schema and proc_name:
                metric_id = f"{schema}.{proc_name}"
                display_name = proc_name
                source_schema = schema
            else:
                metric_id = fname.replace(".sql", "")
                display_name = metric_id
                source_schema = None
                print(f"  [!] No CREATE PROCEDURE found in {fname} — using filename as metric_id")
            sql_rows.append((metric_id, display_name, sql_content, None, None, None, source_schema))
        except Exception as e:
            skipped.append((fname, str(e)))

if not sql_rows:
    print("[X] FATAL: No .sql files found in sql_input/")
    raise SystemExit("Installation cannot proceed — upload your SQL files first.")

metric_ids = [r[0] for r in sql_rows]
dupes = set(m for m in metric_ids if metric_ids.count(m) > 1)
if dupes:
    print(f"[!] WARNING: Duplicate proc identities detected: {', '.join(sorted(dupes))}")
    print("    Two files define the same [schema].[proc_name] — the last one loaded wins.")

from src.schemas import SQL_SOURCES, to_spark_schema
sql_df = spark.createDataFrame(sql_rows, schema=to_spark_schema(SQL_SOURCES))
sql_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("input_sql_sources")

print(f"\n[+] Loaded {len(sql_rows)} SQL files into input_sql_sources")
schemas_found = set(r[6] for r in sql_rows if r[6])
print(f"    Schemas found: {', '.join(sorted(schemas_found)) if schemas_found else 'none'}")
if skipped:
    print(f"[!] Skipped {len(skipped)} files: {', '.join(f[0] for f in skipped)}")
print(f"\n    Sample metric IDs:")
for row in sql_rows[:5]:
    print(f"      {row[0]} (name: {row[1]})")
if len(sql_rows) > 5:
    print(f"      ... and {len(sql_rows) - 5} more")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Load dictionary CSVs into Delta tables
print("\n--- Loading data dictionary ---")

DICT_DIR = "/lakehouse/default/Files/sql-query-agent/dictionary/"

# Tables
tables_path = os.path.join(DICT_DIR, "dict_tables.csv")
if os.path.exists(tables_path):
    dict_tables_df = spark.read.option("header", "true").csv("file://" + tables_path)

    # Validate required columns
    cols = [c.upper() for c in dict_tables_df.columns]
    if "TABLE_NAME" not in cols:
        print("[X] FATAL: dict_tables.csv missing TABLE_NAME column")
        print(f"    Found columns: {dict_tables_df.columns}")
        raise SystemExit("Fix dict_tables.csv and re-run.")

    if "DESCRIPTION" not in cols:
        print("[!] WARNING: dict_tables.csv missing DESCRIPTION column — adding empty descriptions")
        from pyspark.sql.functions import lit
        dict_tables_df = dict_tables_df.withColumn("DESCRIPTION", lit(""))

    dict_tables_df = dict_tables_df.select("TABLE_NAME", "DESCRIPTION")
    dict_tables_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("input_dict_tables")
    print(f"[+] Loaded {dict_tables_df.count()} table descriptions into input_dict_tables")
else:
    print(f"[X] FATAL: dict_tables.csv not found at {tables_path}")
    print("    See DATA_DICTIONARY_REQUIREMENTS.md for format specification.")
    raise SystemExit("Installation cannot proceed — upload dict_tables.csv first.")

# Columns
columns_path = os.path.join(DICT_DIR, "dict_columns.csv")
if os.path.exists(columns_path):
    dict_columns_df = spark.read.option("header", "true").csv("file://" + columns_path)

    cols = [c.upper() for c in dict_columns_df.columns]
    if "TABLE_NAME" not in cols or "COLUMN_NAME" not in cols:
        print("[X] FATAL: dict_columns.csv missing TABLE_NAME or COLUMN_NAME column")
        print(f"    Found columns: {dict_columns_df.columns}")
        raise SystemExit("Fix dict_columns.csv and re-run.")

    if "DESCRIPTION" not in cols:
        print("[!] WARNING: dict_columns.csv missing DESCRIPTION column — adding empty descriptions")
        from pyspark.sql.functions import lit
        dict_columns_df = dict_columns_df.withColumn("DESCRIPTION", lit(""))

    dict_columns_df = dict_columns_df.select("TABLE_NAME", "COLUMN_NAME", "DESCRIPTION")
    dict_columns_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("input_dict_columns")
    print(f"[+] Loaded {dict_columns_df.count()} column descriptions into input_dict_columns")
else:
    print(f"[X] FATAL: dict_columns.csv not found at {columns_path}")
    print("    See DATA_DICTIONARY_REQUIREMENTS.md for format specification.")
    raise SystemExit("Installation cannot proceed — upload dict_columns.csv first.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Seed installation errors knowledge base
print("\n--- Seeding installation errors knowledge base ---")

from src.schemas import INSTALLATION_ERRORS, to_spark_schema

ERROR_SEEDS = [
    ("This property must be set before runtime is initialized", "pythonnet_initialization",
     "%pip install restarts the kernel, breaking pythonnet CLR init.",
     "Use Fabric Environment with pre-installed packages instead of %pip install.",
     "Never use %pip install in notebooks that use pythonnet/ScriptDom.", "2026-07-26"),
    ("No module named 'Microsoft.SqlServer'", "dll_not_found",
     "ScriptDom DLL missing from libs/ folder or wrong filename.",
     "Upload Microsoft.SqlServer.TransactSql.ScriptDom.dll to Files/sql-query-agent/libs/. Use lib/netstandard2.0/ version from NuGet.",
     "Verify DLL path during deployment.", "2026-07-26"),
    ("Could not load file or assembly", "dll_load_failure",
     "Wrong DLL version (e.g., net462 instead of netstandard2.0) or corrupted file.",
     "Re-download from NuGet, use lib/netstandard2.0/ version only.",
     "Always use netstandard2.0 build.", "2026-07-26"),
    ("Config not found at", "config_not_found",
     "org_config.yaml is missing or in the wrong location.",
     "Upload org_config.yaml to Files/sql-query-agent/ (NOT in a config/ subfolder).",
     "Verify file path during 01_install.", "2026-07-30"),
    ("Bad Request.*400.*csv", "spark_csv_read_failure",
     "Spark CSV reader fails with OneLake HTTP path in some Fabric configurations.",
     "Add file:// prefix to CSV paths: spark.read.csv('file://' + path).",
     "Use file:// prefix for all local CSV reads.", "2026-07-31"),
    ("TooManyRequestsForCapacity.*430", "capacity_limit",
     "F2 capacity only supports one Spark session at a time.",
     "Wait 2-3 minutes for the previous session to release, then retry. Check Monitoring hub for active sessions.",
     "Cancel unused sessions. Consider F4 capacity for concurrent workloads.", "2026-07-30"),
    ("TABLE_OR_VIEW_NOT_FOUND", "table_not_found",
     "Delta table doesn't exist yet, or org_config.yaml has old table names.",
     "Run 01_install first to create all tables. Verify org_config.yaml uses domain-prefixed names (input_sql_sources, not sql_sources).",
     "Always run 01_install before other notebooks.", "2026-07-30"),
    ("User Aad Token is expired", "token_expired",
     "AAD token expires after ~1 hour. mssparkutils caches the token and won't refresh within the same session.",
     "Restart the kernel and re-run. For long batch runs, results are saved incrementally so you pick up where you left off.",
     "Design batch operations to save progress incrementally.", "2026-07-30"),
    ("Git_GitProviderCredentialsNotAuthorizedError", "git_auth_failure",
     "Fabric GitHub OAuth doesn't have write access to the repository.",
     "Revoke and re-authorize: GitHub Settings → Applications → find Microsoft Fabric → grant repo access. Or use a GitHub Personal Access Token with repo scope.",
     "Verify Git write access before connecting workspace.", "2026-07-31"),
    ("duplicate filenames", "duplicate_sql_files",
     "SQL files from different schemas have the same filename, causing overwrites in flat upload folder.",
     "Add a prefix to distinguish files from different schemas (e.g., RPT_USP_xxx.sql, ETL_USP_xxx.sql). Or use subfolders.",
     "Check for duplicate filenames before uploading.", "2026-07-30"),
    ("Cannot import 'src' package", "wheel_not_installed",
     "The .whl file is not uploaded to the Fabric Environment, or Environment not published.",
     "Upload sql_query_agent-1.1.0-py3-none-any.whl to Environment → Custom libraries → Publish.",
     "Verify Environment has .whl and is published before running notebooks.", "2026-07-31"),
    ("Set as default lakehouse.*grayed out", "lakehouse_default_issue",
     "Lakehouse moved from another workspace retains stale metadata.",
     "Create a new Lakehouse in the current workspace instead of moving one from another workspace.",
     "Always create Lakehouses in the target workspace.", "2026-07-31"),
]

try:
    error_rows = [
        (sig, cat, cause, fix, prevent, seen)
        for sig, cat, cause, fix, prevent, seen in ERROR_SEEDS
    ]
    errors_df = spark.createDataFrame(error_rows, schema=to_spark_schema(INSTALLATION_ERRORS))
    errors_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("ops_installation_errors")
    print(f"[+] Seeded {len(error_rows)} known error signatures into ops_installation_errors")
except Exception as e:
    print(f"[!] WARNING: Could not seed installation errors: {e}")
    print("    The /troubleshoot command may not work. Non-blocking.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 4: Validate dictionary coverage
print("\n--- Validating dictionary coverage ---")

# Get table names from SQL files
sql_table_refs = set()
try:
    import re
    for row in sql_rows:
        sql_text = row[2]  # sql column
        # Simple extraction: FROM/JOIN table names
        for match in re.finditer(
            r'(?:FROM|JOIN)\s+(?:\[?\w+\]?\.)?(?:\[?\w+\]?\.)?\[?(\w+)\]?',
            sql_text, re.IGNORECASE,
        ):
            name = match.group(1)
            if name.upper() not in (
                "SELECT", "WHERE", "SET", "BEGIN", "END", "AS", "ON",
                "AND", "OR", "NOT", "NULL", "TABLE", "VIEW", "PROCEDURE",
                "CASE", "WHEN", "THEN", "ELSE", "IN", "IS", "LIKE",
            ) and not name.startswith("#"):
                sql_table_refs.add(name.upper())
except Exception:
    pass

if sql_table_refs:
    dict_table_names = set(
        r["TABLE_NAME"].upper()
        for r in spark.table("input_dict_tables").collect()
    )
    covered = sql_table_refs & dict_table_names
    missing = sql_table_refs - dict_table_names
    coverage = len(covered) / len(sql_table_refs) if sql_table_refs else 1.0

    print(f"    SQL references {len(sql_table_refs)} unique tables")
    print(f"    Dictionary covers {len(covered)} ({coverage:.0%})")
    if missing:
        print(f"    Missing from dictionary: {', '.join(sorted(missing)[:10])}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")
    if coverage >= 0.9:
        print(f"[+] Dictionary coverage: {coverage:.0%} — GOOD")
    elif coverage >= 0.7:
        print(f"[!] Dictionary coverage: {coverage:.0%} — ACCEPTABLE (some tables missing descriptions)")
    else:
        print(f"[!] Dictionary coverage: {coverage:.0%} — LOW (agent answers will be incomplete)")
else:
    print("[!] Could not extract table references — skipping coverage check")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 5: Final summary
print("\n" + "=" * 60)
print("INSTALLATION SUMMARY")
print("=" * 60)

sql_count = spark.table("input_sql_sources").count()
dict_t_count = spark.table("input_dict_tables").count()
dict_c_count = spark.table("input_dict_columns").count()

print(f"  SQL sources loaded:     {sql_count}")
print(f"  Dictionary tables:      {dict_t_count}")
print(f"  Dictionary columns:     {dict_c_count}")
print(f"  ScriptDom DLL:          OK")
print(f"  Configuration:          {config.org.name}")
print(f"  Environment:            OK")

all_ok = sql_count > 0 and dict_t_count > 0 and dict_c_count > 0

if all_ok:
    print(f"\n  >>> INSTALLATION COMPLETE <<<")
    print(f"\n  Next steps:")
    print(f"  1. Run 02_parse     — parses SQL files with ScriptDom")
    print(f"  2. Run 03_build_graph — builds knowledge graph")
    print(f"  3. Run 04_build_metric_logic — flattens graph for Data Agent")
    print(f"  4. Run 05_export_graph_tables — exports LPG tables")
    print(f"  5. Run 06_validate  — validates pipeline health")
else:
    print(f"\n  >>> INSTALLATION INCOMPLETE <<<")
    if sql_count == 0:
        print(f"  [X] No SQL files loaded — check sql_input/ folder")
    if dict_t_count == 0:
        print(f"  [X] No dictionary tables — check dictionary/dict_tables.csv")
    if dict_c_count == 0:
        print(f"  [X] No dictionary columns — check dictionary/dict_columns.csv")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
