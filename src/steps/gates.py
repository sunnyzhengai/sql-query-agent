"""Notebook-boundary postcondition gate.

After a notebook writes its tables, the gate proves the persisted state
satisfies the tables' contracts — catching orchestration failures (partial
writes, wrong lakehouse, stale inputs) that the pure step functions can
never see. Driven entirely by the ownership declarations in TABLE_REGISTRY:
a notebook gates exactly the tables it owns or enriches.
"""

from __future__ import annotations

from typing import Callable

from src.invariants import Fetch, check_table_invariants, check_table_relations
from src.schemas import TABLE_REGISTRY


class StepPostconditionError(Exception):
    """The persisted state violates a table contract after a step ran."""


def tables_owned_by(step_name: str, registry: "dict | None" = None) -> "list[str]":
    registry = registry if registry is not None else TABLE_REGISTRY
    return [
        name for name, contract in registry.items()
        if contract.get("status") == "active"
        and (
            (contract.get("owner") or {}).get("notebook") == step_name
            or step_name in contract.get("enrichers", [])
        )
    ]


def postcondition_gate(
    step_name: str,
    fetch: Fetch,
    table_exists: Callable[[str], bool],
    registry: "dict | None" = None,
) -> "list[str]":
    """Check every table this step owns/enriches. Returns the checked table
    names on success; raises StepPostconditionError listing violations."""
    registry = registry if registry is not None else TABLE_REGISTRY
    checked: "list[str]" = []
    violations: "list[str]" = []

    for table in tables_owned_by(step_name, registry):
        if not table_exists(table):
            continue  # conditional outputs (e.g., no parse errors this run)
        reference_targets_present = all(
            table_exists(inv["references"].split(".")[0])
            for inv in registry[table].get("invariants", [])
            if inv["kind"] == "reference"
        )
        if not reference_targets_present:
            continue
        checked.append(table)
        violations.extend(check_table_invariants(table, fetch, registry=registry))
        violations.extend(
            check_table_relations(table, fetch, table_exists, registry=registry)
        )

    if violations:
        raise StepPostconditionError(
            f"{step_name}: persisted state violates its contracts:\n  "
            + "\n  ".join(violations)
        )
    return checked
