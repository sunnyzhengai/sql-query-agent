"""gov_publish_log rows — every push to a DG catalog, durably (2026-08-11).

Adapters return PublishResult objects; notebooks 08/09 pass them here
and append the rows, so 'what did we push to Purview/Collibra and did
it land?' is answerable forever. Pure: no Spark, no HTTP.
"""

from __future__ import annotations

from src.adapters.base import BulkPublishResult, PublishResult

TARGETS = ("purview", "collibra", "fabric_pbi")
KINDS = ("asset", "glossary_term", "report_description")


def publish_log_rows(
    results: "list[PublishResult] | BulkPublishResult",
    target: str,
    kind: str,
    run_id: str,
    published_at: str,
) -> "list[dict]":
    """Project publish results onto the gov_publish_log contract."""
    if target not in TARGETS:
        raise ValueError(f"target must be one of {TARGETS}, got {target!r}")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    if isinstance(results, BulkPublishResult):
        results = results.results
    return [
        {
            "published_at": published_at,
            "run_id": run_id,
            "target": target,
            "kind": kind,
            "asset_id": r.asset_id,
            "name": r.asset_id,
            "status": r.status.value,
            "message": r.message or "",
        }
        for r in results
    ]
