"""Filter grounding — spec:E5, the 123/456 lesson as a function.

    ∀v ∈ FilterValues(answer ∪ executed SQL).
        v ∈ Sites ∪ ValueSets ∪ HumanInput

Every literal in a proposed or executed filter must come from a stored
decision site, a value-set table (T_org), or the human — never from
model memory. The EMR schema travels between hospitals; the values
never do.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _norm(v) -> str:
    return str(v).strip().strip("'\"").upper()


@dataclass
class GroundingVerdict:
    grounded: bool = True
    ungrounded_values: "list[str]" = field(default_factory=list)


def filter_values_grounded(proposed_filters: "list[tuple]",
                           site_operands: "set[str]",
                           value_set_rows: "list",
                           human_inputs: "list[str]",
                           ) -> GroundingVerdict:
    """proposed_filters: (column, op, values) triples the engine wants
    to present or execute. Verdict is deterministic; a single value
    with no source fails the whole proposal (refuse-over-guess)."""
    allowed: "set[str]" = {_norm(v) for v in site_operands}
    for row in value_set_rows:
        if isinstance(row, dict):
            allowed.update(_norm(v) for v in row.values())
        else:
            allowed.add(_norm(row))
    allowed.update(_norm(v) for v in human_inputs)

    verdict = GroundingVerdict()
    for _column, _op, values in proposed_filters:
        if isinstance(values, (str, int, float)):
            values = [values]
        for v in values or []:
            if _norm(v) not in allowed:
                verdict.grounded = False
                verdict.ungrounded_values.append(str(v))
    return verdict
