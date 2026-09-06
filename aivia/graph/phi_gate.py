"""The PHI boundary (SAFE-1) — pure text -> (redacted text, counts).

REWORK of the proven src/phi_scan.py rule set (PM-1 RULED 2026-09-05),
narrowed to the pure signature and split into the two doors of the H6
closure (verbatim-after-redaction, both doors):

- door 1 (estate text, called by the mapper before evidence lands):
  SQL-anchored rules. HIGH-severity literals (contact / id / name)
  redact at intake; date and threshold literals are COUNTED findings
  whose redaction defers to egress. DERIVED, not chosen: the ratified
  F2 answer key keeps '2026-01-01' verbatim in evidence and parameter
  defaults — analytical dates ARE the logic; redacting them at intake
  would contradict the ratified key. (Flagged in the slice-2 report
  for Sunny's confirmation.)
- door 2 (free-typed usage payloads, the deferred ask surface):
  context-free shapes plus keyword-adjacent identifiers — free text
  has no column anchors, the gap PM-1's rework verdict anticipated.
  Fixtures: AIVIA_Product/fixtures/F6_refusals/phi_door2.json.

Deterministic, pattern-based, never LLM-based — a model detector would
require sending the text out, the exact thing being protected against.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

ID_COLUMN = r"[\w\[\]]*(?:_ID|CSN|MRN|_NBR)[\w\[\]]*"
NAME_COLUMN = r"[\w\[\]]*(?:NAME|PROVIDER|PHYSICIAN)[\w\[\]]*"

PLACEHOLDER = {"contact_literal": "<CONTACT>", "id_literal": "<ID>",
               "name_literal": "<NAME>", "date_literal": "<DATE>"}

# (rule, pattern, group holding the literal) — order matters: earlier
# rules claim spans; later rules skip overlaps (ported behavior).
_CONTACT_SHAPES = [
    ("contact_literal", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 0),
    ("contact_literal", re.compile(r"\b[\w.+-]+@[\w-]+\.\w{2,}\b"), 0),
    ("contact_literal", re.compile(
        r"\(\d{3}\)\s?\d{3}[-.]\d{4}|\b\d{3}[-. ]\d{3}[-.]\d{4}\b"), 0),
]
_DOOR1_REDACT = _CONTACT_SHAPES + [
    ("id_literal", re.compile(
        rf"(?i)\b({ID_COLUMN})\s*(?:=|!=|<>)\s*'?(\d{{5,}})'?"), 2),
    ("name_literal", re.compile(
        rf"(?i)\b({NAME_COLUMN})\s*(?:=|<>|!=|LIKE)\s*('[^']+')"), 2),
]
_DOOR1_COUNT_ONLY = [
    ("date_literal", re.compile(
        r"'(\d{4}-\d{1,2}-\d{1,2}(?:[ T][\d:.]+)?)'"), 0),
    ("date_literal", re.compile(r"'(\d{1,2}/\d{1,2}/\d{2,4})'"), 0),
    ("threshold_literal", re.compile(
        r"(?i)\b([\w\[\]\.]+)\s*(?:>=|<=|>|<)\s*(\d+(?:\.\d+)?)\b"), 2),
]
_DOOR2_REDACT = _CONTACT_SHAPES + [
    ("id_literal", re.compile(
        r"(?i)\b(?:MRN|CSN)\s*#?\s*(\d{5,})\b"), 1),
    ("date_literal", re.compile(
        r"(?i)\b(?:born|birth(?:\s*date)?|dob)\s*:?\s*"
        r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4})\b"), 1),
]


@dataclass(frozen=True)
class GateResult:
    text: str
    redaction_count: int
    counted_findings: Dict[str, int] = field(default_factory=dict)


def _apply(text: str, redact_rules, count_rules) -> GateResult:
    claimed: List[Tuple[int, int]] = []

    def free(start, end):
        return all(end <= s or start >= e for s, e in claimed)

    spans = []
    for rule, pattern, group in redact_rules:
        for m in pattern.finditer(text):
            start, end = m.span(group)
            if free(start, end):
                claimed.append((start, end))
                spans.append((start, end, PLACEHOLDER[rule]))
    counted: Dict[str, int] = {}
    for rule, pattern, group in count_rules:
        for m in pattern.finditer(text):
            if free(*m.span(group)):
                counted[rule] = counted.get(rule, 0) + 1
    out = text
    for start, end, placeholder in sorted(spans, reverse=True):
        span = out[start:end]
        # H6 seam (caught by the shapes PHI-probe file): a redaction
        # inside SQL must leave a VALID literal behind — when the
        # claimed span carries its own quotes, the placeholder goes
        # INSIDE them, so the redacted text still parses.
        if len(span) >= 2 and span[0] == span[-1] and span[0] in "'\"":
            placeholder = span[0] + placeholder + span[0]
        out = out[:start] + placeholder + out[end:]
    return GateResult(out, len(spans), counted)


def door1_redact(text: str) -> GateResult:
    """Estate text (SQL) entering the mapper — SAFE-1's first door."""
    return _apply(text, _DOOR1_REDACT, _DOOR1_COUNT_ONLY)


def door2_redact(text: str) -> GateResult:
    """Free-typed usage payloads — SAFE-1's second door (exercised by
    the deferred inward flow; the gate itself is live and tested now)."""
    return _apply(text, _DOOR2_REDACT, [])
