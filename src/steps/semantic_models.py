"""Step 12: parse semantic-model TMDL into landing-table rows (ADR 0040).

Input: TmdlFile records from any source profile (folder / devops_git).
Output rows for three input tables:

  input_report_sources  — partition lineage: which SQL object each PBI
                          table executes (deterministic, from the M expr)
  input_dax_expressions — measures + calculated columns (the DAX half of
                          the business logic)
  input_metric_names    — derived business names, PROC-KEYED (inverted
                          2026-08-18): a proc consumed by exactly one
                          report — or by several reports that all carry
                          the SAME title — inherits that title. A proc
                          consumed by differently-titled reports is
                          skipped and reported, never guessed (ADR 0005;
                          amends the 1.16.0 first-workspace verdict).

Fallout rows (HANDOFF_FUNNEL_AND_FALLOUT): every collected file that
yields no source row, and every proc that refuses a name, leaves a
structured reason row — silent absence is a contract violation.

Logic relations asserted here:
- Every emitted metric-name row cites a report present in report rows.
- Every DAX row belongs to a report seen in the input files.
- sources + partition-fallout rows account for every input file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from src.extractor.devops_tmdl import (
    classify_partition_fallout,
    parse_tmdl_dax,
    parse_tmdl_partition,
)
from src.extractor.tmdl_source import TmdlFile
from src.governance.display_names import friendly_name_from_report


@dataclass
class SemanticModelsOutput:
    report_source_rows: "list[dict]"
    dax_rows: "list[dict]"
    metric_name_rows: "list[dict]"
    reports_seen: "list[str]"
    names_skipped: "list[str]" = field(default_factory=list)
    fallout_rows: "list[dict]" = field(default_factory=list)


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
    tmdl_files: "Iterable[TmdlFile]",
    scan_timestamp: str = "",
    corpus_metric_ids: "set[str] | None" = None,
) -> SemanticModelsOutput:
    """corpus_metric_ids: metric_ids from input_sql_sources. When given,
    name derivation trusts CORPUS MEMBERSHIP over the TMDL Kind field
    (connectors reach views as Kind='Table'); when None, the legacy
    View/StoredProcedure kind filter applies."""
    report_source_rows: "list[dict]" = []
    dax_rows: "list[dict]" = []
    fallout_rows: "list[dict]" = []
    sources_by_report: "dict[str, list[dict]]" = {}
    reports_seen: "list[str]" = []

    for f in tmdl_files:
        if f.report_name not in sources_by_report:
            sources_by_report[f.report_name] = []
            reports_seen.append(f.report_name)

        source = parse_tmdl_partition(f.content, f.table_name)
        if source is None:
            code, text = classify_partition_fallout(f.content, f.table_name)
            if code == "unrecognized_shape":
                # attach the whitelist-anonymized signature so the shape
                # can be filed and shipped without seeing customer M
                from src.mquery.census import census_file

                row = census_file(f.report_name, f.table_name, f.content)
                text = f"{text} [signature: {row.signature}]"
            fallout_rows.append({
                "stage": "12_partition_parse",
                "entity_id": f"{f.report_name}/{f.table_name}",
                "reason_code": code,
                "reason_text": text,
                "contract_id": "contract:input_report_sources",
            })
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

    metric_name_rows, names_skipped, name_fallout = _derive_metric_names(
        sources_by_report, scan_timestamp, corpus_metric_ids
    )
    fallout_rows.extend(name_fallout)

    # Logic relations. (metric-name rows may list several reports,
    # "; "-joined — every listed report must have been seen.)
    report_set = set(reports_seen)
    assert all(
        name.strip() in report_set
        for r in metric_name_rows for name in r["report_name"].split(";")
    )
    assert all(r["report_name"] in report_set for r in dax_rows)

    return SemanticModelsOutput(
        report_source_rows=report_source_rows,
        dax_rows=dax_rows,
        metric_name_rows=metric_name_rows,
        reports_seen=reports_seen,
        names_skipped=names_skipped,
        fallout_rows=fallout_rows,
    )


def _derive_metric_names(
    sources_by_report: "dict[str, list[dict]]",
    scan_timestamp: str,
    corpus_metric_ids: "set[str] | None" = None,
) -> "tuple[list[dict], list[str], list[dict]]":
    """PROC-KEYED derivation (inverted 2026-08-18, field-driven: the
    report-keyed rule named 228/601 at a live estate because multi-source
    dashboards named nothing).

    For each metric (case-folded identity — amendment 1): the ordered
    distinct set of consuming reports decides. One report — its title is
    the name. Several reports all carrying the SAME title (workspace
    copies) — that title, all consumers listed. Differently-titled
    reports — genuine ambiguity: refuse, list, emit a fallout row
    (supersedes the 1.16.0 first-workspace verdict; refuse-over-guess).
    """
    corpus_fold = (
        {mid.lower(): mid for mid in corpus_metric_ids}
        if corpus_metric_ids is not None else None
    )
    consumers: "dict[str, list[str]]" = {}   # folded metric_id -> reports
    display_id: "dict[str, str]" = {}        # folded -> emitted casing
    for report_name, sources in sources_by_report.items():
        for s in sources:
            if not s["sql_object"]:
                continue
            qualified = (
                f"{s['schema_name']}.{s['sql_object']}"
                if s["schema_name"] else s["sql_object"]
            )
            folded = qualified.lower()
            if corpus_fold is not None:
                # Membership beats Kind (amendment 2): anything in the
                # parsed corpus can be named; DirectLake lakehouse tables
                # and InlineQuery self-exclude by not matching.
                if folded not in corpus_fold:
                    continue
                display_id[folded] = corpus_fold[folded]
            else:
                if s["sql_object_type"] not in ("View", "StoredProcedure"):
                    continue
                display_id.setdefault(folded, qualified)
            reports = consumers.setdefault(folded, [])
            if report_name not in reports:
                reports.append(report_name)

    rows: "list[dict]" = []
    skipped: "list[str]" = []
    fallout: "list[dict]" = []
    for folded, reports in consumers.items():
        titles = list(dict.fromkeys(friendly_name_from_report(r) for r in reports))
        if len(titles) > 1:
            reason = (
                f"{display_id[folded]}: consumed by {len(reports)} "
                f"differently-titled reports ({'; '.join(reports)}) — "
                f"refusing to pick a name; qualify manually"
            )
            skipped.append(reason)
            fallout.append({
                "stage": "12_name_derivation",
                "entity_id": display_id[folded],
                "reason_code": "multi_report_consumer",
                "reason_text": reason,
                "contract_id": "contract:input_metric_names",
            })
            continue
        rows.append({
            "metric_id": display_id[folded],
            "business_name": titles[0],
            "source": "pbi_report",
            "report_name": "; ".join(reports),
            "report_url": "",
            "assigned_date": scan_timestamp,
        })
    return rows, skipped, fallout
