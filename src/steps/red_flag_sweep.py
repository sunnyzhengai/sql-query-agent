"""The governance red-flag sweep (ADR 0054), graph-native (ADR 0057).

RESIDENCE (Sunny's demo law, 2026-08-25): the sweep runs INSIDE
300_build_graph (fold-into-300 — clusters are derived structures,
the ADR 0018 precedent; one writer, one truth) and its verdicts live
as reified GOVERNANCE-layer nodes (name_cluster → logic_group →
member_of edges) in graph_nodes/graph_edges. The former
320_red_flag_sweep notebook and gov_red_flags table are retired.

Detection stays deterministic (fold-name, content-hash, token
containment, DISTINCT-grain) — never stochastic. Conservation
asserted (clean ⊎ flagged ⊎ excluded-with-reason; one cluster node
per verdict). Dispositions (append-only events in
gov_flag_dispositions) fold into the flag states on every run and
re-reify onto the cluster nodes, so a rerun preserves steward acts
while re-deriving the flags from current logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.governance.red_flags import SweepResult, apply_dispositions, sweep


@dataclass
class RedFlagSweepOutput:
    flags_rows: "list[dict]"
    cluster_nodes_rows: "list[dict]" = field(default_factory=list)
    cluster_edges_rows: "list[dict]" = field(default_factory=list)
    swept: int = 0
    flagged: int = 0
    clean: int = 0
    excluded: "dict[str, int]" = field(default_factory=dict)
    minted_edges: "list[tuple]" = field(default_factory=list)
    official_props: "list[dict]" = field(default_factory=list)
    rejected_dispositions: "list[dict]" = field(default_factory=list)

    def summary_lines(self) -> "list[str]":
        by_class: "dict[str, int]" = {}
        unlabeled = 0
        for r in self.flags_rows:
            key = f"{r['flag_class']}/{r['severity']}"
            by_class[key] = by_class.get(key, 0) + 1
            if r["disposition"] == "open":
                unlabeled += 1
        lines = [
            "=== GOVERNANCE RED FLAGS (ADR 0054 — flags disclose, "
            "never gate) ===",
            f"swept {self.swept} catalog items: {self.flagged} in "
            f"flags, {self.clean} clean, excluded {self.excluded}",
        ]
        for key, n in sorted(by_class.items()):
            lines.append(f"  {key}: {n} flag(s)")
        lines.append(f"  KPI unlabeled divergences: {unlabeled} "
                     "(target: 0 via dispositions, never merges)")
        if self.rejected_dispositions:
            lines.append(f"  [!] rejected disposition event(s): "
                         f"{len(self.rejected_dispositions)} — each "
                         "carries its reason; fix and rerun")
        return lines


def red_flag_sweep_step(
    nodes_rows: "list[dict]",
    edges_rows: "list[dict]",
    disposition_events: "list[dict] | None" = None,
    run_at: str = "",
) -> RedFlagSweepOutput:
    res: SweepResult = sweep(nodes_rows, edges_rows)
    res.assert_conservation()
    flags = res.flags_rows
    outcome = apply_dispositions(flags, disposition_events or [])
    flags = outcome.flags_rows
    for r in flags:
        r["run_at"] = run_at
    # Re-reify AFTER the disposition fold (ADR 0057): steward acts
    # ride the cluster node properties into the graph — the graph is
    # the sole flag truth, dispositions included.
    from src.governance.red_flags import reify_clusters
    cluster_nodes, cluster_edges = reify_clusters(flags)
    return RedFlagSweepOutput(
        flags_rows=flags,
        cluster_nodes_rows=cluster_nodes,
        cluster_edges_rows=cluster_edges,
        swept=res.swept, flagged=res.flagged, clean=res.clean,
        excluded=dict(res.excluded),
        minted_edges=outcome.minted_edges,
        official_props=outcome.official_props,
        rejected_dispositions=outcome.rejected,
    )
