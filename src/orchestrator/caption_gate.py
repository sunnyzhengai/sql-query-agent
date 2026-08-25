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

from src.orchestrator.ops import (
    COLUMN_COVERAGE_CAVEAT,
    COMPARE_DIFFERS,
    COMPARE_IDENTICAL,
    SAMENESS_CAVEAT,
    normalize_kind,
)

_REF_TOKEN = re.compile(r"\b[R$]\d+\b")
_NUMBERS = re.compile(r"\b\d+\b")
# "nothing" left this lexicon in iteration 5: the bridge headline
# itself stamps "Nothing is NAMED 'X' exactly", and captions echoing
# the stamp were being floored by their own required phrasing.
_ABSOLUTE = re.compile(
    r"(?i)\b(?:all|every|none|only|no other|any other)\b")
_BRIDGE_STAMP = re.compile(r"closest by name: ([^.]+)\.")
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


def caption_violations(caption: str, outputs: "list[dict]",
                       ground_outputs: "list[dict] | None" = None
                       ) -> "list[str]":
    """Deterministic honesty checks. Empty list = the caption's claims
    are supported by what is on screen.

    `ground_outputs` (one mind): what claims are checked AGAINST —
    every result displayed this conversation. The bridge duty below
    binds to THIS TURN's results (`outputs`) only: a prior turn's
    sibling stamp must not impose its duty on every later caption."""
    grounds = ground_outputs if ground_outputs is not None else outputs
    violations: "list[str]" = []
    results = _results(grounds)
    text = _REF_TOKEN.sub(" ", caption)

    ground = _ground_numbers(grounds)
    for num in set(_NUMBERS.findall(text)):
        if num not in ground:
            violations.append(
                f"invented number: {num!r} appears in no displayed result")

    any_complete = any(r.get("complete") for r in results)
    if _ABSOLUTE.search(text) and not any_complete:
        violations.append(
            "absolute claim (all/none/only/every) but no displayed result "
            "set declared itself complete")

    # Sunny's bridge acceptance RULING (2026-08-21) — boundary rule,
    # explicitly authorized (supersedes the P4-default removal of
    # 2026-08-21 morning): when the headline stamps name-siblings,
    # they are presented FIRST, mandatory; meaning-related items are
    # permitted after. Grounded verification: both lists come from
    # code-stamped data and displayed rows, never a lexicon.
    # Aggregated with EXACT-stamp precedence (1.50.9): the exact-mode
    # stamp names the USER'S missed phrase; a model-widened semantic
    # search ('Sepsis' after 'Sepsis Case') stamps near-everything and
    # must not dilute the duty. Competitors are the displayed
    # candidate names across ALL results.
    turn_results = _results(outputs)
    stamped_hits = [
        (r, m) for r in turn_results
        for m in [_BRIDGE_STAMP.search(str(r.get("headline") or ""))]
        if m]
    if stamped_hits:
        exacts = [(r, m) for (r, m) in stamped_hits
                  if (r.get("params") or {}).get("mode") == "exact"]
        _, m2 = (exacts or stamped_hits)[0]
        stamped = [n.strip() for n in m2.group(1).split(",")
                   if n.strip()]
        # a stamped sibling row is a sibling wholly — its alternate
        # surface form (business vs metric name) is not a competitor
        others = sorted({
            str(v) for r in turn_results
            for row in (r.get("rows") or [])
            if not any(str(x) in stamped for x in
                       (row.get("business_name"), row.get("name")) if x)
            for v in (row.get("business_name"), row.get("name"))
            if v})
        low = caption.lower()
        pos_sib = [low.find(n.lower()) for n in stamped]
        pos_sib = min((p for p in pos_sib if p >= 0), default=None)
        pos_oth = [low.find(n.lower()) for n in others]
        pos_oth = min((p for p in pos_oth if p >= 0), default=None)
        # PRESENCE is mandatory, not just ordering (corpse 2026-08-21,
        # ratified-line conviction: the caption synthesized 'criteria'
        # from other metrics' summaries while naming ZERO displayed
        # candidates — even mangling a metric's name — and the old
        # check never fired because it only engaged on a mention).
        # A caption that cites a displayed ref (R1, ...) is pointing
        # AT the display, whose stamped headline carries the siblings
        # — that satisfies presence; a caption naming neither a
        # sibling nor a ref presents content anchored to nothing.
        if pos_sib is None and not _REF_TOKEN.search(caption):
            violations.append(
                "bridge acceptance (Sunny, 2026-08-21): the stamped "
                f"name-siblings ({', '.join(stamped[:3])}) are "
                "MANDATORY — present at least one, first")
        elif pos_oth is not None and pos_oth < pos_sib:
            violations.append(
                "bridge acceptance (Sunny, 2026-08-21): the stamped "
                f"name-siblings ({', '.join(stamped[:3])}) must be "
                "presented FIRST; meaning-related items may follow, "
                "labeled")

    # Sameness duty (walk W6/W7, Sunny 2026-08-23 — the build-stopper
    # corpse: "Yes, two other metrics use the same base population"
    # declared from a MENTION census; ground truth 9 procs, materially
    # different logic). Turn-scoped, like the bridge duty: when a
    # displayed headline carries the machine caveat (a step-name match
    # was on screen), the caption must echo the caveat or a compare
    # result must be displayed this turn. Structural — the stamp is a
    # code constant, no claim-shape lexicon; the floor renders the
    # stamped headlines, so a floored caption carries the caveat.
    sameness_stamped = any(
        SAMENESS_CAVEAT in str(r.get("headline") or "")
        or SAMENESS_CAVEAT in str(r.get("note") or "")
        for r in turn_results)
    if sameness_stamped:
        low_c = caption.lower()
        compare_shown = any(r.get("op") == "compare"
                            for r in turn_results)
        if ("not logic sameness" not in low_c
                and "not compared" not in low_c
                and not compare_shown):
            violations.append(
                "sameness duty (walk W6, 2026-08-23): a displayed "
                "headline stamps that step-NAME matches are not logic "
                "sameness — echo the caveat or run compare; an "
                "equivalence/difference claim from name or mention "
                "evidence is unsupported")

    # Compare-error duty (walk W12b, 2026-08-23 — the Q4 corpse: four
    # errored compares degraded into invented 'Replaced by'
    # relationships plus the exact conclusion the compares were meant
    # to establish). Turn-scoped, structural: a compare ERROR chip is
    # on screen and no successful compare result is — the caption must
    # echo the machine caveat. The floor renders the error line, which
    # carries the caveat verbatim.
    low_c = caption.lower()
    compare_errored = any(
        o.get("error") and (o.get("component") or {}).get("op") == "compare"
        for o in outputs)
    compare_succeeded = any(r.get("op") == "compare" for r in turn_results)
    if compare_errored and not compare_succeeded:
        if ("unverified" not in low_c and "not compared" not in low_c
                and "no comparison" not in low_c):
            violations.append(
                "compare-error duty (walk W12b, 2026-08-23): a compare "
                "operation FAILED this turn — the caption must state "
                "that sameness/difference/replacement remains "
                "unverified; it can never degrade into a claim")

    # Compare-direction duty (W15, gap-check corpse 2026-08-24: the
    # machine stamped 2 hash groups + a 103-line diff and the caption
    # called them "aligned" — the structural compare-present check
    # passed while the DIRECTION went unchecked). Turn-scoped: a
    # displayed compare headline carrying a typed verdict word binds
    # the caption to echo it. Structural — the verdict is a code
    # constant; the floor renders the stamped headline either way.
    differs_stamped = any(
        COMPARE_DIFFERS in str(r.get("headline") or "")
        or COMPARE_DIFFERS in str(r.get("note") or "")
        for r in turn_results)
    identical_stamped = any(
        COMPARE_IDENTICAL in str(r.get("headline") or "")
        or COMPARE_IDENTICAL in str(r.get("note") or "")
        for r in turn_results)
    if differs_stamped and "differ" not in low_c:
        violations.append(
            "compare-direction duty (W15, 2026-08-24): the displayed "
            "comparison stamps 'logic DIFFERS' — the caption must say "
            "so; 'aligned'/'similar' over a differing partition "
            "inverts machine truth")
    if identical_stamped and not differs_stamped \
            and "identical" not in low_c and "same" not in low_c:
        violations.append(
            "compare-direction duty (W15, 2026-08-24): the displayed "
            "comparison stamps 'logic IDENTICAL' — the caption must "
            "echo the verdict")

    # Column-coverage duty (walk W13b, 2026-08-23 — the
    # ED_DEPARTURE_TIME corpse: the headline scoped its zero to
    # 'recorded edges' and the caption dropped the qualifier,
    # claiming 'no certified metrics utilize this column'). When the
    # coverage caveat is stamped on screen, the caption must carry
    # the uncertainty.
    coverage_stamped = any(
        COLUMN_COVERAGE_CAVEAT in str(r.get("headline") or "")
        or COLUMN_COVERAGE_CAVEAT in str(r.get("note") or "")
        for r in turn_results)
    if coverage_stamped:
        if ("cannot conclude" not in low_c and "not tracked" not in low_c
                and "does not prove" not in low_c
                and "coverage" not in low_c):
            violations.append(
                "column-coverage duty (walk W13b, 2026-08-23): the "
                "displayed result stamps that 0 recorded edges cannot "
                "prove the column unused — the caption must carry "
                "that uncertainty, never an absolute absence claim")

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
    displayed results alone. Iteration 5: the floor IS the stamped
    headlines when they exist — so even a floored caption carries the
    bridge material and the step pointer (machine truth, verbatim)."""
    lines = []
    for o in outputs:
        r = o.get("result")
        if r is None:
            c = o.get("component") or {}
            lines.append(f"{c.get('op', 'component')}: "
                         f"{o.get('error', 'did not run')}")
            continue
        if r.get("headline"):
            lines.append(str(r["headline"]))
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
                # rows flagged name_match rode in via containment —
                # including token-degraded companions whose names hold
                # the phrase's tokens but not the verbatim phrase
                # (1.50.9: 'Sepsis Case Definition' stamps 'Sepsis
                # Case Details' / 'Sepsis Case Encounters')
                if r.get("name_match"):
                    val = str(r.get("business_name") or r.get("name")
                              or "")
                    if val and val not in contains:
                        contains.append(val)
                    continue
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
        # Decision evidence disclosure (M2 design pass 2026-08-21):
        # the metric record carries its top decision sites INLINE —
        # the stamp states the exact total and the shown cap (B3);
        # the remainder lives in the step records.
        dec_total = sum(int(r.get("decision_count") or 0)
                        for r in (result.get("rows") or []))
        dec_shown = sum(len(r.get("decision_sites") or [])
                        for r in (result.get("rows") or []))
        if dec_total and dec_shown:
            head += (f" {dec_total} decision site(s) carry the "
                     f"WHERE/CASE criteria — the top {dec_shown} are "
                     "ON THIS RECORD; the rest live in the step "
                     "records.")
        elif dec_total:
            head += (f" {dec_total} decision site(s) carry the "
                     "WHERE/CASE criteria — retrieve the step records "
                     "to read them.")
    if not result.get("complete"):
        head += " Not exhaustive."
    # An op's honesty note is machine truth too (walk step 1,
    # 2026-08-21: the empty exact search now carries its near-names in
    # `note` — stamping it here puts the did-you-mean in the headline,
    # which the template floor renders verbatim).
    note = str(result.get("note") or "").strip()
    if note:
        head += f" {note}"
    return head


def enforce_caption(caption: str, outputs: "list[dict]",
                    ground: "list[dict] | None" = None
                    ) -> "tuple[str, list[str]]":
    """Gate one caption. Returns (text, violations): the original text
    when clean, the template floor when not — never a repaired lie.

    `ground` is what the claims are checked AGAINST — in one mind that
    is every result displayed this conversation (walk find 2026-08-21:
    a zero-round answer restated a count from a prior turn's rows and
    was floored as an invented number). The FLOOR still renders only
    this turn's outputs."""
    violations = caption_violations(caption, outputs,
                                    ground_outputs=ground)
    if not violations or not caption:
        return (caption or template_caption(outputs)), violations
    return template_caption(outputs), violations
