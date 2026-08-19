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

"""Ingest agent conversation events into the admin telemetry tables.

The surfaces (web chat App Service via OneLakeJsonlSink, or manually
uploaded local JSONL from CLI sessions) append event lines under
Files/agent_events/. This notebook folds them into gov_turn_events and
gov_feedback_events — idempotently: re-running never duplicates a row
(dedupe on conversation/turn/timestamp), and the source files are never
modified. Decision-shape flags land as columns so the admin report
slices on WHO decided (engine vs LLM) directly. ADR 0035 telemetry.
"""

EVENTS_DIR = "Files/agent_events"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Read every JSONL line under Files/agent_events
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

require_engine(src.__version__, REQUIRES_ENGINE, "950_ingest_agent_events")

import notebookutils  # noqa: F401  (Fabric runtime)

# Existence is checked explicitly: "directory not created yet" is a normal
# empty state, but a FAILED listing (permissions, renamed path) must raise —
# the old catch-all reported it as "Nothing to ingest" and telemetry went
# dark while every run printed success (audit 2026-08-15).
if notebookutils.fs.exists(EVENTS_DIR):
    files = [f.path for f in notebookutils.fs.ls(EVENTS_DIR)
             if f.name.endswith(".jsonl")]
else:
    files = []

lines = []
for path in files:
    lines.extend(spark.read.text(path).rdd.map(lambda r: r[0]).collect())

print(f"Event files: {len(files)}; lines: {len(lines)}")
if not files:
    print("Nothing to ingest — upload JSONL to Files/agent_events/ or "
          "configure SQA_EVENTS_ONELAKE_URL on the web app.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Parse, dedupe against existing tables, append
from src.schemas import FEEDBACK_EVENTS, TURN_EVENTS, to_spark_schema
from src.steps.agent_events import dedupe_events, parse_agent_events

out = parse_agent_events(lines)
print(f"Parsed: {len(out.turn_rows)} turn rows, "
      f"{len(out.feedback_rows)} feedback rows, {out.malformed} malformed")


def _existing_keys(table_name):
    if not spark.catalog.tableExists(table_name):
        return set()
    return {
        (r["conversation_id"], r["turn_index"], r["event_at"])
        for r in spark.table(table_name)
        .select("conversation_id", "turn_index", "event_at").collect()
    }


turn_fresh = dedupe_events(out.turn_rows, _existing_keys("gov_turn_events"))
if turn_fresh:
    spark.createDataFrame(turn_fresh, schema=to_spark_schema(TURN_EVENTS)) \
        .write.format("delta").mode("append").saveAsTable("gov_turn_events")
print(f"[+] gov_turn_events: {len(turn_fresh)} new rows "
      f"({len(out.turn_rows) - len(turn_fresh)} already ingested)")

fb_fresh = dedupe_events(out.feedback_rows,
                         _existing_keys("gov_feedback_events"))
if fb_fresh:
    spark.createDataFrame(fb_fresh, schema=to_spark_schema(FEEDBACK_EVENTS)) \
        .write.format("delta").mode("append") \
        .saveAsTable("gov_feedback_events")
print(f"[+] gov_feedback_events: {len(fb_fresh)} new rows "
      f"({len(out.feedback_rows) - len(fb_fresh)} already ingested)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3: Decision-mix summary (what the admin report will show)
if spark.catalog.tableExists("gov_turn_events"):
    df = spark.table("gov_turn_events")
    total = df.count()
    print(f"gov_turn_events total: {total}")
    for flag in ("verified_by_tool", "llm_assembled",
                 "unverified_sameness_language", "search_only", "no_tools"):
        n = df.filter(f"{flag} = true").count()
        print(f"  {flag}: {n}")
if spark.catalog.tableExists("gov_feedback_events"):
    fdf = spark.table("gov_feedback_events")
    not_helpful = fdf.filter(fdf.verdict == "not_helpful").count()
    print(f"gov_feedback_events total: {fdf.count()} "
          f"(not_helpful: {not_helpful})")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
