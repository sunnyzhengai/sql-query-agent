"""BRIDGE-1 stage 1 (ADR 0063 §2, FILE-FIRST as ruled): approved
review sets export as NATIVE import files — Collibra Data Intake
CSVs (assets + relations) and the Purview glossary CSV. The admin
uploads; zero API risk; the file itself is a second HITL artifact.

Every row is PROVENANCE-GRADED (the Write-Back Queue law applied
to stage 1): "parsed by <product>, approved by <approver>" — the
approver is the engagement admin who reviews the file before
upload; nothing machine-authored enters an enterprise record
without a named human on the row.

Source of truth: the certified graph (descriptions are the
sweep/steward-authored fields already in the store — the exporter
never authors a word).
"""

from __future__ import annotations

import csv
import io

from src.branding import product_name
from src.orchestrator.ops import OpsSession, op_census

# metric reads table, via the step chain — one scan, distinct pairs
READS_EXPORT_QUERY = (
    "graph_edges\n"
    "| where edge_type == 'transform_to_technical'\n"
    "| extend ['ref'] = tostring(split(source_id, ':')[1]),\n"
    "         tbl = tostring(split(target_id, ':')[1])\n"
    "| distinct ['ref'], tbl\n"
    "| order by ['ref'] asc, tbl asc"
)


def _grade(approver: str) -> str:
    return f"parsed by {product_name()}, approved by {approver}"


def _metric_rows(run_kql) -> "list[dict]":
    return op_census("metric", run_kql, OpsSession()).rows


def collibra_asset_rows(run_kql, approver: str,
                        domain: str = "") -> "list[dict]":
    """Collibra Data Intake — the assets sheet: one row per
    certified metric, description straight from the store."""
    out = []
    for r in sorted(_metric_rows(run_kql),
                    key=lambda x: str(x.get("id"))):
        out.append({
            "Name": str(r.get("business_name") or r.get("name")),
            "Full Name": str(r.get("id")),
            "Asset Type": "Business Metric",
            "Domain": domain,
            "Description": str(r.get("description") or ""),
            "Provenance": _grade(approver),
        })
    return out


def collibra_relation_rows(run_kql, approver: str) -> "list[dict]":
    """Collibra Data Intake — the relations sheet: metric READS
    table, from the parsed edge chain (deterministic lineage,
    never inferred)."""
    names = {str(r.get("id")): str(r.get("business_name")
                                   or r.get("name"))
             for r in _metric_rows(run_kql)}
    out = []
    for e in run_kql(READS_EXPORT_QUERY, {}):
        ref = str(e.get("ref") or "")
        if ref not in names:
            continue
        out.append({
            "Head": names[ref],
            "Head Full Name": ref,
            "Relation": "source table [reads]",
            "Tail": str(e.get("tbl") or ""),
            "Tail Asset Type": "Table",
            "Provenance": _grade(approver),
        })
    return out


def purview_glossary_rows(run_kql, approver: str,
                          expert: str = "") -> "list[dict]":
    """The Purview glossary import CSV — certified metrics as
    glossary terms, Status=Draft (the catalog's own workflow owns
    promotion; we never claim Approved on their side)."""
    out = []
    for r in sorted(_metric_rows(run_kql),
                    key=lambda x: str(x.get("id"))):
        definition = str(r.get("description") or "")
        out.append({
            "Name": str(r.get("business_name") or r.get("name")),
            "Status": "Draft",
            "Definition": (definition
                           + (f"\n[{_grade(approver)}]"
                              if definition else _grade(approver))),
            "Acronym": "",
            "Experts": expert,
            "Stewards": expert,
            "Parent Term Name": "",
            "IsDefinitionRichText": "false",
        })
    return out


def to_csv(rows: "list[dict]") -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()),
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def export_bridge_files(run_kql, approver: str, out_dir: str,
                        domain: str = "",
                        expert: str = "") -> "dict[str, int]":
    """Write the three stage-1 files; returns {filename: rows} —
    the postcondition the caller prints (an acknowledgment is a
    claim; the row counts are the fact)."""
    from pathlib import Path
    outputs = {
        "collibra_assets.csv":
            collibra_asset_rows(run_kql, approver, domain),
        "collibra_relations.csv":
            collibra_relation_rows(run_kql, approver),
        "purview_glossary.csv":
            purview_glossary_rows(run_kql, approver, expert),
    }
    counts = {}
    for fname, rows in outputs.items():
        (Path(out_dir) / fname).write_text(to_csv(rows))
        counts[fname] = len(rows)
    return counts
