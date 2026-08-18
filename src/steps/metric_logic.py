"""Step 04: flatten the graph into the agent's metric_logic table.

Logic relation asserted here: exactly one output row per canonical node.

Freshness (Trust family, gap 2 of the Question Map, 2026-08-18): every
card carries logic_last_changed_at (hash-change of calculation_logic
across runs — the PREVIOUS table is the memory, no extra state) and
source_extracted_at (from the extraction tracker; null on file-drop
routes, and the card says so honestly).
"""

from __future__ import annotations

from src.graph.metric_logic import build_metric_logic_rows
from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.models import NodeLayer
from src.schemas import METRIC_LOGIC

_FRESHNESS_COLUMNS = ("logic_last_changed_at", "source_extracted_at")
_BASE_COLUMNS = [c[0] for c in METRIC_LOGIC["columns"]
                 if c[0] not in _FRESHNESS_COLUMNS]


def apply_freshness(
    rows: "list[dict]",
    previous_rows: "list[dict]",
    extraction_records: "list[dict]",
    run_at: str,
) -> None:
    """Stamp the two Trust columns in place.

    logic_last_changed_at: carried from the previous run while the
    calculation_logic text is unchanged; re-stamped to run_at when it
    differs or the metric is new. source_extracted_at: the extraction
    tracker's timestamp for the object (route 00c); None when the
    corpus arrived by file drop — unknown is stated, never invented.
    """
    prev = {(r.get("metric_id") or "").lower(): r for r in previous_rows}
    extracted: "dict[str, str]" = {}
    for r in extraction_records:
        key = f"{r.get('schema_name', '')}.{r.get('object_name', '')}".lower()
        if r.get("extracted_at"):
            extracted[key] = r["extracted_at"]
    for row in rows:
        key = row["metric_id"].lower()
        p = prev.get(key)
        if (p is not None
                and p.get("calculation_logic") == row.get("calculation_logic")
                and p.get("logic_last_changed_at")):
            row["logic_last_changed_at"] = p["logic_last_changed_at"]
        else:
            row["logic_last_changed_at"] = run_at or None
        row["source_extracted_at"] = extracted.get(key)


def metric_logic_step(
    nodes_rows: "list[dict]",
    edges_rows: "list[dict]",
    previous_rows: "list[dict] | None" = None,
    extraction_records: "list[dict] | None" = None,
    run_at: str = "",
) -> "list[dict]":
    nodes = rows_to_nodes(nodes_rows)
    edges = rows_to_edges(edges_rows)

    tuples = build_metric_logic_rows(nodes, edges)
    rows = [dict(zip(_BASE_COLUMNS, t)) for t in tuples]
    apply_freshness(rows, previous_rows or [], extraction_records or [], run_at)

    canonical_count = sum(1 for n in nodes.values() if n.layer == NodeLayer.CANONICAL)
    assert len(rows) == canonical_count, (
        f"metric_logic_step: {canonical_count} canonical nodes -> {len(rows)} rows"
    )
    assert len({r["metric_id"] for r in rows}) == len(rows), (
        "metric_logic_step: duplicate metric_ids in output"
    )
    return rows
