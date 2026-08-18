"""The admin journey tables — one row, the whole pipeline (family G).

HANDOFF_ADMIN_JOURNEY_DASHBOARD, all decisions resolved by Sunny:
materialized by 500_validate as Delta contracts (never dashboard-side
computation); workspace NAMES on every axis; one unified error_type
vocabulary shared with the fallout reason codes.

Grain rules (settled): ops_metric_journey is METRIC-GRAIN — one row per
metric, ALWAYS; a proc feeding 2 reports gets report_count=2 and a
'; '-joined list, never two rows (a junction may not multiply the
driving grain or funnel totals stop reconciling). ops_report_journey is
REPORT-GRAIN; the exploded pairs stay in input_report_sources.

Accuracy contract: every column is a join over existing contract
tables; the reconciliation tests pin loaded = parsed + errored (etc.)
so the dashboard cannot drift from the system of record.
"""

from __future__ import annotations

# The unified error_type vocabulary (decision c): one set of codes
# across parse errors, description rejections, and publish failures —
# shared with the fallout reason codes. Parse error_category values
# pass through as-is (they are already machine codes).
DESCRIBED_OK = "ok"
DESCRIBED_REJECTED = "rejected_by_agent"   # == the funnel's code
DESCRIBED_PENDING = "pending"


def _fold(s: "str | None") -> str:
    return (s or "").lower()


def metric_journey_rows(
    run_at: str,
    sql_sources: "list[dict]",
    validation_rows: "list[dict]",
    parse_errors: "list[dict]",
    metric_logic_rows: "list[dict]",
    agent_desc_rows: "list[dict]",
    report_source_rows: "list[dict]",
    publish_log_rows: "list[dict]",
) -> "list[dict]":
    """One row per metric_id; columns left-to-right ARE the pipeline."""
    validation = {_fold(r["metric_id"]): r for r in validation_rows}
    errors = {_fold(r["metric_id"]): r.get("error_category") or "parse_error"
              for r in parse_errors}
    cards = {_fold(r["metric_id"]): r for r in metric_logic_rows}
    described = {}
    for r in agent_desc_rows:
        status = r.get("status", DESCRIBED_OK)
        described[_fold(r["metric_name"])] = (
            DESCRIBED_OK if status == "ok" else DESCRIBED_REJECTED)

    reports_of: "dict[str, list[str]]" = {}
    for r in report_source_rows:
        qualified = (f"{r['schema_name']}.{r['sql_object']}"
                     if r.get("schema_name") else r.get("sql_object") or "")
        key = _fold(qualified)
        names = reports_of.setdefault(key, [])
        if r["report_name"] not in names:
            names.append(r["report_name"])

    published: "dict[str, set[str]]" = {}
    for r in publish_log_rows:
        if r.get("status") != "success":
            continue
        for key in (_fold(r.get("asset_id")), _fold(r.get("name"))):
            if key:
                published.setdefault(key, set()).add(r.get("target") or "")

    def _published(metric_id: str, bare: str, target: str) -> bool:
        return (target in published.get(_fold(metric_id), set())
                or target in published.get(_fold(bare), set()))

    rows: "list[dict]" = []
    for s in sql_sources:
        mid = s["metric_id"]
        key = _fold(mid)
        bare = mid.rsplit(".", 1)[-1]
        v = validation.get(key, {})
        card = cards.get(key)
        # a metric with an OK/REJECTED row is described/rejected; one
        # with a card but no row is pending; no card -> not applicable
        if key in described or _fold(bare) in described:
            described_status = described.get(key, described.get(_fold(bare)))
        elif card is not None:
            described_status = DESCRIBED_PENDING
        else:
            described_status = None
        report_names = reports_of.get(key, [])
        rows.append({
            "run_at": run_at,
            "metric_id": mid,
            "source_type": s.get("source_type"),
            "source_schema": s.get("source_schema"),
            "loaded": True,   # presence in input_sql_sources IS loaded
            "parsed": bool(v.get("step2_parsed")),
            "error_type": errors.get(key),
            "in_graph": bool(v.get("step3_canonical")),
            "card": card is not None and bool(card.get("calculation_logic")),
            "described_status": described_status,
            "report_count": len(report_names),
            "report_names": "; ".join(report_names),
            "published_collibra": _published(mid, bare, "collibra"),
            "published_pbi_writeback": _published(mid, bare, "fabric_pbi"),
        })

    # Grain integrity: the driving grain may never multiply.
    assert len({r["metric_id"] for r in rows}) == len(rows), (
        "metric journey grain violated: duplicate metric_id rows")
    return rows


def report_journey_rows(
    run_at: str,
    report_source_rows: "list[dict]",
    corpus_metric_ids: "set[str] | None" = None,
) -> "list[dict]":
    """One row per PBI report — the other side of the M:N tie."""
    corpus_fold = ({_fold(m) for m in corpus_metric_ids}
                   if corpus_metric_ids is not None else None)
    by_report: "dict[str, dict]" = {}
    for r in report_source_rows:
        entry = by_report.setdefault(r["report_name"], {
            "workspace_name": r.get("workspace_name") or "",
            "procs": [],
            "in_corpus": 0,
        })
        if not entry["workspace_name"] and r.get("workspace_name"):
            entry["workspace_name"] = r["workspace_name"]
        qualified = (f"{r['schema_name']}.{r['sql_object']}"
                     if r.get("schema_name") else r.get("sql_object") or "")
        if qualified and qualified not in entry["procs"]:
            entry["procs"].append(qualified)
            if corpus_fold is not None and _fold(qualified) in corpus_fold:
                entry["in_corpus"] += 1

    rows = []
    for report_name, e in sorted(by_report.items()):
        # tie kind: every edge here came from parsed TMDL — lineage-
        # exact by construction; corpus membership says whether the
        # other end exists in the parsed SQL estate
        if corpus_fold is None:
            tie = "lineage"
        elif e["in_corpus"] == len(e["procs"]) and e["procs"]:
            tie = "lineage_in_corpus"
        elif e["in_corpus"] > 0:
            tie = "lineage_partial_corpus"
        else:
            tie = "lineage_outside_corpus"
        rows.append({
            "run_at": run_at,
            "report_name": report_name,
            "workspace_name": e["workspace_name"],
            "proc_count": len(e["procs"]),
            "proc_names": "; ".join(e["procs"]),
            "tie_kind": tie,
        })
    assert len({r["report_name"] for r in rows}) == len(rows)
    return rows
