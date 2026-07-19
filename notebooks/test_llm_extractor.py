"""Fabric Notebook: Test LLM SQL Extractor

Tests which LLM methods are available in your Fabric environment
and runs the extractor on a sample proc that fails deterministic parsing.

Run this AFTER orchestrator_v2 to identify which procs can be recovered.
"""

# %% Cell 1: Check available AI methods
print("=== Checking available AI methods ===\n")

# Method 1: Fabric AI functions
try:
    from pyspark.sql.functions import expr
    test_df = spark.createDataFrame([("test",)], ["input"])
    # Don't actually call it yet — just check it exists
    print("1. PySpark AI functions: AVAILABLE (expr/ai.generate_text)")
except Exception as e:
    print(f"1. PySpark AI functions: NOT AVAILABLE ({e})")

# Method 2: SynapseML OpenAI
try:
    from synapse.ml.services.openai import OpenAIChatCompletion
    print("2. SynapseML OpenAI: AVAILABLE")
except ImportError as e:
    print(f"2. SynapseML OpenAI: NOT AVAILABLE ({e})")

# Method 3: openai package
try:
    import openai
    print(f"3. OpenAI SDK: AVAILABLE (v{openai.__version__})")
except ImportError:
    print("3. OpenAI SDK: NOT AVAILABLE")

# Method 4: anthropic package
try:
    import anthropic
    print(f"4. Anthropic SDK: AVAILABLE (v{anthropic.__version__})")
except ImportError:
    print("4. Anthropic SDK: NOT AVAILABLE")

# %% Cell 2: Test with Fabric AI (simplest method)
# This uses your Fabric tenant's built-in AI — no API keys needed
from pyspark.sql.functions import expr

test_prompt = "Extract only the SELECT statement from this T-SQL: SET NOCOUNT ON; DECLARE @x INT = 1; SELECT col1, col2 FROM my_table WHERE col1 > @x;"

try:
    df = spark.createDataFrame([(test_prompt,)], ["prompt"])
    result_df = df.selectExpr("ai_generate_text(prompt) as response")
    response = result_df.collect()[0]["response"]
    print(f"Fabric AI response:\n{response}")
except Exception as e:
    print(f"Fabric AI failed: {e}")
    print("\nTrying alternative function names...")

    # Try other possible function names
    for func_name in ["ai.generate_text", "ai_generate_text", "generate_text"]:
        try:
            result_df = df.selectExpr(f"{func_name}(prompt) as response")
            response = result_df.collect()[0]["response"]
            print(f"\n{func_name} worked! Response:\n{response}")
            break
        except Exception as e2:
            print(f"  {func_name}: {e2}")

# %% Cell 3: Test with a real failing proc
# Find one proc that failed deterministic parsing
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.parser.sql_parser import parse_sql

# Find a proc that fails
failing_proc = None
for source in sql_sources:
    try:
        parse_sql(source["sql"])
    except Exception:
        failing_proc = source
        break

if failing_proc:
    print(f"Found failing proc: {failing_proc['metric_id']}")
    print(f"SQL length: {len(failing_proc['sql'])} chars")
    print(f"First 200 chars:\n{failing_proc['sql'][:200]}")
else:
    print("No failing procs found!")

# %% Cell 4: Send failing proc to LLM for extraction
if failing_proc:
    from src.parser.llm_extractor import EXTRACTION_PROMPT

    prompt = EXTRACTION_PROMPT.format(sql=failing_proc["sql"])

    # Try Fabric AI
    try:
        df = spark.createDataFrame([(prompt,)], ["prompt"])
        result_df = df.selectExpr("ai_generate_text(prompt) as response")
        extracted = result_df.collect()[0]["response"]

        print(f"LLM extracted SQL ({len(extracted)} chars):")
        print(extracted[:500])
        print("..." if len(extracted) > 500 else "")

        # Now try parsing the extracted SQL
        try:
            result = parse_sql(extracted)
            print(f"\nPARSE SUCCESS!")
            print(f"  CTEs: {len(result.ctes)}")
            print(f"  Final tables: {len(result.final_select_tables)}")
        except Exception as pe:
            print(f"\nParse still failed: {pe}")
    except Exception as e:
        print(f"Fabric AI extraction failed: {e}")
        print("Try Cell 5 for alternative methods.")

# %% Cell 5: Batch test — how many failing procs can LLM recover?
# WARNING: This calls the LLM once per failing proc. May be slow/costly.
# Start with a small batch to test.

BATCH_SIZE = 5  # Start small — increase once you confirm it works

recovered = 0
still_failing = 0

for i, source in enumerate(sql_sources):
    if i >= BATCH_SIZE * 10:  # Only scan first N*10 to find BATCH_SIZE failures
        break

    try:
        parse_sql(source["sql"])
        continue  # Already parses — skip
    except Exception:
        pass

    # This one fails deterministic parsing — try LLM
    try:
        prompt = EXTRACTION_PROMPT.format(sql=source["sql"])
        df = spark.createDataFrame([(prompt,)], ["prompt"])
        result_df = df.selectExpr("ai_generate_text(prompt) as response")
        extracted = result_df.collect()[0]["response"]

        result = parse_sql(extracted)
        recovered += 1
        print(f"  RECOVERED: {source['metric_id']} — {len(result.ctes)} CTEs, {len(result.final_select_tables)} tables")
    except Exception as e:
        still_failing += 1
        print(f"  STILL FAILING: {source['metric_id']} — {str(e)[:80]}")

    if recovered + still_failing >= BATCH_SIZE:
        break

print(f"\nBatch results: {recovered} recovered, {still_failing} still failing out of {BATCH_SIZE} tested")
