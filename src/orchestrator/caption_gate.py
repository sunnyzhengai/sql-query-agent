"""The caption gate — spec:E6 made mechanical for the plan surface.

Twin of the description grounding gate (src/descriptions.py, 2026-08-19):
prompt instructions are intent; only mechanical verification survives.
Origin (2026-08-20, Sunny's web-UI test): an exact name-search for the
word 'metrics' returned an honest empty, and the caption over-claimed
"there are currently no metrics available in the catalog" — a
kind-level absence conjured from a name-scoped result. The caption
prompt already forbade this; this gate enforces it.

Deterministic checks of a caption against the SAME result payload the
captioner saw:

1. numeric claims — every number in the caption must appear in the
   displayed results (rows, counts, universes); invented numbers die;
2. absolute claims (all / none / only / every / nothing) require at
   least one result set that declared itself COMPLETE;
3. kind-level absence ("no metrics", "there are no reports") requires
   a complete census of that kind showing zero rows.

Enforcement is the ADR 0044 shape: one corrective retry lives with the
caller (protocol.caption_turn); a caption that still violates drops to
the deterministic template floor — stilted but true, absence over
fabrication. The floor and the violations both ship to the surface, so
a corrected caption is visibly corrected.
"""

from __future__ import annotations

import json
import re

_REF_TOKEN = re.compile(r"\b[R$]\d+\b")
_NUMBERS = re.compile(r"\b\d+\b")
_ABSOLUTE = re.compile(
    r"(?i)\b(?:all|every|none|only|nothing|no other|any other)\b")
_KIND_ABSENCE = re.compile(
    r"(?i)\b(?:no|none|zero|not any|are no|aren't any)\b[^.;]{0,60}?"
    r"\b(metric|step|term|report|measure)s?\b")


def _ground_numbers(outputs: "list[dict]") -> "set[str]":
    ground = set(_NUMBERS.findall(json.dumps(outputs)))
    for o in outputs:
        rows = (o.get("result") or {}).get("rows")
        if rows is not None:
            ground.add(str(len(rows)))
    return ground


def _results(outputs: "list[dict]") -> "list[dict]":
    return [o["result"] for o in outputs if o.get("result")]


def caption_violations(caption: str, outputs: "list[dict]") -> "list[str]":
    """Deterministic honesty checks. Empty list = the caption's claims
    are supported by what is on screen."""
    violations: "list[str]" = []
    results = _results(outputs)
    text = _REF_TOKEN.sub(" ", caption)

    ground = _ground_numbers(outputs)
    for num in set(_NUMBERS.findall(text)):
        if num not in ground:
            violations.append(
                f"invented number: {num!r} appears in no displayed result")

    any_complete = any(r.get("complete") for r in results)
    if _ABSOLUTE.search(text) and not any_complete:
        violations.append(
            "absolute claim (all/none/only/every) but no displayed result "
            "set declared itself complete")

    for m in _KIND_ABSENCE.finditer(text):
        kind = m.group(1).lower()
        supported = any(
            r.get("op") == "census"
            and (r.get("params") or {}).get("kind") == kind
            and r.get("complete") and not r.get("rows")
            for r in results
        )
        if not supported:
            violations.append(
                f"kind-level absence claimed for {kind!r} without a "
                f"complete zero-row census of that kind — an empty NAME "
                f"lookup is not a kind census")
    return violations


def template_caption(outputs: "list[dict]") -> str:
    """The deterministic floor: stilted but true, computed from the
    displayed results alone."""
    lines = []
    for o in outputs:
        r = o.get("result")
        if r is None:
            c = o.get("component") or {}
            lines.append(f"{c.get('op', 'component')}: "
                         f"{o.get('error', 'did not run')}")
            continue
        n = len(r.get("rows") or [])
        lines.append(f"{r.get('ref')}: {r.get('op')} returned {n} row(s) — "
                     f"{r.get('universe', '')}")
    return ("Results as displayed. "
            + " ".join(lines)).strip()


def enforce_caption(caption: str, outputs: "list[dict]"
                    ) -> "tuple[str, list[str]]":
    """Gate one caption. Returns (text, violations): the original text
    when clean, the template floor when not — never a repaired lie."""
    violations = caption_violations(caption, outputs)
    if not violations or not caption:
        return (caption or template_caption(outputs)), violations
    return template_caption(outputs), violations
