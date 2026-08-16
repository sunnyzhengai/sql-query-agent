"""Step 12: parse semantic-model TMDL into landing-table rows (ADR 0040).

Input: TmdlFile records from any source profile (folder / devops_git).
Output rows for three input tables:

  input_report_sources  — partition lineage: which SQL object each PBI
                          table executes (deterministic, from the M expr)
  input_dax_expressions — measures + calculated columns (the DAX half of
                          the business logic)
  input_metric_names    — derived business names: a report whose model
                          executes exactly ONE SQL object names that
                          metric. Anything else is skipped and reported,
                          never guessed (ADR 0005).

Logic relations asserted here:
- Every emitted metric-name row cites a report present in report rows.
- Every DAX row belongs to a report seen in the input files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from src.extractor.devops_tmdl import parse_tmdl_dax, parse_tmdl_partition
from src.extractor.tmdl_source import TmdlFile


@dataclass
class SemanticModelsOutput:
    report_source_rows: "list[dict]"
    dax_rows: "list[dict]"
    metric_name_rows: "list[dict]"
    reports_seen: "list[str]"
    names_skipped: "list[str]" = field(default_factory=list)


# 'Table'[Column] or Table[Column] — the table part is REQUIRED. A bare
# [X] is ambiguous in DAX (same-table column OR measure reference), so it
# is deliberately not extracted: deterministic-only (ADR 0040).
_DAX_QUALIFIED_REF = re.compile(
    r"(?:'(?P<quoted>[^']+)'|(?<![\w\]])(?P<bare>[A-Za-z_][\w]*))\[(?P<column>[^\[\]]+)\]"
)


def extract_dax_column_refs(expression: str) -> "list[tuple[str, str]]":
    """Table-qualified column references in a DAX expression, in order."""
    refs = []
    for m in _DAX_QUALIFIED_REF.finditer(expression):
        table = m.group("quoted") or m.group("bare")
        refs.append((table, m.group("column")))
    return refs


def semantic_models_step(
    tmdl_files: "Iterable[TmdlFile]", scan_timestamp: str = ""
) -> SemanticModelsOutput:
    report_source_rows: "list[dict]" = []
    dax_rows: "list[dict]" = []
    sources_by_report: "dict[str, list[dict]]" = {}
    reports_seen: "list[str]" = []

    for f in tmdl_files:
        if f.report_name not in sources_by_report:
            sources_by_report[f.report_name] = []
            reports_seen.append(f.report_name)

        source = parse_tmdl_partition(f.content, f.table_name)
        if source:
            row = {
                "report_name": f.report_name,
                "pbi_table": source.table_name,
                "server": source.server,
                "database_name": source.database,
                "schema_name": source.schema,
                "sql_object": source.sql_object,
                "sql_object_type": source.sql_object_type,
                "repo_name": f.repo_name,
                "semantic_model_path": f.semantic_model_path,
                "extracted_at": scan_timestamp,
            }
            report_source_rows.append(row)
            sources_by_report[f.report_name].append(row)

        for dax in parse_tmdl_dax(f.content, f.table_name):
            dax_rows.append({
                "report_name": f.report_name,
                "pbi_table": dax.table_name,
                "name": dax.name,
                "expression": dax.expression,
                "expression_type": dax.expression_type,
            })

    metric_name_rows, names_skipped = _derive_metric_names(
        sources_by_report, scan_timestamp
    )

    # Logic relations.
    report_set = set(reports_seen)
    assert all(r["report_name"] in report_set for r in metric_name_rows)
    assert all(r["report_name"] in report_set for r in dax_rows)

    return SemanticModelsOutput(
        report_source_rows=report_source_rows,
        dax_rows=dax_rows,
        metric_name_rows=metric_name_rows,
        reports_seen=reports_seen,
        names_skipped=names_skipped,
    )


def _derive_metric_names(
    sources_by_report: "dict[str, list[dict]]", scan_timestamp: str
) -> "tuple[list[dict], list[str]]":
    rows: "list[dict]" = []
    skipped: "list[str]" = []
    for report_name, sources in sources_by_report.items():
        # Only procs/views name metrics — a DirectLake TABLE source is
        # lineage, not a metric identity.
        real = [
            s for s in sources
            if s["sql_object"] and s["sql_object_type"] in ("View", "StoredProcedure")
        ]
        distinct = {
            (s["schema_name"], s["sql_object"]): s for s in real
        }
        if len(distinct) != 1:
            skipped.append(
                f"{report_name}: {len(distinct)} distinct SQL objects — "
                f"a business name needs exactly one; qualify manually"
            )
            continue
        src = next(iter(distinct.values()))
        metric_id = (
            f"{src['schema_name']}.{src['sql_object']}"
            if src["schema_name"] else src["sql_object"]
        )
        rows.append({
            "metric_id": metric_id,
            "business_name": report_name,
            "source": "pbi_report",
            "report_name": report_name,
            "report_url": "",
            "assigned_date": scan_timestamp,
        })
    return rows, skipped
