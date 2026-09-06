"""The deterministic text gates — pure checkers (PROD-3 / GRND-2's
future consumer). PORTED essence of the proven produce gates (PM-2:
produce family only; the caption/grounding family defers with the
inward flow).

The contract: smoothing is a REPHRASING, not a rewrite. The gate
holds the candidate against the floor it was smoothed from — every
value survives, nothing is added, no raw identifier reaches steward
prose. A violation names itself; the caller's ruled response is to
ship the floor (an outage costs polish, never truth).
"""
import re
from typing import List

_QUOTED = re.compile(r"'[^']*'")
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")


def _values_in(text: str) -> set:
    return set(_QUOTED.findall(text)) | set(_NUMBER.findall(text))


def check_text(candidate: str, floor: str,
               forbidden_tokens: List[str]) -> List[str]:
    """Named violations, [] = clean. Deterministic; no model consulted."""
    violations = []
    floor_values = _values_in(floor)
    candidate_values = _values_in(candidate)
    for value in sorted(floor_values - candidate_values):
        violations.append(f"GATE-VALUE-1: value {value} dropped — every "
                          "value must survive smoothing")
    for value in sorted(candidate_values - floor_values):
        violations.append(f"GATE-VALUE-2: value {value} added — the model "
                          "never adds a fact")
    for token in forbidden_tokens:
        # CASE-SENSITIVE whole-token match: the ban is on the raw
        # identifier appearing verbatim ('APPT_STATUS_C'), never on the
        # English word it shares letters with ('encounters' vs ENCOUNTER
        # — caught by the injection cases at first build)
        if re.search(rf"(?<![\w.]){re.escape(token)}(?![\w.])", candidate):
            violations.append(f"GATE-VOICE-1: raw identifier '{token}' in "
                              "steward prose")
    if not candidate.strip():
        violations.append("GATE-SHELL-1: empty candidate")
    return violations
