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

"""Refresh the semantic search index end to end (run AFTER 600).

Reads from:  graph_nodes (fresh descriptions)
Writes to:   output_semantic_catalog (Delta), semantic_catalog
             (Eventhouse copy, via KQL mgmt API) + full re-embed

Descriptions change => search documents change => embeddings must be
recomputed, or search keeps ranking on stale vectors (live find
2026-08-13). One-time setup (table DDL, encoding policy, the
semantic_search function, callout policy) stays in
devtools/eventhouse_setup.kql — this notebook is the every-run path.

Standing rule: 300/400 rerun => 600 rerun => THIS notebook => 800.
"""

import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.24"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "700_refresh_search_index")

# Per-environment endpoints come from org_config.yaml (search: block) —
# never hardcoded here: tenant URIs in a notebook are config drift waiting
# to happen, and the embed endpoint is deployment-specific.
import yaml as _yaml

_raw_cfg = _yaml.safe_load(
    open("/lakehouse/default/Files/sql-query-agent/org_config.yaml"))
_search_cfg = _raw_cfg.get("search") or {}
KUSTO_URI = _search_cfg.get("kusto_uri") or ""
KUSTO_DB = _search_cfg.get("kusto_db") or ""
EMBED_ENDPOINT = _search_cfg.get("embed_endpoint") or ""
missing = [k for k, v in
           {"kusto_uri": KUSTO_URI, "kusto_db": KUSTO_DB,
            "embed_endpoint": EMBED_ENDPOINT}.items() if not v]
if missing:
    raise ValueError(
        f"org_config.yaml search: block is missing {missing} — add the "
        "Eventhouse Query URI, database name, and the Azure OpenAI "
        "embeddings endpoint (see org_config.example.yaml)")
# Optional smoke phrase printed with top scores after the refresh
# (leave empty to skip) — set to whatever you are testing today.
PROBE_PHRASE = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import notebookutils

from src.orchestrator.kusto import KustoClient
from src.steps.search_index import COVERAGE_QUERY, embed_command

client = KustoClient(
    KUSTO_URI, KUSTO_DB,
    lambda: notebookutils.credentials.getToken(KUSTO_URI),
    timeout=600,
)
client.mgmt(embed_command(EMBED_ENDPOINT))          # only missing rows pay
print(client.run(COVERAGE_QUERY))                   # expect [{'Count': 0}]
print(client.run(
    "semantic_catalog | where isnull(emb) or array_length(emb) == 0 "
    "| project node_id, search_len = strlen(search_text)"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# refusal floor — expect [] (junk must clear nothing)
print(client.run('semantic_search("unicorn readmission velocity")'))

# the question that started all this — new ranking with scores
for row in client.run('semantic_search("ED sepsis", 10)'):
    print(f"{row['closeness']:.3f}  {row['kind']:<7} {row['node_id']}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Rebuild the catalog Delta table from the fresh graph
from src.steps.gates import precondition_gate

# Required inputs must exist (and be non-empty where the contract says so)
# BEFORE work starts — a missing table fails with a message naming the
# producing notebook, not a pyspark stack trace. Registry-driven; see
# src/steps/gates.py.
precondition_gate("700_refresh_search_index", table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count())


from src.steps.semantic_catalog import build_semantic_catalog

nodes_rows = [r.asDict() for r in spark.table("graph_nodes").collect()]
out = build_semantic_catalog(nodes_rows)
print(f"metrics={out.metric_count} steps={out.step_count} terms={out.term_count}")

# Explicit column order — Spark alphabetizes dict rows, and positional
# copies downstream then shift columns (bit us live 2026-08-09)
df = spark.createDataFrame(out.rows).select(
    "node_id", "kind", "ref", "name", "business_name",
    "search_text", "display_text")
df.write.mode("overwrite").saveAsTable("output_semantic_catalog")
print(f"output_semantic_catalog: {df.count()} rows")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Copy into the Eventhouse + full re-embed + verify
# (notebookutils is a Fabric-injected global — no import needed)
from src.orchestrator.kusto import KustoClient
from src.steps.search_index import refresh_search_index

# (endpoint presence is validated where the search: block is loaded)

client = KustoClient(
    KUSTO_URI, KUSTO_DB,
    lambda: notebookutils.credentials.getToken(KUSTO_URI),
    timeout=600,   # the embed pass batches ~441 ai_embeddings calls
)
report = refresh_search_index(client.mgmt, client.run, EMBED_ENDPOINT)
print(report)
if not report["threshold_ok"]:
    print("WARNING: the refusal probe returned rows — the 0.35 "
          "threshold needs recalibration for the new search_text "
          "composition (see eventhouse_setup.kql section 3 notes).")

if PROBE_PHRASE:
    for row in client.run(f'semantic_search("{PROBE_PHRASE}", 10)'):
        print(f"{row['closeness']:.3f}  {row['kind']:<7} {row['node_id']}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Manual cell: re-embed missing rows + coverage check (moved from the top
# of this notebook 2026-08-15 — it uses `client`/`EMBED_ENDPOINT`, which are
# only defined above, so at the top it broke Run All with a NameError).
# Run AFTER the main cells when you want to top-up embeddings ad hoc.
from src.steps.search_index import COVERAGE_QUERY, embed_command

client.mgmt(embed_command(EMBED_ENDPOINT))          # only missing rows pay
print(client.run(COVERAGE_QUERY))                   # expect Count = 0
print(client.run(
    "semantic_catalog | where isnull(emb) or array_length(emb) == 0 "
    "| project node_id, search_len = strlen(search_text)"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
