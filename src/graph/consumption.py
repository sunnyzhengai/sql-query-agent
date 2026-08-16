"""Wire the consumption layer (reports + measures) into the graph (ADR 0040).

Everything here is deterministic. A report's partition lineage names the
SQL object it executes; resolution to a canonical metric follows ADR 0016
folding (qualified name, else unambiguous bare name) — ambiguous or
unknown objects are SKIPPED and reported, never guessed (ADR 0005). DAX
column references wire measure -> technical column only when the
table-qualified reference resolves through the report's own partition
sources to a column node that actually exists.
"""

from __future__ import annotations

from typing import Any, Iterable

from src.graph.builder import GraphBuilder
from src.models import EdgeType, NodeLayer
from src.parser.identity import fold_identifier
from src.steps.semantic_models import extract_dax_column_refs


def _canonical_index(builder: GraphBuilder) -> "tuple[dict, dict]":
    """(folded qualified metric_id -> node_id, folded bare name -> [node_id])."""
    qualified: "dict[str, str]" = {}
    bare: "dict[str, list[str]]" = {}
    for node in builder.nodes.values():
        if node.layer != NodeLayer.CANONICAL:
            continue
        metric_id = node.node_id.removeprefix("canonical:")
        qualified[fold_identifier(metric_id)] = node.node_id
        bare.setdefault(fold_identifier(metric_id.split(".")[-1]), []).append(node.node_id)
    return qualified, bare


def _resolve_canonical(
    schema_name: str, sql_object: str, qualified: dict, bare: dict
) -> "str | None":
    if schema_name:
        hit = qualified.get(fold_identifier(f"{schema_name}.{sql_object}"))
        if hit:
            return hit
    candidates = bare.get(fold_identifier(sql_object), [])
    return candidates[0] if len(candidates) == 1 else None


def wire_consumption_layer(
    builder: GraphBuilder,
    report_source_records: "Iterable[dict[str, Any]]",
    dax_records: "Iterable[dict[str, Any]]",
) -> "tuple[int, int, list[str]]":
    """Add report/measure nodes and their edges.

    Returns (reports_added, measures_added, skipped) where skipped lists
    human-readable reasons for every lineage that could not be resolved.
    """
    qualified, bare = _canonical_index(builder)
    skipped: "list[str]" = []

    # (report, pbi_table) -> resolved source object, for DAX column refs
    table_source: "dict[tuple[str, str], dict[str, Any]]" = {}
    reports: "set[str]" = set()
    linked_pairs: "set[tuple[str, str]]" = set()

    for r in report_source_records:
        report_name = r["report_name"]
        reports.add(report_name)
        builder.add_report_node(
            report_name,
            repo_name=r.get("repo_name") or "",
            semantic_model_path=r.get("semantic_model_path") or "",
        )
        if not r.get("sql_object") or r.get("sql_object_type") == "InlineSQL":
            skipped.append(f"{report_name}/{r.get('pbi_table')}: inline SQL — no object to link")
            continue
        table_source[(report_name, r.get("pbi_table") or "")] = r
        report_id = f"report:{fold_identifier(report_name)}"

        if r.get("sql_object_type") == "Table":
            # DirectLake (ADR 0040 pattern 5): the partition names a
            # warehouse TABLE — attach to the technical layer.
            tech_id = (
                f"tech:{fold_identifier(r.get('schema_name') or 'dbo')}."
                f"{fold_identifier(r['sql_object'])}"
            )
            if tech_id not in builder.nodes:
                skipped.append(
                    f"{report_name}/{r.get('pbi_table')}: DirectLake table "
                    f"{r['sql_object']} not in the dictionary — not linked"
                )
                continue
            if (report_id, tech_id) not in linked_pairs:
                linked_pairs.add((report_id, tech_id))
                builder.add_edge(report_id, tech_id, EdgeType.REPORT_TO_TECHNICAL)
            continue

        target = _resolve_canonical(
            r.get("schema_name") or "", r["sql_object"], qualified, bare
        )
        if target is None:
            skipped.append(
                f"{report_name}/{r.get('pbi_table')}: {r['sql_object']} is not "
                f"an unambiguous metric in this corpus — not linked"
            )
            continue
        if (report_id, target) not in linked_pairs:
            linked_pairs.add((report_id, target))
            builder.add_edge(report_id, target, EdgeType.REPORT_TO_CANONICAL)

    measures_added = 0
    for d in dax_records:
        report_name = d["report_name"]
        reports.add(report_name)
        measure_id = builder.add_measure_node(
            report_name, d.get("pbi_table") or "", d["name"],
            d["expression"], d.get("expression_type") or "measure",
        )
        measures_added += 1
        for ref_table, ref_column in extract_dax_column_refs(d["expression"]):
            src = table_source.get((report_name, ref_table))
            if src is None:
                continue  # reference to a table with no resolved SQL source
            col_id = (
                f"tech:{fold_identifier(src.get('schema_name') or 'dbo')}."
                f"{fold_identifier(src['sql_object'])}.{fold_identifier(ref_column)}"
            )
            if col_id in builder.nodes:
                builder.add_edge(measure_id, col_id, EdgeType.MEASURE_TO_COLUMN)

    return len(reports), measures_added, skipped
