# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

"""Generate business descriptions for all metrics via the Data Agent.

Reads from:  output_metric_logic (Delta)
Writes to:   output_metric_logic (updates description column)

Run 02-06 first — the Data Agent needs metric_logic populated.
The Data Agent must be published and accessible.

This notebook:
1. Reads all metrics from output_metric_logic
2. For each metric, asks the Data Agent to generate a description
3. Writes descriptions back to output_metric_logic
4. Incremental — skips metrics that already have descriptions
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

WORKSPACE_ID = config.fabric_graph.workspace_id
AGENT_ID = config.fabric_graph.data_agent_id

if not WORKSPACE_ID or not AGENT_ID:
    print("[X] FATAL: workspace_id and data_agent_id must be set in org_config.yaml")
    print("    Under fabric_graph:")
    print("      workspace_id: 'your-workspace-id'")
    print("      data_agent_id: 'your-agent-id'")
    raise SystemExit("Cannot generate descriptions without Data Agent config.")

print(f"Workspace: {WORKSPACE_ID}")
print(f"Agent: {AGENT_ID}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Load metrics and check what needs generation
ml_df = spark.table("output_metric_logic")
metrics = [r.asDict() for r in ml_df.collect()]

needs_generation = []
already_has = []
for m in metrics:
    desc = m.get("description") or ""
    if desc.strip():
        already_has.append(m["metric_name"])
    else:
        needs_generation.append(m)

print(f"Total metrics: {len(metrics)}")
print(f"Already have descriptions: {len(already_has)} (skipped)")
print(f"Need generation: {len(needs_generation)}")

if not needs_generation:
    print("\nAll metrics already have descriptions. Nothing to do.")
    print("To regenerate, clear the description column first.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Generate descriptions via Data Agent
if needs_generation:
    from src.adapters.fabric_agent import FabricAgentClient

    token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
    agent = FabricAgentClient(
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        access_token=token,
    )

    tool_name = agent.discover_tool_name()
    print(f"Data Agent tool: {tool_name}\n")

    DESCRIPTION_PROMPT = (
        "For the metric {metric_name}, write a concise business description in this format:\n\n"
        "First, one sentence stating the business purpose of the report "
        "(why it exists, who uses it, what decisions it supports).\n\n"
        "Then add a blank line and 'Business logic:' followed by a bulleted list of the key "
        "rules, filters, and criteria applied. For each item, describe it in business terms "
        "(not SQL). Include:\n"
        "- What patient/encounter population is included or excluded\n"
        "- What time windows or date ranges apply\n"
        "- What clinical criteria or thresholds are checked\n"
        "- How compliance or outcomes are calculated\n"
        "- What groupings or breakdowns are applied (by department, shift, etc.)\n\n"
        "No greetings, no preamble, no markdown headers, no bold text. "
        "Start directly with the purpose sentence."
    )

    REJECT_PHRASES = [
        "wasn't able to find", "couldn't find", "not found",
        "hasn't been", "I'm happy to help", "don't have information",
        "not available", "no documented",
    ]

    SAVE_EVERY = 10
    generated = {}
    failed = []
    save_count = 0

    for i, m in enumerate(needs_generation):
        metric_name = m["metric_name"]
        prompt = DESCRIPTION_PROMPT.format(metric_name=metric_name)

        resp = agent.query(prompt)

        if resp.status == "success" and resp.answer:
            if any(phrase in resp.answer.lower() for phrase in REJECT_PHRASES):
                print(f"  [{i+1}/{len(needs_generation)}] REJECTED {metric_name} — non-answer")
                failed.append(metric_name)
                continue
            generated[m["metric_id"]] = resp.answer
            print(f"  [{i+1}/{len(needs_generation)}] OK {metric_name} ({len(resp.answer)} chars)")
        else:
            failed.append(metric_name)
            print(f"  [{i+1}/{len(needs_generation)}] FAILED {metric_name}: {resp.error[:100]}")

        # Incremental save
        save_count += 1
        if save_count >= SAVE_EVERY:
            # Save progress (see cell 3)
            save_count = 0

    print(f"\nGenerated: {len(generated)}, Failed: {len(failed)}")
    if failed:
        print(f"Failed metrics: {', '.join(failed[:10])}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3: Write descriptions back to output_metric_logic
if needs_generation and generated:
    from pyspark.sql.functions import when, lit, col
    from pyspark.sql import Row

    # Create a lookup dataframe from generated descriptions
    desc_rows = [(mid, desc) for mid, desc in generated.items()]
    if desc_rows:
        desc_df = spark.createDataFrame(desc_rows, ["metric_id", "new_description"])

        # Read current metric_logic, join with descriptions, update
        current_df = spark.table("output_metric_logic")

        updated_df = current_df.join(desc_df, on="metric_id", how="left")
        updated_df = updated_df.withColumn(
            "description",
            when(col("new_description").isNotNull(), col("new_description"))
            .otherwise(col("description"))
        ).drop("new_description")

        updated_df.write.format("delta").mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable("output_metric_logic")

        print(f"[+] Updated {len(desc_rows)} descriptions in output_metric_logic")

        # Show samples
        for mid, desc in list(generated.items())[:3]:
            print(f"\n  {mid}:")
            print(f"    {desc[:200]}...")
    else:
        print("No descriptions to save.")
else:
    print("Nothing to save — either all descriptions exist or generation was skipped.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 4: Verify
print("\n=== DESCRIPTION COVERAGE ===")
final_df = spark.table("output_metric_logic")
total = final_df.count()
with_desc = final_df.filter("description IS NOT NULL AND description != ''").count()
without_desc = total - with_desc

print(f"Total metrics:       {total}")
print(f"With descriptions:   {with_desc} ({100*with_desc//max(total,1)}%)")
print(f"Without descriptions: {without_desc}")

if without_desc > 0:
    print("\nMetrics still missing descriptions:")
    for r in final_df.filter("description IS NULL OR description = ''").select("metric_name").collect():
        print(f"  {r['metric_name']}")
    print("\nRe-run this notebook to retry failed metrics.")
else:
    print("\n>>> ALL METRICS HAVE DESCRIPTIONS <<<")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
