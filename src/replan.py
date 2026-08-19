"""replan — the registry-derived minimal re-run advisor (ADR 0039/0042
lineage; HANDOFF_INCREMENTAL_RERUN).

Field evidence, twice in one night (2026-08-18): hand-derived re-run
lists are wrong even when an expert writes them — the 300→400→700→800
list omitted 600 and wiped every description on the demo tenant, and
the handoff documenting the problem contained the same omission in its
own example. TABLE_REGISTRY already IS the dependency DAG (owners,
enrichers, consumers); this module computes what a human should never
have to remember.

    replan({"input_metric_names"}) ->
        [300_build_graph, 400_build_metric_logic, 500_validate,
         600_generate_descriptions, 610..., 700..., 800..., 9xx...]

Rules (all derived, none hand-coded):
- A notebook must run when it CONSUMES a dirty table.
- A notebook that runs dirties every table it OWNS or ENRICHES.
- Running the OWNER of a table invalidates that table's ENRICHERS'
  in-place work, so enrichers rerun (300 rebuilds graph_nodes ⇒ 600's
  descriptions are gone ⇒ 600 must run — the exact edge the humans
  missed).
- Lexicographic order of the century scheme IS execution order.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.notebook_registry import NOTEBOOK_REGISTRY
from src.schemas import TABLE_REGISTRY


@dataclass(frozen=True)
class RunAdvice:
    notebook: str
    family: str
    reason: str


def _notebook(name: str) -> "str | None":
    """Registry entries name notebooks exactly; ignore non-notebook
    consumers (data_agent, admin, adapters, utilities)."""
    return name if name in NOTEBOOK_REGISTRY else None


def replan(changed_tables: "set[str]") -> "list[RunAdvice]":
    """Minimal ordered notebook list for a set of changed tables.

    Returns EVERY affected notebook with its family and reason —
    callers (humans, a driver notebook) decide whether publishers and
    optional derivations actually fire; the advisory never silently
    drops them.
    """
    dirty: "set[str]" = set(changed_tables)
    runs: "dict[str, str]" = {}  # notebook -> reason (first cause wins)

    changed = True
    while changed:
        changed = False
        for table, contract in TABLE_REGISTRY.items():
            if contract.get("status") != "active":
                continue
            owner = _notebook((contract.get("owner") or {}).get("notebook", ""))
            enrichers = [e for e in (contract.get("enrichers") or [])
                         if _notebook(e)]
            consumers = [c for c in (contract.get("consumers") or [])
                         if _notebook(c)]

            if table in dirty:
                for nb in consumers:
                    if nb not in runs:
                        runs[nb] = f"consumes changed table {table}"
                        changed = True

            # a running owner invalidates in-place enrichment
            if owner in runs:
                for nb in enrichers:
                    if nb not in runs:
                        runs[nb] = (f"enrichment of {table} is wiped when "
                                    f"{owner} rebuilds it")
                        changed = True

            # anything a running notebook owns or enriches becomes dirty
            for nb in [owner] + enrichers:
                if nb in runs and table not in dirty:
                    dirty.add(table)
                    changed = True

    advice = [
        RunAdvice(nb, NOTEBOOK_REGISTRY[nb]["family"], reason)
        for nb, reason in runs.items()
    ]
    # the century scheme makes ordering trivial: lexicographic = run order
    return sorted(advice, key=lambda a: a.notebook)


def replan_lines(changed_tables: "set[str]") -> "list[str]":
    """Human-readable advisory (for 500's output, /troubleshoot, docs)."""
    advice = replan(changed_tables)
    if not advice:
        return [f"replan: no notebook consumes {sorted(changed_tables)}"]
    lines = [f"replan for changed {sorted(changed_tables)}:"]
    for a in advice:
        lines.append(f"  {a.notebook}  [{a.family}] — {a.reason}")
    return lines
