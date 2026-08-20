"""The blind verifier — ADR 0044 clause 3, spec:F's ρ.

Information-flow constraint enforced at the SIGNATURE: the
reconstruction prompt is built from exactly (description, dict_lines).
There is no parameter through which the SQL or the original tree could
arrive — the verifier reconstructs from the prose alone, which is what
makes agreement EVIDENCE instead of circularity.
"""

from __future__ import annotations

import json
import re

_RECON_PROMPT = (
    "You are auditing a certified metric's step description by "
    "reconstructing the decisions it claims, EXACTLY as written — do "
    "not guess beyond the text.\n"
    "{dict_block}"
    "Step description under audit:\n{description}\n\n"
    "Output ONLY a JSON array. One object per decision the description "
    "states, each: {{\"op\": one of EQ,NEQ,GT,GTE,LT,LTE,IN,NOT_IN,"
    "BETWEEN,NOT_BETWEEN,LIKE,NOT_LIKE,IS,IS_NOT,EXISTS,"
    "PARAMETER_DEFAULT,UNKNOWN; \"column\": the data element name the "
    "description implies (use the dictionary to map business phrases "
    "back to element names; null if unstated); for a decision that "
    "MATCHES two data elements (a join), instead output \"columns\": "
    "[both element names]; \"values\": the literal "
    "codes/numbers/tokens stated; \"or_group\": a shared tag like \"g1\" "
    "for decisions the text presents as alternatives (either/or), "
    "omitted otherwise}}. Represent 'is not null' as op IS_NOT with no "
    "values. If the description states no decisions, output []. No "
    "commentary, no markdown fences."
)


def build_reconstruction_prompt(description: str,
                                dict_lines: "list[str]") -> str:
    dict_block = ""
    if dict_lines:
        entries = "\n".join(dict_lines[:30])
        dict_block = (f"Data dictionary (map business phrases back to "
                      f"element names using these):\n{entries}\n\n")
    return _RECON_PROMPT.format(description=description,
                                dict_block=dict_block)


_JSON_ARRAY = re.compile(r"\[.*\]", re.S)


def parse_reconstruction(response: str) -> "list[dict]":
    """Tolerant JSON extraction; an unparseable response reconstructs
    NOTHING (an empty fact list), which honestly fails the diff — the
    round trip never passes by accident."""
    m = _JSON_ARRAY.search(response or "")
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    return [f for f in data if isinstance(f, dict)]
