"""Step 3b: the governance red-flag sweep (ADR 0054).

Consumes the built graph (graph_nodes + graph_edges rows), produces
gov_red_flags rows — misnomers, duplicates, cousin conflicts at
catalog grain — with the conservation partition asserted (clean ⊎
flagged ⊎ excluded-with-reason). Pure read; no new parse; no LLM.

Dispositions (append-only events in gov_flag_dispositions) fold into
the flag states here on every run, so a rerun preserves steward acts
while re-deriving the flags from current logic: a flag whose logic
changed re-opens (its members' hashes differ), one whose disposition
still applies keeps it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.governance.red_flags import SweepResult, apply_dispositions, sweep


@dataclass
class RedFlagSweepOutput:
    flags_rows: "list[dict]"
    swept: int
    flagged: int
    clean: int
    excluded: "dict[str, int]"
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
    return RedFlagSweepOutput(
        flags_rows=flags,
        swept=res.swept, flagged=res.flagged, clean=res.clean,
        excluded=dict(res.excluded),
        minted_edges=outcome.minted_edges,
        official_props=outcome.official_props,
        rejected_dispositions=outcome.rejected,
    )
