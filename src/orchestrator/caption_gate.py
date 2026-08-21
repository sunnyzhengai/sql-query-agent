"""Presentation honesty for the plan surface — spec:E6.

Origin (2026-08-20, Sunny's web-UI test): an exact name-search for the
word 'metrics' returned an honest empty, and the caption over-claimed
"there are currently no metrics available in the catalog" — a
kind-level absence conjured from a name-scoped result.

TWO mechanisms, with honestly different strengths (review-session
verdict, relayed by Sunny 2026-08-20):

STAMPED HEADLINE — the guarantee (ADR 0032's provenance pattern:
stamped by code, never written by the LLM). Every result panel's
quantitative/existential sentence — count, scope, completeness, and
the kind-vs-name redirect — is rendered by stamped_headline() as a
fixed template over the result's own typed metadata. The LLM caption
is commentary BENEATH it; a lying caption is not caught, it is
contradicted on screen by a machine-stamped sentence standing above
it. No quantitative or existential claim reaches the user only through
LLM prose. This is what flips E6 to ENFORCED: checkable by
construction, no lexicon.

CAPTION LINT — defense-in-depth, MEASURED not tested (E3 vocabulary).
The claim-shape checks below (invented numbers, absolutes without a
complete set, kind-absence without a census) use a finite lexicon
against unbounded English — the approach ADR 0036 rejected as a
primary mechanism ("we can't possibly predict all shapes"). They stay
as a heuristic that catches the common shapes and floors the caption
(one corrective retry, then the deterministic template — the ADR 0044
shape), but no soundness claim rests on them.
"""

from __future__ import annotations

import json
import re

from src.orchestrator.ops import normalize_kind

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
        # Suite finding (first live run, 2026-08-20): requiring a
        # ZERO-row census false-fired on honest name-scoped phrasing
        # ("no metrics are NAMED sepsis") shown beside a 28-row census,
        # flooring a good caption. Any complete census of the kind on
        # screen means the true count is stamped in a headline — the
        # lint (a heuristic, MEASURED) stands down; the headline is the
        # guarantee.
        supported = any(
            r.get("op") == "census"
            and (r.get("params") or {}).get("kind") == kind
            and r.get("complete")
            for r in results
        )
        if not supported:
            violations.append(
                f"kind-level absence claimed for {kind!r} without a "
                f"complete census of that kind on screen — an empty NAME "
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


def stamped_headline(result: dict) -> str:
    """The code-stamped headline (ADR 0032 provenance pattern): a fixed
    template over the result's typed metadata. Deterministic and
    replayable; the sentence the user reads FIRST.

    Fixture case (the 2026-08-20 transcript): an empty exact search for
    'metrics' must headline the zero, the name-scope, and the census
    redirect — preempting the 'no metrics exist' over-claim on screen."""
    params = result.get("params") or {}
    op = result.get("op", "")
    n = len(result.get("rows") or [])
    parts = [f"{result.get('ref', '?')}: {op}"]
    if op == "search":
        parts.append(f"for {str(params.get('phrase', ''))!r} "
                     f"({params.get('mode', '')})")
    elif op == "census":
        parts.append(f"of kind {str(params.get('kind', ''))!r}")
    head = " ".join(parts) + f" — {n} row(s)."
    universe = result.get("universe", "")
    if universe:
        head += f" Scope: {universe}."
    if op == "search" and n == 0:
        kind = normalize_kind(str(params.get("phrase", "")))
        if kind is not None:
            head += (f" Note: {params.get('phrase', '')!r} is a catalog "
                     f"KIND — this was a name lookup, not a census; run "
                     f"census {kind} for the actual count.")
    if op == "search":
        # The bridge material, stamped (iteration 3: the captioner kept
        # synthesizing over near-name siblings it could see; the
        # containment set is DATA — code computes and states it).
        phrase = str(params.get("phrase", "")).strip().lower()
        rows = result.get("rows") or []
        if phrase:
            exact_hit = any(
                phrase == str(r.get(k) or "").strip().lower()
                for r in rows for k in ("name", "business_name"))
            contains = []
            for r in rows:
                for k in ("business_name", "name"):
                    val = str(r.get(k) or "")
                    if phrase in val.lower() and val not in contains:
                        contains.append(val)
                        break
            if contains and not exact_hit:
                head += (f" Nothing is NAMED {params.get('phrase', '')!r} "
                         f"exactly; closest by name: "
                         f"{', '.join(contains[:5])}.")
    if op == "retrieve":
        step_total = sum(len(r.get("steps") or [])
                         for r in (result.get("rows") or []))
        if step_total:
            head += (f" The record(s) list {step_total} calculation "
                     "step id(s) — criteria live in the step records, "
                     "not the summary.")
    if not result.get("complete"):
        head += " Not exhaustive."
    return head


def enforce_caption(caption: str, outputs: "list[dict]"
                    ) -> "tuple[str, list[str]]":
    """Gate one caption. Returns (text, violations): the original text
    when clean, the template floor when not — never a repaired lie."""
    violations = caption_violations(caption, outputs)
    if not violations or not caption:
        return (caption or template_caption(outputs)), violations
    return template_caption(outputs), violations
