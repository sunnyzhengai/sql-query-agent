"""The deterministic template floor (ADR 0044 clause 6's floor, built
in phase 2 because clause 5 needs it too).

render_fact turns one decision leaf into stilted-but-TRUE English with
zero LLM involvement — the worst text this system can publish. Phase 2
uses it for facts the translator failed to voice (the ledger's unvoiced
side still appears in output, truthfully); phase 3 uses it as the
never-converging fallback with provenance template_fallback.
"""

from __future__ import annotations

_OP_TEMPLATES = {
    "EQ": "{col} equals {ops}",
    "NEQ": "{col} is not {ops}",
    "GT": "{col} is greater than {ops}",
    "GTE": "{col} is at least {ops}",
    "LT": "{col} is less than {ops}",
    "LTE": "{col} is at most {ops}",
    "IN": "{col} is one of {ops}",
    "NOT_IN": "{col} is none of {ops}",
    "BETWEEN": "{col} is between {ops}",
    "NOT_BETWEEN": "{col} is outside {ops}",
    "LIKE": "{col} matches the pattern {ops}",
    "NOT_LIKE": "{col} does not match the pattern {ops}",
    "IS": "{col} is null",
    "IS_NOT": "{col} is not null",
    "EXISTS": "a matching record exists ({expr})",
    "PARAMETER_DEFAULT": "when not supplied, defaults apply: {ops}",
}


def render_fact(fact: dict) -> str:
    """One leaf -> one true line. `fact` is a DecisionNode.to_dict()."""
    op = fact.get("op") or "?"
    col = fact.get("column") or (
        fact["columns"][0] if fact.get("columns") else "the expression")
    ops = ", ".join(fact.get("operands") or []) or "(no literal values)"
    template = _OP_TEMPLATES.get(op)
    if template is None:
        return f"- condition holds: {fact.get('expression_sql', '')[:160]}"
    body = template.format(col=col, ops=ops,
                           expr=fact.get("expression_sql", "")[:120])
    prefix = {"where": "filters rows so that",
              "join_on": "joined where",
              "having": "kept only when (after grouping)",
              "case_when": "categorized when",
              "parameter_default": "reporting window:"}.get(
                  fact.get("context", ""), "condition:")
    return f"- {prefix} {body}"


def render_template(facts: "list[dict]", step_name: str = "") -> str:
    """Whole-step floor text: complete, unpolished, TRUE."""
    header = (f"This step ({step_name}) applies the following decisions:"
              if facts else
              f"This step ({step_name}) carries data forward without "
              f"filtering decisions.")
    return "\n".join([header] + [render_fact(f) for f in facts])
