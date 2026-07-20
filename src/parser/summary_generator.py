"""LLM-based summary generator for graph nodes.

Generates plain-English summaries for transformation and canonical nodes
at build time, so the Data Agent can answer questions instantly without
parsing SQL fragments.

Two levels of summary:
1. Transformation nodes: what each logic step does
2. Canonical nodes: what the full metric measures (end-to-end)
"""

from __future__ import annotations

import logging
from typing import Any

from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.models import NodeLayer

logger = logging.getLogger(__name__)


TRANSFORM_SUMMARY_PROMPT = """Summarize what this SQL logic step does in 1-2 sentences.
Write for a business user — no SQL jargon, no table names.
Focus on: what data it selects, what filters it applies, what it calculates.

SQL:
{sql_fragment}

Summary:"""


CANONICAL_SUMMARY_PROMPT = """You are summarizing a healthcare report/metric for business users.

Based on the following information, write a 3-5 sentence description of what this metric measures,
what criteria filter the data, and what the output represents.
Write in plain English — no SQL, no table names, no technical jargon.

Metric name: {metric_name}

Logic steps (in order):
{steps_description}

Source tables and their purposes:
{tables_description}

Summary:"""


def generate_transform_summaries(
    builder: GraphBuilder,
    llm_backend: Any,
    batch_size: int = 10,
) -> dict[str, str]:
    """Generate summaries for all transformation nodes.

    Args:
        builder: The graph builder with nodes populated.
        llm_backend: An object with generate(prompt) -> str method.
        batch_size: How many to process before logging progress.

    Returns:
        Dict of node_id -> summary text.
    """
    summaries = {}
    transform_nodes = [
        n for n in builder.nodes.values()
        if n.layer == NodeLayer.TRANSFORMATION
        and n.name != "__final_select__"
    ]

    logger.info("Generating summaries for %d transformation nodes", len(transform_nodes))

    for i, node in enumerate(transform_nodes):
        sql_fragment = node.properties.get("sql_fragment", "")
        if not sql_fragment:
            continue

        # Truncate very long fragments to avoid token limits
        if len(sql_fragment) > 2000:
            sql_fragment = sql_fragment[:2000] + "\n... (truncated)"

        prompt = TRANSFORM_SUMMARY_PROMPT.format(sql_fragment=sql_fragment)

        try:
            summary = llm_backend.generate(prompt)
            summaries[node.node_id] = summary.strip()
        except Exception as e:
            logger.warning("Failed to summarize %s: %s", node.node_id, e)
            summaries[node.node_id] = ""

        if (i + 1) % batch_size == 0:
            logger.info("  Summarized %d/%d transformation nodes", i + 1, len(transform_nodes))

    logger.info("Generated %d transformation summaries", len(summaries))
    return summaries


def generate_canonical_summaries(
    builder: GraphBuilder,
    llm_backend: Any,
    transform_summaries: dict[str, str] | None = None,
) -> dict[str, str]:
    """Generate end-to-end summaries for all canonical (metric) nodes.

    Uses transformation summaries if available, otherwise reads sql_fragments.

    Args:
        builder: The graph builder with nodes populated.
        llm_backend: An object with generate(prompt) -> str method.
        transform_summaries: Pre-generated transform summaries (from generate_transform_summaries).

    Returns:
        Dict of node_id -> summary text.
    """
    summaries = {}
    traverser = GraphTraverser(builder.nodes, builder.edges)

    canonical_nodes = [
        n for n in builder.nodes.values()
        if n.layer == NodeLayer.CANONICAL
    ]

    logger.info("Generating summaries for %d canonical nodes", len(canonical_nodes))

    for i, node in enumerate(canonical_nodes):
        metric_id = node.node_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)

        if not subgraph:
            continue

        # Build steps description from transform summaries or sql_fragments
        steps = []
        for t_node in subgraph.get("transformations", []):
            if t_node.name == "__final_select__":
                continue
            if transform_summaries and t_node.node_id in transform_summaries:
                summary = transform_summaries[t_node.node_id]
                if summary:
                    steps.append(f"- {t_node.name}: {summary}")
                    continue
            # Fallback to sql_fragment
            fragment = t_node.properties.get("sql_fragment", "")
            if fragment:
                # Truncate for prompt
                if len(fragment) > 500:
                    fragment = fragment[:500] + "..."
                steps.append(f"- {t_node.name}: {fragment}")

        # Build tables description
        tables = []
        for t_node in subgraph.get("technical", []):
            if t_node.properties.get("column") is None:
                desc = t_node.description or "No description available"
                tables.append(f"- {t_node.name}: {desc}")

        if not steps and not tables:
            continue

        steps_text = "\n".join(steps) if steps else "No transformation steps available"
        tables_text = "\n".join(tables[:15]) if tables else "No source tables identified"
        if len(tables) > 15:
            tables_text += f"\n- ... and {len(tables) - 15} more tables"

        prompt = CANONICAL_SUMMARY_PROMPT.format(
            metric_name=node.name,
            steps_description=steps_text,
            tables_description=tables_text,
        )

        try:
            summary = llm_backend.generate(prompt)
            summaries[node.node_id] = summary.strip()
        except Exception as e:
            logger.warning("Failed to summarize %s: %s", node.node_id, e)
            summaries[node.node_id] = ""

        if (i + 1) % 10 == 0:
            logger.info("  Summarized %d/%d canonical nodes", i + 1, len(canonical_nodes))

    logger.info("Generated %d canonical summaries", len(summaries))
    return summaries


