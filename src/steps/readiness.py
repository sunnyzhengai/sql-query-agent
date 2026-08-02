"""Step 06: the deployment readiness decision, as a pure function.

Takes every gate input (threshold measurements, invariant violations,
schema ambiguities, acknowledgment flag) and returns the verdict plus the
exact report lines to print — so the decision logic is testable in CI and
identical wherever the pipeline runs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GateResult:
    blocked: bool
    lines: "list[str]"


def readiness_gate(
    thresholds: "dict[str, tuple[float, float, bool]]",
    invariant_violations: "dict[str, list[str]]",
    schema_ambiguities: "dict[str, list[str]]",
    ambiguity_acknowledged: bool,
) -> GateResult:
    """thresholds: {name: (actual, threshold, is_blocking)}."""
    blocked = False
    lines: "list[str]" = []

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
