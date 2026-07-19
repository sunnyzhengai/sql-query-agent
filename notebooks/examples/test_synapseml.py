"""Fabric Notebook: Test SynapseML OpenAI

Tests if SynapseML OpenAI can call Azure OpenAI from your Fabric environment.
"""

# %% Cell 1: Simple SynapseML test
from synapse.ml.services.openai import OpenAIChatCompletion
from pyspark.sql import Row

# Create a simple test prompt
test_df = spark.createDataFrame([
    Row(messages=[
        Row(role="system", content="You are a SQL extraction tool. Return only SQL."),
        Row(role="user", content="Extract only the SELECT statement from this: SET NOCOUNT ON; DECLARE @x INT = 1; SELECT col1, col2 FROM my_table WHERE col1 > 1;"),
    ])
])

completion = (
    OpenAIChatCompletion()
    .setMessagesCol("messages")
    .setOutputCol("response")
)

result_df = completion.transform(test_df)
result_df.select("response").show(truncate=False)

# %% Cell 2: If Cell 1 fails, try with explicit deployment name
# You may need to set a deployment name that matches your Azure OpenAI setup
completion_v2 = (
    OpenAIChatCompletion()
    .setDeploymentName("gpt-4")
    .setMessagesCol("messages")
    .setOutputCol("response")
)

try:
    result_df = completion_v2.transform(test_df)
    result_df.select("response").show(truncate=False)
except Exception as e:
    print(f"gpt-4 failed: {e}")

    # Try gpt-35-turbo
    completion_v3 = (
        OpenAIChatCompletion()
        .setDeploymentName("gpt-35-turbo")
        .setMessagesCol("messages")
        .setOutputCol("response")
    )
    try:
        result_df = completion_v3.transform(test_df)
        result_df.select("response").show(truncate=False)
    except Exception as e2:
        print(f"gpt-35-turbo also failed: {e2}")
        print("\nYou may need to configure an Azure OpenAI connection in your Fabric workspace.")
