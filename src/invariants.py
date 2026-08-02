"""Generic data-invariant checker — the enforcement half of the contracts.

Declarations live in TABLE_REGISTRY[table]["invariants"] (src/schemas.py);
this module validates actual rows against them. Delta Lake has no
engine-enforced constraints (no PRIMARY KEY / UNIQUE / FOREIGN KEY), so
uniqueness, allowed values, and referential integrity only become real
where code checks them — at write time and in the 06_validate gate, which
calls check_all_invariants with a Spark-backed fetch.

The checker is generic on purpose: it reads the contracts and enforces
whatever they declare. Adding an invariant to a contract is sufficient —
no per-table checking code is ever written.

fetch(table_name, columns) -> list[dict] supplies rows (only the requested
columns, so callers can push down column pruning). Null values never
violate allowed_values or reference — nullability is the shape's job.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from src.schemas import TABLE_REGISTRY

Fetch = Callable[[str, "list[str]"], "list[dict[str, Any]]"]

_SAMPLE = 5  # max offending values quoted per violation message


def _sample(values: Iterable) -> str:
    listed = sorted(str(v) for v in values)
    shown = ", ".join(listed[:_SAMPLE])
    more = len(listed) - _SAMPLE
    return shown + (f" (+{more} more)" if more > 0 else "")


def check_table_invariants(
    table_name: str,
    fetch: Fetch,
    registry: "dict | None" = None,
) -> "list[str]":
    """Check one table's declared invariants. Returns violation messages."""
    registry = registry if registry is not None else TABLE_REGISTRY
    contract = registry[table_name]
    violations: "list[str]" = []

    for inv in contract.get("invariants", []):
        kind = inv["kind"]

        if kind == "unique":
            cols = inv["columns"]
            fold = inv.get("fold_case", False)
            seen: "dict[tuple, int]" = {}
            for row in fetch(table_name, cols):
                key = tuple(
                    v.upper() if fold and isinstance(v, str) else v
                    for v in (row[c] for c in cols)
                )
                seen[key] = seen.get(key, 0) + 1
            dupes = {k for k, n in seen.items() if n > 1}
            if dupes:
                shown = {k[0] if len(k) == 1 else k for k in dupes}
                violations.append(
                    f"{table_name}: unique({', '.join(cols)}) violated by "
                    f"{len(dupes)} value(s): {_sample(shown)}"
                )

        elif kind == "allowed_values":
            col, allowed = inv["column"], set(inv["values"])
            bad = {
                row[col]
                for row in fetch(table_name, [col])
                if row[col] is not None and row[col] not in allowed
            }
            if bad:
                violations.append(
                    f"{table_name}.{col}: value(s) outside allowed set "
                    f"{sorted(allowed)}: {_sample(bad)}"
                )

        elif kind == "reference":
            col = inv["column"]
            target_table, target_col = inv["references"].split(".")
            targets = {
                row[target_col] for row in fetch(target_table, [target_col])
            }
            missing = {
                row[col]
                for row in fetch(table_name, [col])
                if row[col] is not None and row[col] not in targets
            }
            if missing:
                violations.append(
                    f"{table_name}.{col}: {len(missing)} value(s) not found in "
                    f"{target_table}.{target_col}: {_sample(missing)}"
                )

        else:  # unreachable while meta-tests pin INVARIANT_KINDS
            violations.append(f"{table_name}: unknown invariant kind '{kind}'")

    return violations


def check_all_invariants(
    fetch: Fetch,
    table_exists: Callable[[str], bool],
    registry: "dict | None" = None,
) -> "dict[str, list[str]]":
    """Check every active, existing table. Returns {table: violations},
    omitting tables with no violations."""
    registry = registry if registry is not None else TABLE_REGISTRY
    results: "dict[str, list[str]]" = {}
    for name, contract in registry.items():
        if contract.get("status") != "active" or not contract.get("invariants"):
            continue
        if not table_exists(name):
            continue
        # A reference invariant needs its target table too.
        targets_missing = [
            inv["references"].split(".")[0]
            for inv in contract["invariants"]
            if inv["kind"] == "reference"
            and not table_exists(inv["references"].split(".")[0])
        ]
        if targets_missing:
            continue
        violations = check_table_invariants(name, fetch, registry=registry)
        if violations:
            results[name] = violations
    return results
