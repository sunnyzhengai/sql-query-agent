"""BRIDGE-1 stage 1 (ADR 0063 §2, FILE-FIRST as ruled): approved
review sets export as NATIVE import files — Collibra Data Intake
CSVs (assets + relations) and the Purview glossary CSV. The admin
uploads; zero API risk; the file itself is a second HITL artifact.

Every row is PROVENANCE-GRADED (the Write-Back Queue law applied
to stage 1): "parsed by <product>, approved by <approver>" — the
approver is the engagement admin who reviews the file before
upload; nothing machine-authored enters an enterprise record
without a named human on the row.

BR-1 (review find, blocked Sunny's Purview experiment): catalogs
require UNIQUE names, and this estate's whole point is that names
collide. Colliding names export QUALIFIED (name + ref) with the
conflict DISCLOSED in the definition text — uniqueness satisfied,
honesty exported, never-gate preserved; an open conflict flag on
the name is cited by class. `assert_unique_names` makes the
duplicate-Name class structurally dead in every export.

BR-2: Stewards/Experts populate from the STORE's steward/developer
fields — pre-filled stewardship is the product; the CLI arg is
only the fallback for storeless rows.

Source of truth: the certified graph; the exporter never authors
a description.
"""

from __future__ import annotations

import csv
import io

from src.branding import product_name
from src.orchestrator.ops import OpsSession, op_census

# one scan carries the whole export surface (BR-2: steward fields
# ride the same table the facts assembler reads)
METRIC_EXPORT_QUERY = (
    "output_metric_logic\n"
    "| project metric_id, metric_name, business_name, description,\n"
    "          steward, developer\n"
    "| order by metric_id asc"
)

# metric reads table, via the step chain — one scan, distinct pairs
READS_EXPORT_QUERY = (
    "graph_edges\n"
    "| where edge_type == 'transform_to_technical'\n"
    "| extend ['ref'] = tostring(split(source_id, ':')[1]),\n"
    "         tbl = tostring(split(target_id, ':')[1])\n"
    "| distinct ['ref'], tbl\n"
    "| order by ['ref'] asc, tbl asc"
)

_CONFLICT_CLASSES = ("cousin_conflict", "misnomer", "grain_shift")


class ExportIntegrityError(Exception):
    """A file that would discredit itself never leaves the house."""


def _grade(approver: str) -> str:
    return f"parsed by {product_name()}, approved by {approver}"


def _metric_rows(run_kql) -> "list[dict]":
    return sorted(run_kql(METRIC_EXPORT_QUERY, {}),
                  key=lambda r: str(r.get("metric_id")))


def _conflict_flags_by_ref(run_kql) -> "dict[str, str]":
    """ref -> conflict flag class, for OPEN conflict-class flags —
    the disclosure the qualified name cites."""
    from src.orchestrator.tools import GOV_FLAG_MEMBER_NAMES_QUERY
    out: "dict[str, str]" = {}
    try:
        flags = op_census("flag", run_kql, OpsSession()).rows
        members = {str(r.get("cluster")): [
            str(m) for m in (r.get("member_ids") or [])]
            for r in run_kql(GOV_FLAG_MEMBER_NAMES_QUERY, {})}
        for f in flags:
            if str(f.get("flag_class")) not in _CONFLICT_CLASSES:
                continue
            if str(f.get("disposition") or "open") != "open":
                continue
            for mid in members.get(str(f.get("id")), []):
                ref = mid.split(":", 1)[-1]
                out.setdefault(ref, str(f.get("flag_class")))
    except Exception:   # noqa: BLE001 — disclosure enrich is additive
        return {}
    return out


