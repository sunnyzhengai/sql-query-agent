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
# META     }
# META   }
# META }

# CELL ********************

"""Fabric Notebook: Ingest PBI Semantic Models (ADR 0040)

Parses TMDL semantic-model definitions into three input tables:
  input_report_sources  — report -> SQL object partition lineage
  input_dax_expressions — DAX measures + calculated columns
  input_metric_names    — business names derived from report lineage

Reads from: a semantic_models source profile (folder or devops_git)
Writes to:  input_report_sources, input_dax_expressions, input_metric_names

Run BEFORE 03_build_graph so the consumption layer lands in the graph.
"""

# %% Cell 0: Setup
import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from src.config import load_config

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

if config.semantic_models is None:
    raise ValueError(
        "No 'semantic_models' section in org_config.yaml — add one with "
        "source_type folder (git-synced workspace / uploaded Files) or "
        "devops_git. See org_config.example.yaml."
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Collect TMDL files via the configured source profile
from src.extractor.tmdl_source import (
    FabricWorkspaceTmdlSource,
    FolderTmdlSource,
    collect_from_devops,
)

sm = config.semantic_models
if sm.source_type == "workspace":
    # Turn-key default: straight from the Fabric workspace REST API —
    # works whether or not the workspace has git integration.
    workspace_id = sm.workspace_id or notebookutils.runtime.context.get(  # noqa: F821
        "currentWorkspaceId")
    tmdl_files = FabricWorkspaceTmdlSource(
        workspace_id,
        token_provider=lambda: notebookutils.credentials.getToken(  # noqa: F821
            "https://api.fabric.microsoft.com"),
    ).collect()
elif sm.source_type == "folder":
    if not sm.folder_path:
        raise ValueError("semantic_models.folder_path is required for the folder profile")
    tmdl_files = FolderTmdlSource(sm.folder_path).collect()
else:  # devops_git
    if sm.devops is None:
        raise ValueError("semantic_models.devops section is required for the devops_git profile")
    if not (sm.devops.key_vault_url and sm.devops.pat_secret_name):
        raise ValueError(
            "devops_git requires key_vault_url + pat_secret_name — the PAT "
            "is fetched from Key Vault at run time, never stored in config"
        )
    from src.extractor.devops_tmdl import DevOpsTmdlClient

    # Fetched fresh each run; PAT never lands in config, code, or git.
    pat = notebookutils.credentials.getSecret(  # noqa: F821
        sm.devops.key_vault_url, sm.devops.pat_secret_name
    )
    client = DevOpsTmdlClient(sm.devops.org, sm.devops.project, pat)
    tmdl_files = collect_from_devops(client, sm.devops.repo)

print(f"Collected {len(tmdl_files)} TMDL table files "
      f"({len({f.report_name for f in tmdl_files})} semantic models) via {sm.source_type}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Parse (logic in src/steps/semantic_models.py)
from datetime import datetime, timezone

from src.steps.semantic_models import semantic_models_step

out = semantic_models_step(
    tmdl_files, scan_timestamp=datetime.now(timezone.utc).isoformat()
)

print(f"Reports: {len(out.reports_seen)}")
print(f"SQL sources: {len(out.report_source_rows)}")
print(f"DAX expressions: {len(out.dax_rows)}")
print(f"Business names derived: {len(out.metric_name_rows)}")
for reason in out.names_skipped:
    print(f"  [i] no name derived — {reason}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3: Write the three input tables and run the postcondition gate
from src.schemas import DAX_EXPRESSIONS, METRIC_NAMES, REPORT_SOURCES, to_spark_schema
from src.steps.gates import postcondition_gate

if out.report_source_rows:
    spark.createDataFrame(out.report_source_rows, schema=to_spark_schema(REPORT_SOURCES)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("input_report_sources")
    print(f"Saved {len(out.report_source_rows)} rows to input_report_sources")

if out.dax_rows:
    spark.createDataFrame(out.dax_rows, schema=to_spark_schema(DAX_EXPRESSIONS)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("input_dax_expressions")
    print(f"Saved {len(out.dax_rows)} rows to input_dax_expressions")

if out.metric_name_rows:
    spark.createDataFrame(out.metric_name_rows, schema=to_spark_schema(METRIC_NAMES)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("input_metric_names")
    print(f"Saved {len(out.metric_name_rows)} rows to input_metric_names")

checked = postcondition_gate(
    "12_ingest_semantic_models",
    fetch=lambda t, cols: [r.asDict() for r in spark.table(t).select(*cols).collect()],
    table_exists=spark.catalog.tableExists,
)
print(f"[+] Postcondition gate passed for: {', '.join(checked)}")
print("\nNext: run 03_build_graph to land the consumption layer in the graph.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
