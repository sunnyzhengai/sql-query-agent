"""Bottom-up description generation over the calculation DAG (ADR 0019).

A CTE is the smallest certified unit of business definition. Descriptions
are generated in topological order — every step's direct dependencies are
described before the step itself — then each metric's description is
composed from its ROOT steps' descriptions (summaries of summaries, never
raw SQL walls).

This module is pure orchestration: ordering, prompts, content-hash caching.
The LLM is a callback `describe(prompt) -> str`, so tests run with a fake,
devtools plugs in a local OpenAI-compatible endpoint, and production plugs
in the customer's Azure OpenAI — the Data Agent is a CONSUMER of these
descriptions, never the generator.

Grounding rule: a step's prompt contains its OWN sql fragment plus only the
names+descriptions of its direct dependencies (context, not content), so a
bad description cannot cascade up the chain.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Callable

from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.models import EdgeType, NodeLayer

# Bump when a prompt changes: the version is part of every cache key,
# so a prompt upgrade automatically regenerates every description on
# the next 07 run — no flags, no manual cache wipe (live find
# 2026-08-13: vague descriptions survived a rerun because the cache
# key knew only the SQL, not the prompt that read it).
# v3 (live find 2026-08-14): v2 kept actual values but also kept raw
# warehouse identifiers — the fix is grounded translation material
# (the data dictionary the graph already holds) plus a ban on raw
# identifiers in the output.
PROMPT_VERSION = "3"

STEP_PROMPT = (
    "You are documenting a certified business metric's calculation step "
    "for a business audience of clinicians and executives.\n"
    "Step name: {name}\n"
    "{deps_block}"
    "{dict_block}"
    "SQL for THIS step:\n{fragment}\n\n"
    "Write ONE sentence (max 30 words) stating what this step produces "
    "in business terms. Then, if the SQL makes decisions, add one line "
    "per decision, each starting with '- ': filters, inclusion and "
    "exclusion rules, code lists, thresholds, time windows, and joins "
    "that restrict the population. State each decision in plain "
    "business language and keep the literal VALUES that define it — "
    "codes, numbers, statuses, hours — with the business meaning "
    "beside each code when the data dictionary above provides one. "
    "NEVER show raw table or column identifiers or temp-table names "
    "in the output — use the dictionary description or a plain phrase "
    "instead, and refer to earlier steps by what they produce. Never "
    "write vague fillers such as 'specific', 'specified', 'certain', "
    "or 'various' in place of a value. Ground every line in the SQL "
    "above; describe THIS step only, not its dependencies. No patient "
    "identifiers, no preamble."
)

METRIC_PROMPT = (
    "You are documenting the certified business metric {metric_name}.\n"
    "Its calculation is assembled from these final steps (each already "
    "described in business terms):\n{roots_block}\n"
    "It draws on {step_count} calculation steps in total.\n\n"
    "Write a concise business description: first, one sentence stating "
    "what this metric reports or measures, grounded strictly in the step "
    "descriptions and the metric name. Then a blank line, then "
    "'Business logic:' followed by 3-6 bullets covering the population "
    "included, time windows, clinical criteria or thresholds, and how the "
    "outcome is calculated — in business terms, grounded ONLY in the step "
    "descriptions above. Bullets must keep the actual values, codes, "
    "thresholds, and time windows the step descriptions name — never "
    "generalize them away, and never write vague fillers such as "
    "'specific', 'specified', 'certain', or 'various' in place of a "
    "value. Do not state purposes, benefits, or decisions "
    "the metric supports unless a step description states them — no "
    "filler like 'supports decision-making' or 'improves outcomes'. "
    "Plain text only: no greetings, no markdown headers, no bold, no "
    "trailing spaces, no invented details."
)

# Observation only (never a retry loop): generated text that hides a
# value behind a filler word is flagged for the run report / dashboard.
_VAGUE_FILLERS = re.compile(
    r"\b(specific|specified|certain|various)\b", re.IGNORECASE)

# Raw-identifier smell in OUTPUT text: SNAKE_CASE_CAPS columns,
# #temp tables, backticked/dotted code refs (live find 2026-08-14:
# ADT_DEPARTMENT_ID / #SDX / `pd.PatEncCSNID` all over the workbench).
_RAW_IDENTIFIERS = re.compile(
    r"(#\w+|`[^`]+`|\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b)")


def step_content_hash(fragment: str, dep_names: "list[str]",
                      dict_lines: "list[str] | None" = None) -> str:
    payload = (
        PROMPT_VERSION + "\n" + (fragment or "")
        + "\n--deps--\n" + "\n".join(sorted(dep_names))
        + "\n--dict--\n" + "\n".join(dict_lines or [])
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def metric_content_hash(metric_name: str, roots: "list[tuple[str, str]]",
                        step_count: int) -> str:
    payload = (
        PROMPT_VERSION + "\n" + metric_name + f"\n{step_count}\n"
        + "\n".join(f"{n}\t{d}" for n, d in sorted(roots))
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


@dataclass
class DescriptionResult:
    descriptions: "dict[str, str]" = field(default_factory=dict)  # node_id -> text
    cache_hits: int = 0
    generated: int = 0
    failed: "list[str]" = field(default_factory=list)
    vague: "list[str]" = field(default_factory=list)   # filler-word flags
    jargon: "list[str]" = field(default_factory=list)  # raw-identifier flags


def topological_step_order(nodes: dict, edges: list) -> "list[str]":
    """Transformation node_ids, every direct dependency before its dependent.

    DEPENDS_ON points dependent -> dependency, so emit in DFS post-order.
    Cycles (shouldn't exist; parser output is a DAG) are broken at the
    back-edge — the step is emitted once, grounded in its own fragment.
    """
    dependencies: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TRANSFORM:
            dependencies.setdefault(e.source_id, []).append(e.target_id)

    ordered: "list[str]" = []
    done: "set[str]" = set()
    in_progress: "set[str]" = set()

    def visit(node_id: str) -> None:
        if node_id in done or node_id in in_progress:
            return
        in_progress.add(node_id)
        for dep in dependencies.get(node_id, []):
            visit(dep)
        in_progress.discard(node_id)
        done.add(node_id)
        ordered.append(node_id)

    for node_id, node in sorted(nodes.items()):
        if node.layer == NodeLayer.TRANSFORMATION:
            visit(node_id)
    return ordered


MAX_DICT_LINES = 30


def build_step_prompt(
    name: str, fragment: str, deps: "list[tuple[str, str]]",
    dict_lines: "list[str] | None" = None,
) -> str:
    if deps:
        lines = "\n".join(f"- {n}: {d}" for n, d in deps)
        deps_block = f"It builds on these already-described steps:\n{lines}\n\n"
    else:
        deps_block = ""
    if dict_lines:
        entries = "\n".join(dict_lines[:MAX_DICT_LINES])
        dict_block = (
            "Data dictionary for what this step touches (translate "
            f"identifiers using these):\n{entries}\n\n"
        )
    else:
        dict_block = ""
    return STEP_PROMPT.format(name=name, deps_block=deps_block,
                              dict_block=dict_block,
                              fragment=fragment or "(none)")


def dictionary_for_step(
    step_id: str, nodes: dict, tech_map: "dict[str, list[str]]",
    columns_map: "dict[str, list[str]]", fragment: str,
) -> "list[str]":
    """Dictionary lines for the tables a step touches, plus only the
    COLUMNS the fragment actually references (whole-table column lists
    would drown the prompt). Pure selection — the dictionary text
    itself is the customer's own, from graph_nodes."""
    frag = (fragment or "").lower()
    lines: "list[str]" = []
    for table_id in sorted(tech_map.get(step_id, [])):
        table = nodes.get(table_id)
        if table is None:
            continue
        if (table.description or "").strip():
            lines.append(f"- {table.name}: {table.description.strip()}")
        for col_id in sorted(columns_map.get(table_id, [])):
            col = nodes.get(col_id)
            if col is None or not (col.description or "").strip():
                continue
            if col.name.lower() in frag:
                lines.append(f"  - {col.name}: {col.description.strip()}")
    return lines


def build_metric_prompt(metric_name: str, roots: "list[tuple[str, str]]", step_count: int) -> str:
    roots_block = "\n".join(f"- {n}: {d}" for n, d in roots) or "- (no described steps)"
    return METRIC_PROMPT.format(
        metric_name=metric_name, roots_block=roots_block, step_count=step_count
    )


def generate_descriptions(
    nodes_rows: "list[dict]",
    edges_rows: "list[dict]",
    describe: "Callable[[str], str]",
    cache: "dict[str, str] | None" = None,
) -> DescriptionResult:
    """Walk the DAG bottom-up; describe steps, then compose metrics.

    cache maps content_hash -> description and is mutated in place — the
    caller persists it (Delta table on Fabric, JSON locally). The cache
    is the ONLY regeneration authority: keys include PROMPT_VERSION and
    the exact inputs, so a description regenerates precisely when its
    SQL, its dependencies, or the prompt changed — an existing text on
    the node never blocks an upgrade from reaching it.
    """
    nodes = rows_to_nodes(nodes_rows)
    edges = rows_to_edges(edges_rows)
    cache = cache if cache is not None else {}
    result = DescriptionResult()

    dep_map: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TRANSFORM:
            dep_map.setdefault(e.source_id, []).append(e.target_id)
    roots_map: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.CANONICAL_TO_TRANSFORM:
            roots_map.setdefault(e.source_id, []).append(e.target_id)
    tech_map: "dict[str, list[str]]" = {}       # step -> touched tables
    columns_map: "dict[str, list[str]]" = {}    # table -> its columns
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TECHNICAL:
            tech_map.setdefault(e.source_id, []).append(e.target_id)
        elif e.edge_type == EdgeType.TABLE_TO_COLUMN:
            columns_map.setdefault(e.source_id, []).append(e.target_id)

    described: "dict[str, str]" = {}

    for step_id in topological_step_order(nodes, edges):
        node = nodes[step_id]
        fragment = node.properties.get("sql_fragment", "")
        dep_names = [nodes[d].name for d in dep_map.get(step_id, []) if d in nodes]
        dict_lines = dictionary_for_step(
            step_id, nodes, tech_map, columns_map, fragment)
        key = step_content_hash(fragment, dep_names, dict_lines)
        if key in cache:
            described[step_id] = cache[key]
            result.descriptions[step_id] = cache[key]
            result.cache_hits += 1
            continue
        deps = [
            (nodes[d].name, described.get(d, ""))
            for d in dep_map.get(step_id, []) if d in nodes
        ]
        try:
            text = describe(build_step_prompt(
                node.name, fragment, deps, dict_lines)).strip()
        except Exception:  # noqa: BLE001 — one bad step must not kill the batch
            result.failed.append(step_id)
            continue
        if not text:
            result.failed.append(step_id)
            continue
        if _VAGUE_FILLERS.search(text):
            result.vague.append(step_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(step_id)
        cache[key] = text
        described[step_id] = text
        result.descriptions[step_id] = text
        result.generated += 1

    # Metrics: composed from ROOT step descriptions (raw roots-only edges)
    step_count_by_metric: "dict[str, int]" = {}
    for node_id, node in nodes.items():
        if node.layer == NodeLayer.TRANSFORMATION:
            metric_id = node.properties.get("metric_id", "")
            step_count_by_metric[metric_id] = step_count_by_metric.get(metric_id, 0) + 1

    for node_id, node in sorted(nodes.items()):
        if node.layer != NodeLayer.CANONICAL:
            continue
        metric_id = node_id.replace("canonical:", "")
        roots = [
            (nodes[r].name, described.get(r, ""))
            for r in roots_map.get(node_id, []) if r in nodes
        ]
        if not roots:
            result.failed.append(node_id)
            continue
        step_count = step_count_by_metric.get(metric_id, len(roots))
        key = metric_content_hash(node.name, roots, step_count)
        if key in cache:
            result.descriptions[node_id] = cache[key]
            result.cache_hits += 1
            continue
        prompt = build_metric_prompt(node.name, roots, step_count)
        try:
            text = describe(prompt).strip()
        except Exception:  # noqa: BLE001
            result.failed.append(node_id)
            continue
        if not text:
            result.failed.append(node_id)
            continue
        if _VAGUE_FILLERS.search(text):
            result.vague.append(node_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(node_id)
        cache[key] = text
        result.descriptions[node_id] = text
        result.generated += 1

    return result
