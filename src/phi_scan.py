"""PHI / hardcoded-literal scanning of customer SQL (ADR 0025).

Deterministic, pattern-based, never LLM-based — an LLM detector would
require sending the text out, the exact thing being protected against.
Five rules, each named in the ADR and the ops_phi_findings contract:

    contact_literal    SSN / email / phone shapes            high    redact
    id_literal         long numerics against id-ish columns  high    redact
    name_literal       string literals against name columns  high    redact
    date_literal       quoted date/datetime literals         medium  redact
    threshold_literal  bare numeric comparisons              low     open

Dispositions: high/medium findings default to `redact`; threshold
findings open for steward review (hardcoded business thresholds are
governance smells, not PHI). Redaction applies at every point SQL-derived
text leaves the lakehouse (description prompts, catalog publishes); the
graph keeps the original fragment — nothing inside the tenant is blocked.

Parameters (@dStartDate) never match: every rule requires a literal.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

ID_COLUMN = r"[\w\[\]]*(?:_ID|CSN|MRN|_NBR)[\w\[\]]*"
NAME_COLUMN = r"[\w\[\]]*(?:NAME|PROVIDER|PHYSICIAN)[\w\[\]]*"

PLACEHOLDERS = {
    "contact_literal": "<CONTACT>",
    "id_literal": "<ID>",
    "name_literal": "<NAME>",
    "date_literal": "<DATE>",
    "threshold_literal": "<VALUE>",  # unused unless a steward flips to redact
}

SEVERITY = {
    "contact_literal": "high",
    "id_literal": "high",
    "name_literal": "high",
    "date_literal": "medium",
    "threshold_literal": "low",
}

DEFAULT_DISPOSITION = {
    "contact_literal": "redact",
    "id_literal": "redact",
    "name_literal": "redact",
    "date_literal": "redact",
    "threshold_literal": "open",
}

# Rule order matters: earlier rules claim their spans; later rules skip
# anything overlapping an already-claimed span (a matched SSN must not
# re-fire as a threshold comparison).
_RULES: "list[tuple[str, re.Pattern, int]]" = [
    # (rule, pattern, group index of the literal to redact)
    ("contact_literal", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 0),
    ("contact_literal", re.compile(r"\b[\w.+-]+@[\w-]+\.\w{2,}\b"), 0),
    ("contact_literal", re.compile(r"\b\(?\d{3}\)?[-. ]\d{3}[-.]\d{4}\b"), 0),
    ("id_literal", re.compile(
        rf"(?i)\b({ID_COLUMN})\s*(?:=|!=|<>)\s*'?(\d{{5,}})'?"), 2),
    ("name_literal", re.compile(
        rf"(?i)\b({NAME_COLUMN})\s*(?:=|<>|!=|LIKE)\s*('[^']+')"), 2),
    ("date_literal", re.compile(
        r"'(\d{4}-\d{1,2}-\d{1,2}(?:[ T][\d:.]+)?)'"), 0),
    ("date_literal", re.compile(r"'(\d{1,2}/\d{1,2}/\d{2,4})'"), 0),
    ("threshold_literal", re.compile(
        r"(?i)\b([\w\[\]\.]+)\s*(?:>=|<=|>|<)\s*(\d+(?:\.\d+)?)\b"), 2),
]

_CONTEXT = 30

# IN-lists against id columns need their own pass: every member must be
# flagged, not just the first (an IN-list of 30 CSNs is 30 findings).
_ID_IN_LIST = re.compile(rf"(?i)\b({ID_COLUMN})\s+IN\s*\(([^)]*)\)")
_LONG_NUMBER = re.compile(r"\d{5,}")


@dataclass(frozen=True)
class Finding:
    finding_id: str
    metric_id: str
    rule: str
    matched_text: str
    masked_context: str
    severity: str
    disposition: str


def _finding_id(metric_id: str, rule: str, matched: str) -> str:
    payload = f"{metric_id}|{rule}|{matched}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _mask_context(text: str, start: int, end: int, rule: str) -> str:
    lo = max(0, start - _CONTEXT)
    hi = min(len(text), end + _CONTEXT)
    snippet = text[lo:start] + PLACEHOLDERS[rule] + text[end:hi]
    return snippet.replace("\n", " ").strip()


def scan_sql(metric_id: str, sql: str) -> "list[Finding]":
    """Run every rule over one SQL text; one Finding per matched literal."""
    if not sql:
        return []
    findings: "list[Finding]" = []
    claimed: "list[tuple[int, int]]" = []
    seen_ids: "set[str]" = set()

    def overlaps(start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in claimed)

    def add(rule: str, start: int, end: int) -> None:
        claimed.append((start, end))
        matched = sql[start:end]
        fid = _finding_id(metric_id, rule, matched)
        # The same literal repeated in one proc (code lists copied across
        # CTEs) hashes to the same id: ONE finding, first occurrence's
        # context — one steward decision per (metric, rule, value). The
        # ops_phi_findings unique(finding_id) invariant enforces this
        # (caught live by 02's postcondition gate, 2026-08-15).
        if fid in seen_ids:
            return
        seen_ids.add(fid)
        findings.append(Finding(
            finding_id=fid,
            metric_id=metric_id,
            rule=rule,
            matched_text=matched,
            masked_context=_mask_context(sql, start, end, rule),
            severity=SEVERITY[rule],
            disposition=DEFAULT_DISPOSITION[rule],
        ))

    # IN-list pass first: flag EVERY long number in the list
    for m in _ID_IN_LIST.finditer(sql):
        list_start = m.start(2)
        for num in _LONG_NUMBER.finditer(m.group(2)):
            start, end = list_start + num.start(), list_start + num.end()
            if not overlaps(start, end):
                add("id_literal", start, end)

    for rule, pattern, group in _RULES:
        for m in pattern.finditer(sql):
            start, end = m.span(group)
            if not overlaps(start, end):
                add(rule, start, end)
    return findings


def redact(sql: str, findings: "list[Finding]") -> str:
    """Substitute placeholders for every redact-disposition finding.

    Longest matches first so a literal that contains another (a date
    inside a datetime) cannot leave fragments behind.
    """
    to_redact = sorted(
        (f for f in findings if f.disposition == "redact"),
        key=lambda f: len(f.matched_text), reverse=True,
    )
    for f in to_redact:
        sql = sql.replace(f.matched_text, PLACEHOLDERS[f.rule])
    return sql


def to_records(findings: "list[Finding]", first_seen: str = "") -> "list[dict]":
    """Rows shaped for the ops_phi_findings contract (src/schemas.py)."""
    return [
        {
            "finding_id": f.finding_id,
            "metric_id": f.metric_id,
            "rule": f.rule,
            "matched_text": f.matched_text,
            "masked_context": f.masked_context,
            "severity": f.severity,
            "disposition": f.disposition,
            "disposed_by": "",
            "first_seen": first_seen,
        }
        for f in findings
    ]


def from_records(records: "list[dict]") -> "list[Finding]":
    """Findings back from persisted ops_phi_findings rows (07's read path)."""
    return [
        Finding(
            finding_id=r["finding_id"],
            metric_id=r["metric_id"],
            rule=r["rule"],
            matched_text=r["matched_text"],
            masked_context=r.get("masked_context", ""),
            severity=r["severity"],
            disposition=r["disposition"],
        )
        for r in records
    ]


def redact_node_fragments(
    nodes_rows: "list[dict]", findings: "list[Finding]"
) -> int:
    """Redact flagged literals from transformation sql_fragments in place.

    The egress gate for description generation: fragments are redacted
    before any prompt is built. Returns the number of fragments changed.
    Handles rows whose properties are dicts or JSON strings.
    """
    import json as _json

    by_metric: "dict[str, list[Finding]]" = {}
    for f in findings:
        if f.disposition == "redact":
            by_metric.setdefault(f.metric_id, []).append(f)
    changed = 0
    for row in nodes_rows:
        if row.get("layer") != "transformation":
            continue
        was_str = isinstance(row["properties"], str)
        props = _json.loads(row["properties"]) if was_str else row["properties"]
        fragment = props.get("sql_fragment") or ""
        relevant = by_metric.get(props.get("metric_id", ""), [])
        if not (fragment and relevant):
            continue
        redacted = redact(fragment, relevant)
        if redacted != fragment:
            props["sql_fragment"] = redacted
            if was_str:
                row["properties"] = _json.dumps(props)
            changed += 1
    return changed


def apply_dispositions(
    findings: "list[Finding]", existing: "list[dict]"
) -> "list[Finding]":
    """Carry steward dispositions forward from persisted findings.

    A steward's `allow` (confirmed false positive) or explicit `redact`
    on a threshold survives re-scans: dispositions keyed by finding_id,
    which is stable for unchanged (metric, rule, literal) triples.
    """
    by_id = {r["finding_id"]: r.get("disposition", "") for r in existing}
    out = []
    for f in findings:
        prior = by_id.get(f.finding_id)
        if prior and prior != f.disposition:
            out.append(Finding(
                finding_id=f.finding_id, metric_id=f.metric_id, rule=f.rule,
                matched_text=f.matched_text, masked_context=f.masked_context,
                severity=f.severity, disposition=prior,
            ))
        else:
            out.append(f)
    return out
