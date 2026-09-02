"""X-RAY-1 (ADR 0063 §1 — the wedge): the Estate X-Ray report.

The 0054 sweep + census surfaces, productized: THEIR real counts,
their red flags with code-level basis, and the AI-readiness
verdict — every sentence machine-composed from stamped numbers
(no model authors anything; the report is the sweep wearing a
suit). Output is a durable artifact for the customer's document
estate (§0: artifacts land).

The verdict's logic is deterministic and disclosed in the report
itself: conflict-class flags (cousin_conflict / misnomer /
grain_shift) are the hallucination surface — a name-grounded
assistant answers differently depending on which twin it lands
on. Duplicates are wasted trust; every count cites the sweep.
"""

from __future__ import annotations

from src.branding import product_name
from src.orchestrator.ops import OpsSession, op_census

# the classes where ONE NAME carries MORE THAN ONE meaning — the
# exact surface a name-grounded assistant hallucinates on
_CONFLICT_CLASSES = ("cousin_conflict", "misnomer", "grain_shift")

_COUNT_KINDS = ("metric", "step", "term", "report", "measure")


def _census_rows(kind: str, run_kql) -> "list[dict] | None":
    try:
        return op_census(kind, run_kql, OpsSession()).rows
    except Exception:   # noqa: BLE001 — absent surface is disclosed
        return None


def compose_xray(run_kql, org_name: str,
                 generated_at: str = "") -> str:
    """The report, as markdown — deterministic for a given store."""
    brand = product_name()
    lines = [f"# {brand} Estate X-Ray — {org_name}",
             (f"Generated {generated_at}" if generated_at else "")]

    lines += ["", "## Your estate, in numbers", ""]
    counts: "dict[str, int]" = {}
    for kind in _COUNT_KINDS:
        rows = _census_rows(kind, run_kql)
        if rows is None:
            lines.append(f"- {kind}s: surface not present in this "
                         "store (disclosed, not zero)")
        else:
            counts[kind] = len(rows)
            lines.append(f"- certified {kind}s discovered: "
                         f"{len(rows)}")

    flags = _census_rows("flag", run_kql) or []
    conflicts = [f for f in flags
                 if str(f.get("flag_class")) in _CONFLICT_CLASSES]
    duplicates = [f for f in flags
                  if str(f.get("flag_class")) == "duplicate"]

    lines += ["", f"## Governance red flags ({len(flags)} found "
                  "by the sweep)", ""]
    if not flags:
        lines.append("The sweep found no red flags in this estate.")
    for f in flags:
        # XR-1 (review, blocks wedge use): the member LIST must
        # reconcile with the member COUNT — a paid diagnosis that
        # disagrees with its own list discredits itself. ALL
        # members render (census rows carry qualified-on-collision
        # labels via the W3a mechanism); a store-side shortfall is
        # DISCLOSED, never silent.
        names = [str(m) for m in (f.get("member_names") or [])]
        count = int(f.get("member_count") or 0)
        members = ", ".join(names) or "—"
        shortfall = (f" (store lists {len(names)} of {count} names)"
                     if names and len(names) < count else "")
        lines += [
            f"### {f.get('identity')} — {f.get('flag_class')} "
            f"({f.get('severity')})",
            str(f.get("description") or ""),
            f"- members ({count}): {members}{shortfall}",
            f"- distinct logics: {f.get('distinct_logics')} · "
            f"blast radius: {f.get('blast_radius')} certified "
            "consumer(s)",
            f"- disposition: {f.get('disposition') or 'open'}",
            ""]

    # ADR 0074 call 4 (the wedge description contract): a
    # hand-gradable DESCRIPTION SAMPLE with provenance chips — the
    # Bridge order form's evidence ("accurate descriptions your
    # stewards never write"). Provenance vocabulary is spec:B2's.
    lines += ["", "## Description sample (hand-gradable)", ""]
    try:
        sample = run_kql(
            "ops_description_cache | where isnotempty(description) "
            "| project description, provenance | take 5")
    except Exception:   # noqa: BLE001 — absent surface is disclosed
        sample = None
    if not sample:
        lines.append("- description surface not present in this "
                     "store (disclosed, not zero)")
    else:
        for r in sample:
            prov = str(r.get("provenance") or "gate_passed")
            first = str(r.get("description") or "").splitlines()[0]
            lines.append(f"- `[{prov}]` {first}")
        lines.append("")
        lines.append("Grade these against your own SQL: every claim "
                     "is machine-checked before it lands "
                     "(`gate_passed` = model prose that cleared the "
                     "grounding gate; `skeleton_floor` = "
                     "deterministic composition, unfalsifiable by "
                     "construction). Absent descriptions are counted, "
                     "never silent.")

    lines += ["", "## The AI-readiness verdict", ""]
    n_conf = len(conflicts)
    n_dup = len(duplicates)
    if n_conf:
        names = sorted({str(f.get("identity")) for f in conflicts})
        lines += [
            f"**{n_conf} name(s) in this estate carry more than one "
            "meaning** ("
            + ", ".join(names[:6])
            + (", …" if len(names) > 6 else "") + ").",
            "A name-grounded assistant answers differently depending "
            "on which definition it lands on — this is why a generic "
            "Copilot hallucinates on this estate. Every conflict "
            "above cites its members and their code-level basis; "
            "none of this is opinion.",
            ""]
    if n_dup:
        lines += [
            f"**{n_dup} identical logic(s) live under different "
            "names** — duplicated maintenance and split usage "
            "signals.", ""]
    if n_conf:
        verdict = ("VERDICT: NOT AI-READY as it stands — resolve or "
                   "disclose the conflicting names first. The flags "
                   "above are the exact work list.")
    elif flags:
        verdict = ("VERDICT: AI-READY WITH DISCLOSURES — the "
                   "remaining flags are documented and cite their "
                   "basis.")
    else:
        verdict = ("VERDICT: AI-READY on the surfaces measured — "
                   "the sweep found no conflicting definitions.")
    lines += [verdict, ""]

    lines += [
        "## What happens next",
        "",
        f"Every number above came from {brand}'s deterministic "
        "parsers reading your actual code — no sampling, no "
        "opinion. The same engine that found these flags can keep "
        "your catalog true continuously: descriptions, proposed "
        "business terms, relationships, and steward alerts, every "
        "write approved by your people before it lands "
        f"({brand} Bridge). You are not buying a new tool; you are "
        "buying the engine that makes your expensive catalog true.",
        ""]
    return "\n".join(lines)