COMBINED_PROMPT = """You are summarizing a healthcare report/metric for business users.

Analyze the following SQL logic and produce TWO types of summaries:

1. METRIC SUMMARY: A 3-5 sentence description of what the entire metric measures,
   what criteria filter the data, and what the output represents.
   Write in plain English — no SQL, no table names, no technical jargon.

2. STEP SUMMARIES: For each named logic step listed below, write a 1-2 sentence
   description of what that specific step does. Focus on what data it selects,
   what filters it applies, and what it calculates.

Metric name: {metric_name}

Logic steps:
{steps}

Source tables and their purposes:
{tables}

Respond ONLY in this exact JSON format (no markdown, no code fences):
{{
  "metric_summary": "Your 3-5 sentence metric summary here",
  "step_summaries": {{
    "step_name_1": "What this step does",
    "step_name_2": "What this step does"
  }}
}}"""


def generate_all_summaries_combined(
    builder: GraphBuilder,
    llm_backend: Any,
    batch_log_interval: int = 10,
) -> tuple[dict[str, str], dict[str, str]]:
    """Generate all summaries in one pass — one LLM call per metric.

    Produces both canonical-level and transformation-level summaries
    in a single call, roughly 3x faster than separate passes.

    Args:
        builder: The graph builder with nodes and edges populated.
        llm_backend: An object with generate(prompt) -> str method.
        batch_log_interval: Log progress every N metrics.

    Returns:
        Tuple of (canonical_summaries, transform_summaries) where each
        is a dict of node_id -> summary text.
    """
    import json as _json

    traverser = GraphTraverser(builder.nodes, builder.edges)

    canonical_summaries: dict[str, str] = {}
    transform_summaries: dict[str, str] = {}

    canonical_nodes = [
        n for n in builder.nodes.values()
        if n.layer == NodeLayer.CANONICAL
    ]

    logger.info("Generating combined summaries for %d canonical nodes", len(canonical_nodes))
    skipped = 0

    for i, node in enumerate(canonical_nodes):
        metric_id = node.node_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)

        if not subgraph:
            skipped += 1
            continue

        transforms = [
            t for t in subgraph.get("transformations", [])
            if t.name != "__final_select__"
        ]

        if not transforms and not subgraph.get("technical"):
            skipped += 1
            continue

        # Build steps text
        steps_parts = []
        for t_node in transforms:
            fragment = t_node.properties.get("sql_fragment", "")
            if len(fragment) > 800:
                fragment = fragment[:800] + "... (truncated)"
            steps_parts.append(f"Step '{t_node.name}':\n{fragment}")

        # Build tables text
        tables_parts = []
        for t_node in subgraph.get("technical", []):
            if t_node.properties.get("column") is None:
                desc = t_node.description or "No description available"
                tables_parts.append(f"- {t_node.name}: {desc}")

        steps_text = "\n\n".join(steps_parts) if steps_parts else "No named logic steps"
        tables_text = "\n".join(tables_parts[:15]) if tables_parts else "No source tables identified"
        if len(tables_parts) > 15:
            tables_text += f"\n- ... and {len(tables_parts) - 15} more tables"

        prompt = COMBINED_PROMPT.format(
            metric_name=node.name,
            steps=steps_text,
            tables=tables_text,
        )

        try:
            response = llm_backend.generate(prompt)

            # Clean up markdown code fences
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                lines = [line for line in lines if not line.strip().startswith("```")]
                response = "\n".join(lines).strip()

            parsed_response = _json.loads(response)

            # Extract canonical summary
            metric_summary = parsed_response.get("metric_summary", "")
            if metric_summary:
                canonical_summaries[node.node_id] = metric_summary

            # Extract per-step summaries
            step_sums = parsed_response.get("step_summaries", {})
            for t_node in transforms:
                if t_node.name in step_sums:
                    transform_summaries[t_node.node_id] = step_sums[t_node.name]

        except _json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON response for %s: %s", metric_id, e)
            if response and len(response) > 20:
                canonical_summaries[node.node_id] = response[:500]
        except Exception as e:
            logger.warning("Failed to summarize %s: %s", metric_id, e)

        if (i + 1) % batch_log_interval == 0:
            logger.info("  Processed %d/%d metrics (%d skipped)",
                       i + 1, len(canonical_nodes), skipped)

    logger.info(
        "Generated %d canonical summaries, %d transform summaries (%d metrics skipped)",
        len(canonical_summaries), len(transform_summaries), skipped,
    )
    return canonical_summaries, transform_summaries


def apply_summaries(builder: GraphBuilder, summaries: dict[str, str]) -> int:
    """Apply generated summaries back to graph nodes.

    Stores summaries in the node's properties as 'summary' and also
    updates the node's description field for canonical nodes.

    Args:
        builder: The graph builder to update.
        summaries: Dict of node_id -> summary text.

    Returns:
        Number of nodes updated.
    """
    updated = 0
    for node_id, summary in summaries.items():
        if node_id in builder.nodes and summary:
            builder.nodes[node_id].properties["summary"] = summary
            # For canonical nodes, also set the description
            if builder.nodes[node_id].layer == NodeLayer.CANONICAL:
                builder.nodes[node_id].description = summary
            updated += 1

    logger.info("Applied summaries to %d nodes", updated)
    return updated
