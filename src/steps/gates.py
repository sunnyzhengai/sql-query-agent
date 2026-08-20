"""Notebook-boundary gates: preconditions and postconditions.

precondition_gate — BEFORE a step runs, its required input tables must
exist, carry every contract-declared column (schema drift: the physical
table predates an upgrade and its producer hasn't rerun), and be
non-empty where the contract says emptiness is invalid.
A failure is a STATE problem with an admin-actionable message naming the
producing notebook — never a pyspark stack trace. Failures have two
audiences: state problems route to the customer admin (self-serve); raw
stack traces are reserved for true product defects, which route to the
vendor. Every stack trace a gate could have prevented is a misfiled
support ticket.

postcondition_gate — AFTER a notebook writes its tables, the gate proves
the persisted state satisfies the tables' contracts — catching
orchestration failures (partial writes, wrong lakehouse, stale inputs)
that the pure step functions can never see.

Both are driven entirely by TABLE_REGISTRY: required inputs come from each
table's `consumers` list (excluding self-reads of previous-run state and
tables flagged `optional_input`), producers from `owner.notebook`,
emptiness rules from `must_be_nonempty`. Gates cannot drift from the
contracts because they ARE the contracts, executed.

Every failure cites the violated contract's stable id (`contract:<table>`)
so error events can link error → contract → data (extends ADR 0026).
"""

from __future__ import annotations

from typing import Callable, Optional

from src.invariants import Fetch, check_table_invariants, check_table_relations
from src.schemas import TABLE_REGISTRY


def contract_id(table_name: str) -> str:
    """Stable identifier for a table's contract, citable from error events."""
    return f"contract:{table_name}"


class StepPreconditionError(Exception):
    """A required input table is missing or empty BEFORE a step runs.

    Carries structured `failures` (table, problem, producer, contract_id)
    so callers can log them as error events; the message is the
    admin-actionable rendering.
    """

    def __init__(self, step_name: str, failures: "list[dict]") -> None:
        self.step_name = step_name
        self.failures = failures
        lines = [f"[!] Preconditions failed for {step_name}:"]
        for f in failures:
            lines.append(
                f"    {f['table']} {f['problem']} — produced by "
                f"{f['producer']} [{f['contract_id']}]"
            )
        super().__init__("\n".join(lines))


def required_inputs(step_name: str, registry: "dict | None" = None) -> "list[str]":
    """Tables this step consumes, derived from the registry.

    Excluded: self-reads of the step's own previous-run state (absent on a
    legitimate first run), tables flagged optional_input, non-active tables.
    """
    registry = registry if registry is not None else TABLE_REGISTRY
    out = []
    for name, contract in registry.items():
        if contract.get("status") != "active":
            continue
        if step_name not in contract.get("consumers", []):
            continue
        if (contract.get("owner") or {}).get("notebook") == step_name:
            continue
        if contract.get("optional_input"):
            continue
        out.append(name)
    return sorted(out)


def optional_inputs(step_name: str, registry: "dict | None" = None) -> "list[str]":
    """Active tables this step consumes that are flagged optional_input."""
    registry = registry if registry is not None else TABLE_REGISTRY
    return sorted(
        name for name, contract in registry.items()
        if contract.get("status") == "active"
        and step_name in contract.get("consumers", [])
        and contract.get("optional_input")
    )


def setup_completeness_rows(
    step_name: str,
    table_exists: Callable[[str], bool],
    run_at: str,
    registry: "dict | None" = None,
) -> "list[dict]":
    """One ops_setup_completeness row per optional input of this step.

    A run that proceeds without an optional enrichment is legitimate but
    DEGRADED (graph with zero stewards, object names only) — a third
    category between gate error and product defect. That state must be
    queryable, never only a printed line (handoff item 3, 2026-08-15).
    """
    registry = registry if registry is not None else TABLE_REGISTRY
    return [
        {
            "run_at": run_at,
            "step": step_name,
            "table_name": table,
            "present": bool(table_exists(table)),
            "remediation": registry[table].get("remediation", ""),
            "contract_id": contract_id(table),
        }
        for table in optional_inputs(step_name, registry)
    ]


def missing_columns(
    table: str,
    physical_columns: "list[str]",
    registry: "dict | None" = None,
) -> "list[str]":
    """Contract columns absent from the physical table (case-insensitive).

    Schema drift: an upgrade adds a column to a table's contract, but the
    physical Delta table was written by the producer's PREVIOUS version
    and is only rewritten when that producer reruns. Field find (tenant
    500 run, 2026-08-20): input_dict_tables lacked ORIGIN and the leaf-
    grounding cell died with a raw AnalysisException mid-notebook."""
    registry = registry if registry is not None else TABLE_REGISTRY
    have = {c.upper() for c in physical_columns}
    return [name for name, _dtype, _nullable in registry[table].get("columns", [])
            if name.upper() not in have]


def precondition_gate(
    step_name: str,
    table_exists: Callable[[str], bool],
    count: "Optional[Callable[[str], int]]" = None,
    registry: "dict | None" = None,
    columns_of: "Optional[Callable[[str], list[str]]]" = None,
) -> "list[str]":
    """Check every required input before the step runs.

    count enables the non-empty check for tables whose contract sets
    must_be_nonempty; pass e.g. `lambda t: spark.table(t).count()`.
    columns_of enables the schema-drift check (every contract-declared
    column present); pass e.g. `lambda t: spark.table(t).columns`.
    Returns checked table names; raises StepPreconditionError otherwise.
    """
    registry = registry if registry is not None else TABLE_REGISTRY
    failures: "list[dict]" = []
    checked: "list[str]" = []

    for table in required_inputs(step_name, registry):
        producer = (registry[table].get("owner") or {}).get("notebook") or "unknown"
        entry = {"table": table, "producer": producer, "contract_id": contract_id(table)}
        if not table_exists(table):
            failures.append({**entry, "problem": "missing"})
            continue
        if columns_of is not None:
            absent = missing_columns(table, columns_of(table), registry)
            if absent:
                failures.append({
                    **entry,
                    "problem": (
                        f"is missing column(s) {', '.join(absent)} — schema "
                        f"drift after an upgrade; rerun the producer to rewrite it"
                    ),
                })
                continue
        if (
            count is not None
            and registry[table].get("must_be_nonempty")
            and not count(table)
        ):
            failures.append({**entry, "problem": "is empty"})
            continue
        checked.append(table)

    if failures:
        raise StepPreconditionError(step_name, failures)
    return checked


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