def _display_names(rows: "list[dict]",
                   conflicts: "dict[str, str]") -> "dict[str, tuple]":
    """ref -> (unique display name, disclosure prefix or "").
    BR-1: colliding names qualify with the ref; the collision is
    disclosed in the definition, citing an open conflict flag when
    one covers the name."""
    by_name: "dict[str, list]" = {}
    for r in rows:
        name = str(r.get("business_name") or r.get("metric_name"))
        by_name.setdefault(name, []).append(str(r.get("metric_id")))
    out: "dict[str, tuple]" = {}
    for name, refs in by_name.items():
        if len(refs) == 1:
            out[refs[0]] = (name, "")
            continue
        for ref in refs:
            flagged = conflicts.get(ref)
            disclosure = (
                f"{len(refs)} definitions share the name "
                f"{name!r} — unresolved"
                + (f" ({flagged} flag open)" if flagged else "")
                + ". ")
            out[ref] = (f"{name} ({ref})", disclosure)
    return out


def assert_unique_names(rows: "list[dict]", where: str) -> None:
    names = [r["Name"] for r in rows]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise ExportIntegrityError(
            f"duplicate Name(s) in {where}: {dupes[:4]} — the "
            "import would fail or maul a twin inside the customer "
            "record; qualification missed them")


def collibra_asset_rows(run_kql, approver: str,
                        domain: str = "") -> "list[dict]":
    rows = _metric_rows(run_kql)
    names = _display_names(rows, _conflict_flags_by_ref(run_kql))
    out = []
    for r in rows:
        ref = str(r.get("metric_id"))
        display, disclosure = names[ref]
        out.append({
            "Name": display,
            "Full Name": ref,
            "Asset Type": "Business Metric",
            "Domain": domain,
            "Description": disclosure + str(r.get("description")
                                            or ""),
            "Stewards": str(r.get("steward") or ""),
            "Provenance": _grade(approver),
        })
    assert_unique_names(out, "collibra_assets")
    return out


def collibra_relation_rows(run_kql, approver: str) -> "list[dict]":
    rows = _metric_rows(run_kql)
    names = _display_names(rows, _conflict_flags_by_ref(run_kql))
    out = []
    for e in run_kql(READS_EXPORT_QUERY, {}):
        ref = str(e.get("ref") or "")
        if ref not in names:
            continue
        out.append({
            "Head": names[ref][0],
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
    glossary terms, Status=Draft (their workflow owns promotion)."""
    rows = _metric_rows(run_kql)
    names = _display_names(rows, _conflict_flags_by_ref(run_kql))
    out = []
    for r in rows:
        ref = str(r.get("metric_id"))
        display, disclosure = names[ref]
        definition = disclosure + str(r.get("description") or "")
        steward = str(r.get("steward") or "") or expert
        out.append({
            "Name": display,
            "Status": "Draft",
            "Definition": (definition
                           + (f"\n[{_grade(approver)}]"
                              if definition else _grade(approver))),
            "Acronym": "",
            "Experts": str(r.get("developer") or "") or expert,
            "Stewards": steward,
            "Parent Term Name": "",
            "IsDefinitionRichText": "false",
        })
    assert_unique_names(out, "purview_glossary")
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
    """Write the stage-1 files; returns {filename: rows} — the
    postcondition the caller prints (an acknowledgment is a claim;
    the row counts are the fact).

    TERM-PROPOSE-1/2 (09-04): the hierarchy set rides the same
    export — every OPEN conflict-class name family as parent
    concept + child terms (landing_registry organize_hierarchy)."""
    from pathlib import Path

    from src.term_propose import (
        hierarchy_collibra_asset_rows,
        hierarchy_collibra_relation_rows,
        hierarchy_purview_rows,
        term_hierarchy_payloads,
    )
    payloads = term_hierarchy_payloads(run_kql)
    outputs = {
        "collibra_assets.csv":
            collibra_asset_rows(run_kql, approver, domain),
        "collibra_relations.csv":
            collibra_relation_rows(run_kql, approver),
        "purview_glossary.csv":
            purview_glossary_rows(run_kql, approver, expert),
        "purview_term_hierarchy.csv":
            hierarchy_purview_rows(payloads),
        "collibra_term_hierarchy_assets.csv":
            hierarchy_collibra_asset_rows(payloads, domain),
        "collibra_term_hierarchy_relations.csv":
            hierarchy_collibra_relation_rows(payloads),
    }
    counts = {}
    for fname, rows in outputs.items():
        (Path(out_dir) / fname).write_text(to_csv(rows))
        counts[fname] = len(rows)
    return counts
