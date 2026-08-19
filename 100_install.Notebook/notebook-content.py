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

"""Fabric Notebook: Installation Verification

Run FIRST on a new install and any time state is unclear. It verifies
the ENVIRONMENT (library, packages, pythonnet, ScriptDom DLL, config),
seeds the error knowledge base, then reports INGESTION STATE from the
tables themselves — which acquisition routes (00a-00e) have satisfied
their contracts and which still need running. It never assumes a route
and never loads data itself (that is what the 00-family routes do).

Safe to re-run — idempotent, read-only except the error seed.
"""

# %% Cell 0: Environment verification (route-independent)
import os
import sys

print("=" * 60)
print("Installation Verification")
print("=" * 60)

# --- Check 1: product library ---
try:
    import src
    print(f"\n[+] Product library loaded: v{src.__version__}")
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    try:
        import src
        print(f"\n[+] Product library loaded (via sys.path): v{src.__version__}")
    except ImportError:
        print("\n[X] FATAL: Cannot import 'src' package.")
        print("    Either upload the .whl to the Fabric Environment,")
        print("    or ensure src/ is at Files/sql-query-agent/src/")
        raise SystemExit("Verification cannot proceed.")

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.24"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "100_install")

# --- Check 2: required Python packages ---
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
    print("    Add these to your Fabric Environment -> External repositories -> Add library")
    raise SystemExit("Verification cannot proceed.")
print("[+] All required Python packages installed")

# --- Check 3: pythonnet ---
try:
    from pythonnet import load
    try:
        load("coreclr")
    except Exception:  # noqa: BLE001, S110 — idempotent init: already-loaded runtime throws, which is fine
        pass
    import clr  # noqa: F401 — probe: importing proves pythonnet + CLR are usable
    print("[+] pythonnet loaded successfully")
except ImportError:
    print("[X] FATAL: pythonnet not installed.")
    print("    Add 'pythonnet' version 3.0.1 to Fabric Environment -> External repositories")
    raise SystemExit("Verification cannot proceed.")

# --- Check 4: ScriptDom DLL ---
DLL_PATH = "/lakehouse/default/Files/sql-query-agent/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll"
if os.path.exists(DLL_PATH):
    from System.Reflection import Assembly
    Assembly.LoadFrom(DLL_PATH)
    print(f"[+] ScriptDom DLL loaded: {DLL_PATH}")
else:
    print(f"[X] FATAL: ScriptDom DLL not found at: {DLL_PATH}")
    print("    Download from: https://www.nuget.org/packages/Microsoft.SqlServer.TransactSql.ScriptDom")
    print("    Rename .nupkg -> .zip, extract, upload lib/netstandard2.0/*.dll to Files/sql-query-agent/libs/")
    raise SystemExit("Verification cannot proceed.")

# --- Check 5: org_config.yaml ---
CONFIG_PATH = "/lakehouse/default/Files/sql-query-agent/org_config.yaml"
if os.path.exists(CONFIG_PATH):
    from src.config import load_config
    try:
        config = load_config(CONFIG_PATH)
        print(f"[+] Configuration loaded: org = '{config.org.name}'")
    except Exception as e:  # noqa: BLE001 — any config defect is FATAL with the message
        print(f"[X] FATAL: org_config.yaml is invalid: {e}")
        raise SystemExit("Verification cannot proceed.")
else:
    print(f"[X] FATAL: org_config.yaml not found at: {CONFIG_PATH}")
    print("    Upload org_config.yaml to Files/sql-query-agent/ (NOT in a subfolder)")
    raise SystemExit("Verification cannot proceed.")

# --- Check 6: folders (INFORMATIONAL — folders belong to specific routes) ---
BASE = "/lakehouse/default/Files/sql-query-agent"
for name, route in [("sql_input", "route 00a"), ("dictionary", "route 00d Cell 1")]:
    path = f"{BASE}/{name}"
    if os.path.isdir(path):
        file_count = len([f for f in os.listdir(path) if not f.startswith(".")])
        print(f"[+] Folder {name}/: {file_count} files (used by {route})")
    else:
        print(f"[i] Folder {name}/ absent — only needed for {route}")

print("\n[+] Environment verification PASSED")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Seed installation errors knowledge base (route-independent)
from src.governance.installation_errors import ERROR_SEEDS
from src.schemas import INSTALLATION_ERRORS, to_spark_schema

try:
    errors_df = spark.createDataFrame(ERROR_SEEDS, schema=to_spark_schema(INSTALLATION_ERRORS))
    errors_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("ops_installation_errors")
    print(f"[+] Seeded {len(ERROR_SEEDS)} known error signatures into ops_installation_errors")
except Exception as e:  # noqa: BLE001 — degraded /troubleshoot only; consequence stated
    print(f"[!] WARNING: Could not seed installation errors: {e}")
    print("    The /troubleshoot command may not work. Non-blocking.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Ingestion state report — from the tables, never from memory
print("\n" + "=" * 60)
print("INGESTION STATE (state-driven, like the gates)")
print("=" * 60)

ROUTES = {
    "input_sql_sources": "010_ingest_sql_filedrop | 020_ingest_sql_folders | 030_ingest_sql_live",
    "input_dict_tables": "040_dict_clarity (then optionally 050_dict_caboodle)",
    "input_dict_columns": "040_dict_clarity (then optionally 050_dict_caboodle)",
}

state = {}
for table, routes in ROUTES.items():
    if spark.catalog.tableExists(table):
        n = spark.table(table).count()
        state[table] = n
        mark = "+" if n > 0 else "!"
        print(f"  [{mark}] {table}: present ({n} rows)")
    else:
        state[table] = None
        print(f"  [!] {table}: ABSENT — run one of: {routes}")

# Coverage preview only when both halves of a source pair are present.
# (Rough regex preview; 500_validate's dictionary_coverage is the
# authoritative, blocking check.)
if state.get("input_sql_sources") and state.get("input_dict_tables"):
    from src.dictionary import preview_table_references
    try:
        sql_table_refs = preview_table_references(
            [row["sql"] for row in
             spark.table("input_sql_sources").select("sql").collect()]
        )
        dict_table_names = set(
            r["TABLE_NAME"].upper() for r in spark.table("input_dict_tables").collect()
        )
        if sql_table_refs:
            covered = sql_table_refs & dict_table_names
            coverage = len(covered) / len(sql_table_refs)
            print(f"\n  Dictionary coverage preview: {coverage:.0%} "
                  f"({len(covered)}/{len(sql_table_refs)} referenced tables)")
            missing = sorted(sql_table_refs - dict_table_names)
            if missing:
                print(f"  Missing from dictionary: {', '.join(missing[:10])}"
                      + (f" ... and {len(missing) - 10} more" if len(missing) > 10 else ""))
    except Exception as e:  # noqa: BLE001 — preview only; 500 runs the authoritative gate
        print(f"  [!] coverage preview failed ({e}) — 500_validate runs the authoritative gate")

all_present = all(v for v in state.values())
print("\n" + "=" * 60)
if all_present:
    print(">>> VERIFIED — ingestion satisfied. Next: 200 -> 300 -> 400 -> 500 (then 600s, 700, 800, 900s) <<<")
else:
    print(">>> VERIFIED (environment) — ingestion PENDING <<<")
    print("Remember: a source system enters as a PAIR (its SQL and its")
    print("dictionary together), or 06's coverage gate will block.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
