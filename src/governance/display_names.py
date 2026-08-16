"""Business-friendly metric display names (from PBI lineage or manual entry).

A proc name like USP_IP_SEPSIS_COMPLIANCE is developer vocabulary; the
report built on it ("Sepsis Compliance Dashboard") is how the business
knows the metric. This module applies a metric_id -> business_name
mapping (input_metric_names) onto canonical graph nodes, from where it
flows to output_metric_logic and the LPG export.

Matching follows ADR 0016 (case-insensitive, fold to upper) and ADR 0005
(refuse over guess): records may name a metric by qualified metric_id or
bare object name, but a bare name that collides across schemas is
SKIPPED and reported, never guessed.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Iterable

from src.graph.builder import GraphBuilder
from src.models import NodeLayer

logger = logging.getLogger(__name__)


def _fold(name: str) -> str:
    return (name or "").strip().upper()


def apply_business_names(
    builder: GraphBuilder,
    records: "Iterable[dict[str, Any]]",
) -> "tuple[int, list[str]]":
    """Set business_name on canonical nodes. Returns (applied, skipped).

    records: dicts with metric_id (qualified or bare) and business_name;
    optional source (pbi_report | manual | ...) kept for provenance.
    Skipped entries are ambiguous bare names or unknown metrics.
    """
    canonical = {
        node.node_id.removeprefix("canonical:"): node
        for node in builder.nodes.values()
        if node.layer == NodeLayer.CANONICAL
    }
    by_qualified = {_fold(mid): mid for mid in canonical}
    bare_map: "dict[str, list[str]]" = {}
    for mid in canonical:
        bare = mid.split(".")[-1]
        bare_map.setdefault(_fold(bare), []).append(mid)

    applied = 0
    skipped: "list[str]" = []
    for r in records:
        ref = _fold(r.get("metric_id", ""))
        name = (r.get("business_name") or "").strip()
        if not ref or not name:
            continue
        target = by_qualified.get(ref)
        if target is None:
            candidates = bare_map.get(ref, [])
            if len(candidates) == 1:
                target = candidates[0]
            elif len(candidates) > 1:
                skipped.append(
                    f"{r.get('metric_id')}: bare name matches {len(candidates)} "
                    f"schemas ({', '.join(sorted(candidates))}) — qualify it"
                )
                continue
            else:
                skipped.append(f"{r.get('metric_id')}: no such metric")
                continue
        node = canonical[target]
        node.properties["business_name"] = name
        if r.get("source"):
            node.properties["business_name_source"] = r["source"]
        if r.get("report_name"):
            node.properties["report_name"] = r["report_name"]
        if r.get("report_url"):
            node.properties["report_url"] = r["report_url"]
        applied += 1

    if skipped:
        logger.warning("Business names skipped: %s", "; ".join(skipped))
    logger.info("Applied %d business names to canonical nodes", applied)
    return applied, skipped


def friendly_name_from_report(report_name: str) -> str:
    """Report/folder name -> business-friendly display name.

    'IP_Sepsis_Compliance_Dashboard' -> 'IP Sepsis Compliance Dashboard'.
    Purely mechanical (separators to spaces, collapse whitespace) — no
    vocabulary invention; the report author chose these words.
    (Moved from scripts/extract_pbix_sources.py when pbix-cracking was
    deleted — TMDL supersedes it in every path.)
    """
    return " ".join(re.split(r"[_\-]+", report_name)).strip()
