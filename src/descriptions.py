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
from dataclasses import dataclass, field
from typing import Callable

from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.models import EdgeType, NodeLayer

STEP_PROMPT = (
    "You are documenting a certified business metric's calculation step "
    "for a business audience.\n"
    "Step name: {name}\n"
    "{deps_block}"
    "SQL for THIS step:\n{fragment}\n\n"
    "Write ONE sentence (max 40 words) stating what this step produces in "
    "business terms — the population, filter, measure, or join it "
    "contributes. Ground every claim in the SQL above; describe THIS step "
    "only, not its dependencies. No SQL keywords, no table names unless "
    "business-meaningful, no patient identifiers, no preamble."
)

METRIC_PROMPT = (
    "You are documenting the certified business metric {metric_name}.\n"
    "Its calculation is assembled from these final steps (each already "
    "described in business terms):\n{roots_block}\n"
    "It draws on {step_count} calculation steps in total.\n\n"
    "Write a concise business description: first, one sentence stating the "
    "business purpose (why it exists, what decisions it supports). Then a "
    "blank line, then 'Business logic:' followed by 3-6 bullets covering "
    "the population included, time windows, clinical criteria or "
    "thresholds, and how the outcome is calculated — in business terms, "
    "grounded ONLY in the step descriptions above. No greetings, no "
    "markdown headers, no bold, no invented details."
)


def step_content_hash(fragment: str, dep_names: "list[str]") -> str:
    payload = (fragment or "") + "\n--deps--\n" + "\n".join(sorted(dep_names))
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


@dataclass
class DescriptionResult:
    descriptions: "dict[str, str]" = field(default_factory=dict)  # node_id -> text
    cache_hits: int = 0
    generated: int = 0
    failed: "list[str]" = field(default_factory=list)


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


def build_step_prompt(name: str, fragment: str, deps: "list[tuple[str, str]]") -> str:
    if deps:
        lines = "\n".join(f"- {n}: {d}" for n, d in deps)
        deps_block = f"It builds on these already-described steps:\n{lines}\n\n"
    else:
        deps_block = ""
    return STEP_PROMPT.format(name=name, deps_block=deps_block, fragment=fragment or "(none)")


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
    only_missing: bool = True,
) -> DescriptionResult:
    """Walk the DAG bottom-up; describe steps, then compose metrics.

    cache maps step_content_hash -> description and is mutated in place —
    the caller persists it (Delta table on Fabric, JSON locally). Metric
    descriptions are not cached: they are cheap (one call each) and depend
    on their whole step set.
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

    described: "dict[str, str]" = {}

    for step_id in topological_step_order(nodes, edges):
        node = nodes[step_id]
        if only_missing and (node.description or "").strip():
            described[step_id] = node.description
            continue
        fragment = node.properties.get("sql_fragment", "")
        dep_names = [nodes[d].name for d in dep_map.get(step_id, []) if d in nodes]
        key = step_content_hash(fragment, dep_names)
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
            text = describe(build_step_prompt(node.name, fragment, deps)).strip()
        except Exception:  # noqa: BLE001 — one bad step must not kill the batch
            result.failed.append(step_id)
            continue
        if not text:
            result.failed.append(step_id)
            continue
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
        if only_missing and (node.description or "").strip():
            continue
        metric_id = node_id.replace("canonical:", "")
        roots = [
            (nodes[r].name, described.get(r, ""))
            for r in roots_map.get(node_id, []) if r in nodes
        ]
        if not roots:
            result.failed.append(node_id)
            continue
        prompt = build_metric_prompt(
            node.name, roots, step_count_by_metric.get(metric_id, len(roots))
        )
        try:
            text = describe(prompt).strip()
        except Exception:  # noqa: BLE001
            result.failed.append(node_id)
            continue
        if not text:
            result.failed.append(node_id)
            continue
        result.descriptions[node_id] = text
        result.generated += 1

    return result
