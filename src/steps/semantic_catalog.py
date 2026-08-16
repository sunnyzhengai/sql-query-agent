"""Semantic catalog build step (ADR 0030 L3, probe-verified 2026-08-08).

Composes one searchable "document" per resolution target — metrics,
transformation steps, and business terms — from the graph plus the
governance tables. The Eventhouse ingests these rows and embeds the
search_text in-database (ai_embeddings under user impersonation); this
step never calls an LLM itself, so it is pure and offline-testable.

Search text composition is the tuning surface for retrieval quality:
name + business name + description (+ report and concept vocabulary),
pipe-separated — the same shape the probe validated (readmission phrase
matched at 0.51 similarity vs 0.37 noise).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.graph.serialization import rows_to_nodes
from src.models import NodeLayer

# Kinds are part of the contract: resolution consumers dispatch on them
KIND_METRIC = "metric"
KIND_STEP = "step"
KIND_TERM = "term"
KIND_REPORT = "report"
KIND_MEASURE = "measure"


@dataclass
class SemanticCatalogOutput:
    rows: "list[dict]"           # semantic_catalog rows (emb filled in-engine)
    metric_count: int
    step_count: int
    term_count: int
    report_count: int = 0
    measure_count: int = 0


def _doc(*parts: "str | None") -> str:
    return " | ".join(p.strip() for p in parts if p and p.strip())


def build_semantic_catalog(
    nodes_rows: "list[dict]",
    term_records: "list[dict] | None" = None,
    term_links: "list[dict] | None" = None,
) -> SemanticCatalogOutput:
    """One row per metric, named step, and business term.

    Steps ride under their own node_id so resolution can answer
    definition-grain questions (ADR 0019: the CTE is the smallest
    certified unit); plumbing steps (__final_select__) are excluded —
    they resolve to their metric, not to themselves.
    """
    import json as _json

    nodes = rows_to_nodes(nodes_rows)
    rows: "list[dict]" = []
    metric_count = step_count = term_count = 0
    report_count = measure_count = 0

    for node_id, node in sorted(nodes.items()):
        if node.layer == NodeLayer.CANONICAL:
            metric_id = node_id.removeprefix("canonical:")
            props = node.properties or {}
            rows.append({
                "node_id": node_id,
                "kind": KIND_METRIC,
                "ref": metric_id,
                "name": node.name,
                "business_name": props.get("business_name") or "",
                "search_text": _doc(
                    metric_id, node.name, props.get("business_name"),
                    props.get("report_name"), node.description,
                ),
                "display_text": _doc(
                    props.get("business_name") or node.name, metric_id,
                ),
            })
            metric_count += 1
        elif node.layer == NodeLayer.TRANSFORMATION:
            if node.name.startswith("__"):
                continue  # plumbing, resolves to its metric
            props = node.properties or {}
            metric_id = props.get("metric_id", "")
            # search_text deliberately EXCLUDES metric_id (live find
            # 2026-08-13: identity leak — every step of USP_ED_Sepsis
            # carried the tokens "ED Sepsis", so transfer-timeline
            # steps outscored the sepsis metrics on "ED sepsis"). A
            # step matches when ITS OWN definition matches; finding a
            # metric's steps is retrieve's job, not search's.
            rows.append({
                "node_id": node_id,
                "kind": KIND_STEP,
                "ref": metric_id,
                "name": node.name,
                "business_name": "",
                "search_text": _doc(node.name, node.description),
                "display_text": _doc(node.name, f"step of {metric_id}"),
            })
            step_count += 1
        elif node.layer == NodeLayer.REPORT:
            # Consumption layer (ADR 0040): users ask by dashboard name
            rows.append({
                "node_id": node_id,
                "kind": KIND_REPORT,
                "ref": node.name,
                "name": node.name,
                "business_name": node.name,
                "search_text": _doc(node.name, node.description),
                "display_text": _doc(node.name, "Power BI report"),
            })
            report_count += 1
        elif node.layer == NodeLayer.MEASURE:
            props = node.properties or {}
            # Like steps, search_text excludes the parent report's name
            # (identity-leak lesson 2026-08-13): a measure matches when
            # ITS definition matches; finding a report's measures is the
            # links tool's job, not search's.
            rows.append({
                "node_id": node_id,
                "kind": KIND_MEASURE,
                "ref": props.get("report_name", ""),
                "name": node.name,
                "business_name": "",
                "search_text": _doc(node.name, node.description),
                "display_text": _doc(
                    node.name, f"DAX measure of {props.get('report_name', '')}"
                ),
            })
            measure_count += 1

    links_by_term: "dict[str, list[str]]" = {}
    for link in term_links or []:
        links_by_term.setdefault(link["term_id"], []).append(link["node_ref"])
    for term in term_records or []:
        rows.append({
            "node_id": f"term:{term['term_id']}",
            "kind": KIND_TERM,
            "ref": term["term_id"],
            "name": term["name"],
            "business_name": term["name"],
            "search_text": _doc(
                term["name"], term.get("definition"),
                *links_by_term.get(term["term_id"], []),
            ),
            "display_text": _doc(term["name"], f"{term.get('status', '')} term"),
        })
        term_count += 1

    # Logic relations: unique ids, no empty search docs
    ids = [r["node_id"] for r in rows]
    assert len(ids) == len(set(ids)), "semantic_catalog: duplicate node_ids"
    empty = [r["node_id"] for r in rows if not r["search_text"]]
    assert not empty, f"semantic_catalog: empty search_text for {empty[:5]}"
    _json.dumps(rows[:1])  # rows must be JSON-serializable end to end

    return SemanticCatalogOutput(
        rows=rows,
        metric_count=metric_count,
        step_count=step_count,
        term_count=term_count,
        report_count=report_count,
        measure_count=measure_count,
    )
