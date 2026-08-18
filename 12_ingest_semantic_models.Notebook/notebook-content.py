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

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.18"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "12_ingest_semantic_models")


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
    FolderTmdlSource,
    collect_from_devops,
)

sm = config.semantic_models
if sm.source_type == "workspace":
    # Turn-key default: straight from the Fabric workspace REST API —
    # works whether or not the workspace has git integration. Reports
    # commonly span several workspaces: workspace_ids collects them all
    # in ONE pass and ONE write (per-workspace runs would clobber each
    # other under overwrite semantics). Naming is refuse-over-guess
    # (2026-08-18): shared metrics name only when consumer titles agree.
    from src.extractor.tmdl_source import collect_from_workspaces

    tmdl_files, ws_counts = collect_from_workspaces(
        sm.resolved_workspace_ids(),
        token_provider=lambda: notebookutils.credentials.getToken(  # noqa: F821
            "https://api.fabric.microsoft.com"),
        current_workspace_id=notebookutils.runtime.context.get(  # noqa: F821
            "currentWorkspaceId"),
    )
    for ws_id, r in ws_counts.items():
        print(f"  workspace {ws_id}: {r['files']} TMDL table files, "
              f"{len(r['skipped'])} models skipped")
        for model, cls, reason in r["skipped"]:
            note = {"not-exportable": "expected (default/legacy model)",
                    "permission": "ACTIONABLE — grant workspace access",
                    "timeout": "retry later"}.get(cls, "inspect")
            print(f"    [skip:{cls}] {model} — {note}")
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

# Shape census (pre-step): total classification at file grain BEFORE
# parsing — the harvest states its coverage up front instead of failing
# silently partway. Unknown signatures are whitelist-anonymized (M
# stdlib names only) and safe to send to support.
from src.mquery import census_files, coverage_lines

census_rows = census_files(tmdl_files)
for line in coverage_lines(census_rows):
    print(line)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Parse (logic in src/steps/semantic_models.py)
from datetime import datetime, timezone

from src.steps.semantic_models import semantic_models_step

# Corpus membership for name derivation (amendment 2026-08-18): trust
# "is this a parsed metric" over the TMDL Kind field — connectors reach
# views as Kind='Table'. Absence of the corpus is legitimate on a
# fresh workspace; a failed read is not (it must raise).
corpus_metric_ids = None
if spark.catalog.tableExists(config.lakehouse.sql_sources):
    corpus_metric_ids = {
        r["metric_id"] for r in
        spark.table(config.lakehouse.sql_sources).select("metric_id").collect()
    }
    print(f"Corpus membership: {len(corpus_metric_ids)} metric ids")
else:
    print("No input_sql_sources yet — name derivation falls back to TMDL kinds")

RUN_AT = datetime.now(timezone.utc).isoformat()
out = semantic_models_step(
    tmdl_files, scan_timestamp=RUN_AT, corpus_metric_ids=corpus_metric_ids
)

print(f"Reports: {len(out.reports_seen)}")
print(f"SQL sources: {len(out.report_source_rows)}")
print(f"DAX expressions: {len(out.dax_rows)}")
print(f"Business names derived: {len(out.metric_name_rows)}")
for reason in out.names_skipped:
    print(f"  [i] no name derived — {reason}")

# Funnel (HANDOFF_FUNNEL_AND_FALLOUT): every collected file is accounted
# for — a source row or a classified fallout row, never silent absence.
from collections import Counter

partition_fallout = [f for f in out.fallout_rows if f["stage"] == "12_partition_parse"]
print(f"\nFunnel: {len(tmdl_files)} files -> "
      f"{len(out.report_source_rows)} sources, "
      f"{len(partition_fallout)} fallout, "
      f"{len(out.fallout_rows) - len(partition_fallout)} naming refusals")
for (code, cnt) in Counter(f["reason_code"] for f in out.fallout_rows).most_common():
    print(f"  {code}: {cnt}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3: Write the input tables + fallout, run the postcondition gate
from src.schemas import (
    DAX_EXPRESSIONS,
    FALLOUT,
    METRIC_NAMES,
    REPORT_SOURCES,
    to_spark_schema,
)
from src.steps.gates import postcondition_gate

# Fallout rows are the gold (append-only history): collector skips +
# partition-parse drops + naming refusals, all queryable by reason_code.
fallout_all = [
    {"run_at": RUN_AT, **f} for f in out.fallout_rows
]
if sm.source_type == "workspace":
    for ws_id, r in ws_counts.items():
        for model, cls, reason in r["skipped"]:
            fallout_all.append({
                "run_at": RUN_AT, "stage": "12_collect",
                "entity_id": f"{ws_id}/{model}",
                "reason_code": f"collect_{cls}", "reason_text": reason,
                "contract_id": "contract:input_report_sources",
            })
if fallout_all:
    fallout_df = spark.createDataFrame(
        [(f["run_at"], f["stage"], f["entity_id"], f["reason_code"],
          f["reason_text"], f["contract_id"]) for f in fallout_all],
        schema=to_spark_schema(FALLOUT))
    fallout_df.write.format("delta").mode("append").saveAsTable("ops_fallout")
print(f"ops_fallout: {len(fallout_all)} rows appended "
      "(query: GROUP BY reason_code)")

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
