"""Build the metric_logic flat table from the knowledge graph.

Traverses the graph for each canonical metric and flattens:
- Calculation logic (SQL fragments from transformation chain)
- Source tables (physical tables with descriptions)
- Steward and developer assignments
- Decision-site summary + counts + twin verdict (Fabric refresh,
  HANDOFF_REMATCH_ROUND4_GOAL / ADR 0020 doctrine: the Data Agent
  answers drill-downs by READING A ROW — single-hop reads it cannot
  get wrong — so the drill-down material is flattened onto the row)

This produces the single-table view that the Data Agent queries.
"""

from __future__ import annotations

from src.graph.traversal import GraphTraverser
from src.models import GraphNode, NodeLayer
from src.parser.identity import fold_identifier
from src.parser.sql_parser import normalize_sql_whitespace
from src.phi_scan import redact, scan_sql

_MAX_DECISION_LINES = 12
_MAX_EXPR_CHARS = 160


def decision_summary_for(
    metric_id: str, decision_rows: "list[dict]"
) -> "str | None":
    """Flatten a metric's decision sites into one readable, PHI-gated
    column. Deterministic order; capped with an honest remainder line
    (no silent truncation)."""
    fold = fold_identifier(metric_id)
    mine = sorted(
        (r for r in decision_rows
         if fold_identifier(str(r.get("metric_id", ""))) == fold
         and r.get("status") == "extracted"
         and r.get("context") in ("where", "having", "join_on",
                                  "case_when")),
        key=lambda r: (str(r.get("step_name", "")),
                       str(r.get("site_id", ""))),
    )
    if not mine:
        return None
    lines = []
    for r in mine[:_MAX_DECISION_LINES]:
        expr = str(r.get("expression_sql") or "").strip()
        findings = [f for f in scan_sql(metric_id, expr)
                    if f.disposition == "redact"]
        if findings:
            expr = redact(expr, findings)
        expr = normalize_sql_whitespace(expr)[:_MAX_EXPR_CHARS]
        lines.append(f"{r.get('step_name')} [{r.get('context')}]: {expr}")
    if len(mine) > _MAX_DECISION_LINES:
        lines.append(f"(+{len(mine) - _MAX_DECISION_LINES} more decision "
                     "sites — see graph_decision_sites)")
    return "\n".join(lines)


def build_metric_logic_rows(
    nodes: dict[str, GraphNode],
    edges: list,
    decision_rows: "list[dict] | None" = None,
) -> list[tuple]:
    """Build metric_logic row tuples from the in-memory graph.

    Returns list of tuples matching the METRIC_LOGIC schema:
    (metric_id, metric_name, business_name, report_name, report_url,
     description, steward, developer, transform_count, calculation_logic,
     source_tables, table_descriptions, table_count, decision_summary)
    """
    traverser = GraphTraverser(nodes, edges)

    canonical_nodes = [n for n in nodes.values() if n.layer == NodeLayer.CANONICAL]
    rows = []

    for canonical in canonical_nodes:
        metric_id = canonical.node_id.removeprefix("canonical:")
        subgraph = traverser.get_metric_subgraph(metric_id)
        if not subgraph:
            continue

        steward = canonical.properties.get("steward")
        developer = canonical.properties.get("developer")

        transforms = subgraph.get("transformations", [])
        sql_fragments = []
        for t in transforms:
            frag = t.properties.get("sql_fragment", "")
            if frag:
                frag = normalize_sql_whitespace(frag)
                sql_fragments.append(f"-- {t.name}\n{frag}")

        combined_logic = "\n\n".join(sql_fragments) if sql_fragments else None

        tech_nodes = subgraph.get("technical", [])
        tables = sorted(set(
            t.name for t in tech_nodes if t.properties.get("column") is None
        ))
        tables_str = ", ".join(tables) if tables else None

        table_descs = []
        for t in tech_nodes:
            if t.properties.get("column") is None and t.description:
                table_descs.append(f"{t.name}: {t.description}")
        table_descs_str = "; ".join(table_descs) if table_descs else None

        rows.append((
            metric_id, canonical.name,
            canonical.properties.get("business_name"),
            canonical.properties.get("report_name"),
            canonical.properties.get("report_url"),
            canonical.description,
            steward, developer,
            len(transforms), combined_logic,
            tables_str, table_descs_str,
            len(tables),
            decision_summary_for(metric_id, decision_rows or []),
        ))

    return rows
