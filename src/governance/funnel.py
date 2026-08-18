"""The pipeline funnel — family G's dashboard shape (ADR 0039 lineage).

One mechanism, two views (HANDOFF_FUNNEL_AND_FALLOUT): fallout rows are
the gold (already landing in ops_fallout); this module derives the
FUNNEL from them plus stage outputs — per run, per stage: how many came
in, how many came through, how many fell off, and WHY (reason codes,
aggregated). Each fell-off number is backed by queryable rows, never a
bare count.

Extends ops_build_summary's counts; never duplicates them — the funnel
row says where its numbers came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FunnelStage:
    stage: str
    in_count: int
    out_count: int
    reasons: "dict[str, int]" = field(default_factory=dict)
    derived_from: str = ""      # which tables produced the numbers

    @property
    def fell_off(self) -> int:
        return max(0, self.in_count - self.out_count)


def funnel_rows(stages: "list[FunnelStage]", run_at: str) -> "list[dict]":
    """Display/persist-shaped funnel rows. Reasons are rendered
    'code:count' sorted by count desc — GROUP BY-able upstream, readable
    downstream. A stage whose reasons don't cover its fell-off gets an
    explicit 'unexplained' bucket — a missing fallout row is itself a
    finding, never silently absorbed."""
    rows = []
    for s in stages:
        explained = sum(s.reasons.values())
        reasons = dict(s.reasons)
        if s.fell_off > explained:
            reasons["unexplained"] = s.fell_off - explained
        rendered = "; ".join(
            f"{code}:{n}" for code, n in
            sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))
        )
        rows.append({
            "run_at": run_at,
            "stage": s.stage,
            "in_count": s.in_count,
            "out_count": s.out_count,
            "fell_off": s.fell_off,
            "reasons": rendered,
            "derived_from": s.derived_from,
        })
    return rows


def funnel_lines(rows: "list[dict]") -> "list[str]":
    lines = ["=== PIPELINE FUNNEL (each fell-off number is backed by "
             "queryable rows) ==="]
    for r in rows:
        arrow = f"  {r['stage']}: {r['in_count']} -> {r['out_count']}"
        if r["fell_off"]:
            arrow += f"  ({r['fell_off']} fell off — {r['reasons']})"
        lines.append(arrow)
    return lines


def reasons_from_fallout(
    fallout_rows: "list[dict]", stage: str
) -> "dict[str, int]":
    """Aggregate ops_fallout reason codes for one stage, LATEST run only
    (the funnel is per-run; history stays in the table)."""
    stage_rows = [r for r in fallout_rows if r.get("stage") == stage]
    if not stage_rows:
        return {}
    latest = max(r.get("run_at") or "" for r in stage_rows)
    out: "dict[str, int]" = {}
    for r in stage_rows:
        if (r.get("run_at") or "") == latest:
            out[r["reason_code"]] = out.get(r["reason_code"], 0) + 1
    return out
