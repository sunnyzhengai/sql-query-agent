"""LLM-based SQL extractor.

Sends raw stored procedures to an LLM and asks it to extract only the
SELECT/WITH/UNION queries, stripping all procedural T-SQL scaffolding.

This replaces the regex-based preprocessing approach with a turn-key
solution that works across dialects (T-SQL, PL/SQL, Snowflake, etc.).

Backend-agnostic: supports multiple LLM backends via the LLMBackend protocol.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """You are a SQL extraction tool. \
Your job is to extract ONLY the data query logic from a stored procedure or script.

RULES:
1. Return ONLY the SELECT, WITH (CTE), and UNION/EXCEPT/INTERSECT statements
2. REMOVE all of these (they are procedural scaffolding, not business logic):
   - CREATE PROCEDURE / ALTER PROCEDURE and parameter declarations
   - DECLARE @variable statements
   - SET @variable = ... assignments
   - SET NOCOUNT ON, SET ANSI_NULLS ON, SET TRANSACTION ISOLATION LEVEL, etc.
   - IF ... BEGIN ... END blocks
   - WHILE loops
   - GOTO / labels
   - PRINT statements
   - DROP TABLE IF EXISTS
   - CREATE INDEX statements
   - INSERT INTO #temp VALUES(...) seed data
   - OPTION(...) query hints
   - BEGIN / END block wrappers
   - GO batch separators
   - USE [database] statements
   - EXEC / EXECUTE calls
   - RETURN statements
   - TRY / CATCH blocks
3. KEEP SELECT ... INTO #temp_table statements — these ARE business logic (staging queries)
4. KEEP the WITH (CTE) ... SELECT pattern intact
5. KEEP UNION / EXCEPT / INTERSECT combinations
6. Do NOT modify, reformat, or "improve" the SQL — return it EXACTLY as written
7. Do NOT add any explanation — return ONLY the extracted SQL
8. Separate multiple statements with a semicolon (;)
9. If @variables appear in WHERE clauses or expressions, replace them with placeholders like '__param_VarName__'

INPUT:
{sql}

OUTPUT (extracted SQL only):"""


@runtime_checkable
class LLMBackend(Protocol):
    """Protocol for LLM backends."""

    def generate(self, prompt: str) -> str:
        """Send a prompt and return the response text."""
        ...


class FabricAIBackend:
    """Uses Fabric's built-in AI capabilities via SynapseML OpenAI.

    Requires: synapse.ml.services.openai available in the Fabric environment.
    Uses the Azure OpenAI deployment your Fabric tenant is configured with.
    """

    def __init__(self, deployment_name: str = "gpt-4", max_tokens: int = 4096) -> None:
        self.deployment_name = deployment_name
        self.max_tokens = max_tokens
        self._client = None

    def generate(self, prompt: str) -> str:
        if self._client is None:
            try:
                from synapse.ml.services.openai import OpenAICompletion
                self._client = OpenAICompletion
            except ImportError:
                raise ImportError(
                    "SynapseML OpenAI not available. "
                    "This backend only works in Microsoft Fabric notebooks."
                )
        # SynapseML uses Spark DataFrames — we create a single-row DF
        # This will be called from a Fabric notebook where spark is available
        raise NotImplementedError(
            "FabricAIBackend requires Spark context. "
            "Use the fabric_extract_sql() helper function instead."
        )


class AzureOpenAIBackend:
    """Uses Azure OpenAI REST API directly.

    Requires: openai pip package + Azure OpenAI endpoint configured.
    """

    def __init__(
        self,
        endpoint: str = "",
        api_key: str = "",
        deployment: str = "gpt-4",
        api_version: str = "2024-02-15-preview",
        max_tokens: int = 4096,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version
        self.max_tokens = max_tokens

    def generate(self, prompt: str) -> str:
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required: pip install openai")

        client = openai.AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

        response = client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are a SQL extraction tool. Return only SQL, no explanations."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=0,  # deterministic
        )

        return response.choices[0].message.content.strip()


class AnthropicBackend:
    """Uses Anthropic Claude API.

    Requires: anthropic pip package + API key.
    """

    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-20250514", max_tokens: int = 4096) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, prompt: str) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return response.content[0].text.strip()


def extract_sql(raw_sql: str, backend: LLMBackend) -> str:
    """Extract clean SQL from a raw stored procedure using an LLM.

    Args:
        raw_sql: The full stored procedure text (CREATE PROCEDURE ... END).
        backend: An LLM backend that implements the generate() method.

    Returns:
        Clean SQL containing only SELECT/WITH/UNION statements.
    """
    prompt = EXTRACTION_PROMPT.format(sql=raw_sql)
    logger.info("Sending %d chars to LLM for SQL extraction", len(raw_sql))

    result = backend.generate(prompt)

    # Clean up common LLM output artifacts
    # Remove markdown code fences if the LLM wraps the output
    if result.startswith("```"):
        lines = result.split("\n")
        # Remove first line (```sql) and last line (```)
        lines = [line for line in lines if not line.strip().startswith("```")]
        result = "\n".join(lines)

    logger.info("LLM returned %d chars of extracted SQL", len(result))
    return result.strip()


def fabric_extract_sql(raw_sql: str, spark_session=None) -> str:
    """Extract SQL using Fabric's built-in AI functions.

    This is a convenience function for use directly in Fabric notebooks.
    It uses the msfabric AI capabilities without requiring external API keys.

    Args:
        raw_sql: The full stored procedure text.
        spark_session: The Spark session (pass `spark` from notebook).

    Returns:
        Clean SQL containing only SELECT/WITH/UNION statements.
    """
    if spark_session is None:
        raise ValueError("spark_session is required. Pass `spark` from your Fabric notebook.")

    prompt = EXTRACTION_PROMPT.format(sql=raw_sql)

    try:
        # Method 1: Fabric AI functions (if available)
        from pyspark.sql.functions import expr
        df = spark_session.createDataFrame([(prompt,)], ["prompt"])
        result_df = df.withColumn(
            "response",
            expr("ai.generate_text(prompt)")
        )
        result = result_df.collect()[0]["response"]
        return result.strip()
    except Exception as e:
        logger.warning("Fabric AI function failed: %s. Trying SynapseML.", e)

    try:
        # Method 2: SynapseML OpenAI
        from pyspark.sql import Row
        from synapse.ml.services.openai import OpenAIChatCompletion

        df = spark_session.createDataFrame([
            Row(messages=[
                Row(role="system", content="You are a SQL extraction tool. Return only SQL."),
                Row(role="user", content=prompt),
            ])
        ])

        completion = (
            OpenAIChatCompletion()
            .setDeploymentName("gpt-4")
            .setMaxTokens(4096)
            .setTemperature(0)
            .setMessagesCol("messages")
            .setOutputCol("response")
        )

        result_df = completion.transform(df)
        result = result_df.collect()[0]["response"]
        return result.strip()
    except Exception as e:
        logger.error("All Fabric AI methods failed: %s", e)
        raise RuntimeError(
            "Could not access Fabric AI functions. "
            "Ensure your Fabric workspace has AI capabilities enabled."
        ) from e
