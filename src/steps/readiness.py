"""Step 06: the deployment readiness decision, as a pure function.

Takes every gate input (threshold measurements, invariant violations,
schema ambiguities, acknowledgment flag) and returns the verdict plus the
exact report lines to print — so the decision logic is testable in CI and
identical wherever the pipeline runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

# Gate-integrity contract: these checks may FAIL, but they may never silently
# DISAPPEAR from the gate. A caller that cannot supply one must be blocked,
# not quietly graded on fewer checks (audit 2026-08-15: dictionary_coverage
# vanished inside a try/except and the gate printed DEPLOYMENT READY).
REQUIRED_CHECKS = (
    "parse_rate",
    "calculation_logic",
    "traversal_coverage",
    "dictionary_coverage",
)


@dataclass
class GateResult:
    blocked: bool
    lines: "list[str]"


def tech_table_names(nodes: "Iterable[dict]") -> "set[str]":
    """Upper-cased table names of technical table nodes.

    Accepts node rows whose `properties` field is either a JSON string
    (Delta round-trip) or a dict (in-memory build). Column nodes are skipped.
    """
    names: "set[str]" = set()
    for node in nodes:
        if not (node.get("node_id") or "").startswith("tech:"):
            continue
        raw = node.get("properties") or {}
        props = json.loads(raw) if isinstance(raw, str) else raw
        if props.get("table") and not props.get("column"):
            names.add(props["table"].upper())
    return names


def dictionary_coverage_threshold(
    dict_table_names: "set[str]",
    sql_table_names: "set[str]",
    threshold: float = 0.90,
) -> "tuple[float, float, bool]":
    """Share of SQL-referenced tables present in the data dictionary.

    An empty graph (no technical table nodes) measures 0.0 — the empty case
    blocks, it does not skip: that is exactly when deployment must not
    proceed.
    """
    if not sql_table_names:
        return (0.0, threshold, True)
    folded_dict = {n.upper() for n in dict_table_names}
    folded_sql = {n.upper() for n in sql_table_names}
    return (len(folded_sql & folded_dict) / len(folded_sql), threshold, True)


def readiness_gate(
    thresholds: "dict[str, tuple[float, float, bool]]",
    invariant_violations: "dict[str, list[str]]",
    schema_ambiguities: "dict[str, list[str]]",
    ambiguity_acknowledged: bool,
    required_checks: "tuple[str, ...]" = REQUIRED_CHECKS,
) -> GateResult:
    """thresholds: {name: (actual, threshold, is_blocking)}."""
    blocked = False
    lines: "list[str]" = []

    missing = [name for name in required_checks if name not in thresholds]
    if missing:
        blocked = True
        lines.append(
            f"[X] gate_integrity: required check(s) missing from gate inputs: "
            f"{', '.join(missing)} — BLOCKED"
        )

    for name, (actual, threshold, is_blocking) in thresholds.items():
        status = "PASS" if actual >= threshold else ("BLOCKED" if is_blocking else "WARNING")
        symbol = "+" if status == "PASS" else ("X" if status == "BLOCKED" else "!")
        lines.append(f"[{symbol}] {name}: {actual:.0%} (threshold: {threshold:.0%}) — {status}")
        if status == "BLOCKED":
            blocked = True

    if invariant_violations:
        blocked = True
        total = sum(len(v) for v in invariant_violations.values())
        lines.append(f"[X] data_contract_invariants: {total} violation(s) — BLOCKED")
        for table in sorted(invariant_violations):
            for msg in invariant_violations[table]:
                lines.append(f"      {msg}")
    else:
        lines.append("[+] data_contract_invariants: all declared invariants hold — PASS")

    if schema_ambiguities:
        status = "WARNING (acknowledged)" if ambiguity_acknowledged else "BLOCKED"
        symbol = "!" if ambiguity_acknowledged else "X"
        lines.append(
            f"[{symbol}] dictionary_schema_ambiguity: {len(schema_ambiguities)} "
            f"table name(s) in multiple schemas — {status}"
        )
        for table in sorted(schema_ambiguities):
            schemas = ", ".join(schema_ambiguities[table])
            lines.append(f"      {table} appears in schemas: {schemas}")
        if not ambiguity_acknowledged:
            blocked = True
            lines.append(
                "      Set dictionary.accept_schema_ambiguity: true in "
                "org_config.yaml to acknowledge, or resolve the ambiguity."
            )
    else:
        lines.append("[+] dictionary_schema_ambiguity: none")

    return GateResult(blocked=blocked, lines=lines)
