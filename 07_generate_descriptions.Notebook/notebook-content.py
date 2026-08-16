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

"""Generate business descriptions bottom-up over the calculation DAG (ADR 0019).

Reads from:  graph_nodes, graph_edges, ops_description_cache (Delta)
Writes to:   graph_nodes (description column: transformation + canonical rows),
             output_metric_logic (description column), ops_description_cache

Order matters: CTE steps are described before the metrics that use them
(topological walk in src/descriptions.py); each metric's description is
composed from its root steps' descriptions — summaries of summaries, never
raw SQL walls. Incremental: unchanged steps hit the content-hash cache and
cost nothing.

LLM: an OpenAI-compatible chat endpoint — the customer's Azure OpenAI in
production. Configure in org_config.yaml:

    llm:
      endpoint: https://<resource>.openai.azure.com/openai/deployments/<dep>  # or any /v1 base
      model: gpt-4o-mini
      api_key_file: llm_api_key.txt   # next to org_config.yaml, NEVER in git

After running: re-run 05 and re-Load the Graph Model so the LPG picks up
the step descriptions.
"""

# %% Cell 0: Setup
import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from datetime import datetime, timezone
from pathlib import Path

import yaml

CONFIG_DIR = Path("/lakehouse/default/Files/sql-query-agent")
raw_config = yaml.safe_load((CONFIG_DIR / "org_config.yaml").read_text())
llm_cfg = raw_config.get("llm") or {}
LLM_ENDPOINT = (llm_cfg.get("endpoint") or "").rstrip("/")
LLM_MODEL = llm_cfg.get("model") or "gpt-4o-mini"
key_file = CONFIG_DIR / (llm_cfg.get("api_key_file") or "llm_api_key.txt")

if not LLM_ENDPOINT or not key_file.exists():
    print("[X] FATAL: llm.endpoint in org_config.yaml and the api_key_file are required.")
    print("    See this notebook's docstring for the org_config.yaml llm: block.")
    raise SystemExit("Cannot generate descriptions without an LLM endpoint.")
LLM_API_KEY = key_file.read_text().strip()
print(f"LLM endpoint: {LLM_ENDPOINT} (model {LLM_MODEL})")


from src.llm_client import chat_completion


def describe(prompt: str) -> str:
    # Azure vs OpenAI header/url differences live in src.llm_client —
    # Azure endpoints get api-key auth and api-version handling.
    return chat_completion(
        "You write terse, faithful business documentation.", prompt,
        endpoint=LLM_ENDPOINT, api_key=LLM_API_KEY, model=LLM_MODEL,
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Load graph + cache, run the bottom-up walk

# Registry-driven precondition gate — includes ops_phi_findings: descriptions
# must never be generated without the steward-reviewed PHI findings (ADR 0025).
from src.steps.gates import precondition_gate

precondition_gate("07_generate_descriptions", table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count())


from src.descriptions import generate_descriptions
from src.phi_scan import from_records, redact_measure_expressions, redact_node_fragments

nodes_rows = [r.asDict() for r in spark.table("graph_nodes").collect()]
edges_rows = [r.asDict() for r in spark.table("graph_edges").collect()]

# PHI gate (ADR 0025): fragments are redacted BEFORE any prompt is built,
# using the findings 02_parse persisted (which carry steward dispositions —
# a steward's 'redact' decision must hold here). 02 always writes the table,
# even when empty, so absence means 02 never ran: STOP. The old inline
# rescan silently dropped dispositions right before text left for an
# external LLM endpoint (audit 2026-08-15).
phi_findings = from_records(
    [r.asDict() for r in spark.table("ops_phi_findings").collect()]
)
redacted_count = redact_node_fragments(nodes_rows, phi_findings)
print(f"PHI gate: {len(phi_findings)} findings, {redacted_count} fragments redacted")

# DAX passes the same gate (ADR 0040): measure expressions are scanned
# and redacted inline every run — fail-safe toward redaction — before
# any measure prompt is built.
dax_findings, dax_redacted = redact_measure_expressions(nodes_rows)
print(f"PHI gate (DAX): {dax_findings} findings, {dax_redacted} expressions redacted")

cache: dict = {}
if spark.catalog.tableExists("ops_description_cache"):
    for r in spark.table("ops_description_cache").collect():
        cache[r["content_hash"]] = r["description"]
print(f"Nodes: {len(nodes_rows)}, edges: {len(edges_rows)}, cached steps: {len(cache)}")

result = generate_descriptions(nodes_rows, edges_rows, describe, cache=cache)
print(f"Generated: {result.generated}  cache hits: {result.cache_hits}  failed: {len(result.failed)}")
if result.failed:
    for nid in result.failed[:10]:
        print(f"  failed: {nid}")
if result.vague:
    print(f"Vague-filler flags (value hidden behind 'specific'/'certain'): {len(result.vague)}")
    for nid in result.vague[:10]:
        print(f"  vague: {nid}")
if result.jargon:
    print(f"Raw-identifier flags (warehouse jargon in business text): {len(result.jargon)}")
    for nid in result.jargon[:10]:
        print(f"  jargon: {nid}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Write descriptions back — graph_nodes (enricher), cache, metric_logic
from src.schemas import DESCRIPTION_CACHE, to_spark_schema

if result.descriptions:
    desc_df = spark.createDataFrame(
        list(result.descriptions.items()), ["node_id", "new_description"]
    )
    from pyspark.sql.functions import col, when

    updated = (
        spark.table("graph_nodes")
        .join(desc_df, on="node_id", how="left")
        .withColumn(
            "description",
            when(col("new_description").isNotNull(), col("new_description"))
            .otherwise(col("description")),
        )
        .drop("new_description")
    )
    updated.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("graph_nodes")
    print(f"[+] Enriched {len(result.descriptions)} node descriptions in graph_nodes")

    now = datetime.now(timezone.utc).isoformat()
    cache_rows = [
        {"content_hash": h, "node_id": "", "description": d, "generated_at": now}
        for h, d in cache.items()
    ]
    spark.createDataFrame(cache_rows, schema=to_spark_schema(DESCRIPTION_CACHE)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("ops_description_cache")
    print(f"[+] Persisted {len(cache_rows)} cache entries")

    metric_desc = [
        (nid.replace("canonical:", ""), d)
        for nid, d in result.descriptions.items() if nid.startswith("canonical:")
    ]
    if metric_desc:
        md_df = spark.createDataFrame(metric_desc, ["metric_id", "new_description"])
        ml = (
            spark.table("output_metric_logic")
            .join(md_df, on="metric_id", how="left")
            .withColumn(
                "description",
                when(col("new_description").isNotNull(), col("new_description"))
                .otherwise(col("description")),
            )
            .drop("new_description")
        )
        ml.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
            .saveAsTable("output_metric_logic")
        print(f"[+] Updated {len(metric_desc)} metric descriptions in output_metric_logic")
else:
    print("Nothing to write — all descriptions current.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3: Coverage + next steps
for layer, label in (("transformation", "steps"), ("canonical", "metrics")):
    df = spark.table("graph_nodes").filter(f"layer = '{layer}'")
    total = df.count()
    described = df.filter("description IS NOT NULL AND description != ''").count()
    print(f"{label}: {described}/{total} described")

print("\nNext: run 05 (export picks up step descriptions), then re-Load the Graph Model.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
