"""The compare verb: two metrics, one fixed panel (ADR 0034).

Born from the verb-scorecard game (2026-08-10). Three rules extracted
there, implemented here:

1. The LLM never judges sameness — code computes it (whole-logic hash,
   per-shared-step hash via the variants kernel).
2. A comparison has three slots: subject A, subject B, and the ASPECT.
   "Same sepsis definition?" is not "identical metrics?" — a concept
   aspect resolves INSIDE each subject's steps and the equality kernel
   runs on the matched pair, never the wholes.
3. Field comparison is TYPED: scalar fields (developer, steward,
   report) compare as equality; list fields (tables, steps) compare as
   set algebra — shared / only-in-A / only-in-B.

The panel runs in full on every call regardless of phrasing (the
general answer dominates every specific one); the narrate edge answers
the question actually asked from the computed facts.
"""

from __future__ import annotations

from typing import Callable

from src.graph.templates import _fold
from src.orchestrator.assemble import FactSet, assemble_metric
from src.orchestrator.core import Candidate
from src.orchestrator.variants import _cap, _content_key, _diff

# Fixed lookups. Step lists come from the same semantic catalog the
# resolver uses; a step's ['ref'] IS its parent metric_id (catalog
# contract).
STEPS_OF_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "semantic_catalog | where ['kind'] == 'step' and ['ref'] == p_ref\n"
    "| project node_id, name\n"
    "| order by node_id asc"
)

# Concept-aspect resolution, scoped to the two subjects: the SAME
# semantic_search, wider net, filtered to steps of A and B. The concept
# is a parameter; the query text never changes.
SCOPED_RESOLVE_QUERY = (
    "declare query_parameters(token:string, p_a:string, p_b:string);\n"
    "semantic_search(token, 200)\n"
    "| where ['kind'] == 'step' and ['ref'] in (p_a, p_b)"
)

# Batched fragment fetch: two sibling procs can share dozens of step
# names, and one round trip per fragment was measured too slow live
# (2026-08-10). The id list travels as a JSON string parameter.
BATCH_FRAGMENTS_QUERY = (
    "declare query_parameters(p_ids:string);\n"
    "graph_nodes\n"
    "| where set_has_element(todynamic(p_ids), node_id)\n"
    "| project node_id, properties"
)

MAX_SHARED_STEP_CHECKS = 20   # fragment fetches are 2 per shared name

# Aspect-zoom policy (live find 2026-08-10: the chooser dumped a proc's
# ENTIRE 32-step inventory on the user — the system delegating its
# hardest question to the person who asked it). Deterministic ladder:
# nothing clears the floor -> say the concept doesn't map cleanly and
# answer from the full panel; one clear match -> auto-bind; a few
# contenders -> ask, showing at most 5, with 'n' meaning skip the zoom.
# Floor calibrated from live data: exact-name concepts score ~0.71,
# vague concepts top out ~0.56.
ASPECT_CHOICES_SHOWN = 5
ASPECT_MATCH_FLOOR = 0.60

# Aspects that are schema FIELDS need no resolution — the panel already
# computes them; the narrate edge just answers from the facts.
_FIELD_ASPECTS = {
    "developer", "developers", "steward", "stewards", "owner", "owners",
    "ownership", "table", "tables", "source tables", "sources", "step",
    "steps", "sql", "logic", "code", "calculation", "report", "reports",
    "link", "dashboard",
}


def is_field_aspect(aspect: str) -> bool:
    return _fold(aspect.strip()) in {_fold(a) for a in _FIELD_ASPECTS}


def _fragments(run_kql, node_ids: "list[str]") -> "dict[str, str]":
    """One round trip for any number of fragments; missing ids simply
    absent from the result (compared as empty — honest, not invented)."""
    import json
    if not node_ids:
        return {}
    rows = run_kql(BATCH_FRAGMENTS_QUERY,
                   {"p_ids": json.dumps(sorted(node_ids))})
    out = {}
    for r in rows:
        props = r.get("properties") or "{}"
        if isinstance(props, str):
            props = json.loads(props)
        out[r["node_id"]] = props.get("sql_fragment") or ""
    return out


def _scalar_verdict(label_a: str, label_b: str, a, b) -> str:
    if not a and not b:
        return "not recorded for either"
    if a and not b:
        return f"only {label_a} records one ({a})"
    if b and not a:
        return f"only {label_b} records one ({b})"
    return f"yes ({a})" if a == b else f"no ({label_a}: {a} / {label_b}: {b})"


def _table_set(facts: dict) -> "set[str]":
    raw = facts.get("source_tables") or ""
    return {t.strip() for t in raw.split(",") if t.strip()}


def _logic_verdict(a: "str | None", b: "str | None") -> str:
    if not (a or "").strip() or not (b or "").strip():
        return "cannot verify — calculation not recorded for one or both"
    return "yes" if _content_key(a) == _content_key(b) else "no"


def build_comparison(
    ref_a: str,
    ref_b: str,
    run_kql: "Callable[[str, dict], list[dict]]",
    chosen_aspect: "str | None" = None,
    choose: "Callable[[str, tuple], int] | None" = None,
) -> FactSet:
    """The full panel, computed by code. `choose(side_label, candidates)`
    is the surface's pick UI, invoked ONLY when a concept aspect matches
    more than one step on a side (amendment 2: human picks, no bypass).
    Raises AssemblyError (from assemble_metric) if a subject has no facts.
    """
    fa = assemble_metric(ref_a, run_kql)
    fb = assemble_metric(ref_b, run_kql)
    label_a = fa.facts.get("business_name") or ref_a
    label_b = fb.facts.get("business_name") or ref_b

    steps_a = run_kql(STEPS_OF_QUERY, {"p_ref": ref_a})
    steps_b = run_kql(STEPS_OF_QUERY, {"p_ref": ref_b})
    names_a = {r["name"]: r["node_id"] for r in steps_a}
    names_b = {r["name"]: r["node_id"] for r in steps_b}
    shared = sorted(set(names_a) & set(names_b))

    checked = shared[:MAX_SHARED_STEP_CHECKS]
    frags = _fragments(run_kql, [names_a[n] for n in checked]
                       + [names_b[n] for n in checked])
    agree, drifted, unrecorded = [], [], []
    for name in checked:
        frag_a = frags.get(names_a[name], "")
        frag_b = frags.get(names_b[name], "")
        if not frag_a.strip() or not frag_b.strip():
            unrecorded.append(name)   # empty==empty is NOT identity
        elif _content_key(frag_a) == _content_key(frag_b):
            agree.append(name)
        else:
            drifted.append(name)

    tables_a, tables_b = _table_set(fa.facts), _table_set(fb.facts)
    f = fa.facts

    facts: dict = {
        "subject_1": f"{label_a} ({ref_a})",
        "subject_2": f"{label_b} ({ref_b})",
        "same_developer": _scalar_verdict(
            label_a, label_b, f.get("developer"), fb.facts.get("developer")),
        "same_steward": _scalar_verdict(
            label_a, label_b, f.get("steward"), fb.facts.get("steward")),
        "same_report": _scalar_verdict(
            label_a, label_b, f.get("report_name"), fb.facts.get("report_name")),
        "whole_calculation_identical": _logic_verdict(
            f.get("calculation_logic"), fb.facts.get("calculation_logic")),
        "shared_tables": ", ".join(sorted(tables_a & tables_b)) or "(none)",
        "tables_only_in_subject_1": ", ".join(sorted(tables_a - tables_b)) or "(none)",
        "tables_only_in_subject_2": ", ".join(sorted(tables_b - tables_a)) or "(none)",
        "shared_step_names": ", ".join(shared) or "(none)",
        "shared_steps_with_identical_logic": ", ".join(agree) or "(none)",
        "shared_steps_with_different_logic": ", ".join(drifted) or "(none)",
    }
    if unrecorded:
        facts["shared_steps_where_logic_not_comparable"] = (
            ", ".join(unrecorded) + " (SQL not recorded for one or both)")
    if len(shared) > MAX_SHARED_STEP_CHECKS:
        facts["note"] = (
            f"{len(shared)} step names are shared; logic was checked for "
            f"the first {MAX_SHARED_STEP_CHECKS}")

    fragment_lookups = 2 * min(len(shared), MAX_SHARED_STEP_CHECKS)
    basis_parts = [
        f"output_metric_logic[{ref_a!r}, {ref_b!r}] -> 2 rows",
        f"semantic_catalog[steps of both] -> {len(names_a)}+{len(names_b)} "
        f"steps, {len(shared)} shared names",
        f"graph_nodes[{fragment_lookups} fragments] -> "
        f"{len(agree)} identical, {len(drifted)} drifted",
    ]

    if chosen_aspect and not is_field_aspect(chosen_aspect):
        basis_parts.append(_aspect_panel(
            facts, chosen_aspect, ref_a, ref_b, label_a, label_b,
            run_kql, choose))

    return FactSet(
        kind="comparison", ref=f"{ref_a} vs {ref_b}", facts=facts,
        basis="; ".join(basis_parts),
        sources=("output_metric_logic", "semantic_catalog", "graph_nodes"),
    )


def _aspect_panel(facts, aspect, ref_a, ref_b, label_a, label_b,
                  run_kql, choose) -> str:
    """Amendment 2: resolve the concept INSIDE each subject, pick when
    ambiguous, equality-kernel the matched pair. Mutates `facts`;
    returns its basis clause."""
    rows = run_kql(SCOPED_RESOLVE_QUERY,
                   {"token": aspect, "p_a": ref_a, "p_b": ref_b})
    per_side = {ref_a: [], ref_b: []}
    for r in sorted(rows, key=lambda r: (-float(r["closeness"]), r["node_id"])):
        per_side[r["ref"]].append(r)

    matched = {}
    for ref, label in ((ref_a, label_a), (ref_b, label_b)):
        side = per_side[ref][:ASPECT_CHOICES_SHOWN]
        if not side or float(side[0]["closeness"]) < ASPECT_MATCH_FLOOR:
            best = f" (best closeness {side[0]['closeness']:.2f})" if side else ""
            facts[f"'{aspect}' in {label}"] = (
                "no step clearly matches this concept"
                f"{best} — see the shared-step comparison instead")
            continue
        idx = 0
        if len(side) > 1 and choose is not None:
            candidates = tuple(
                Candidate(node_id=r["node_id"], kind="step", ref=r["ref"],
                          name=r["name"],
                          business_name=r.get("business_name") or "",
                          display_text=r.get("display_text") or "",
                          closeness=float(r["closeness"]),
                          total_matches=len(side))
                for r in side)
            idx = choose(f"Which step in {label} is '{aspect}'? "
                         "('n' = skip, answer from the full comparison)",
                         candidates)
            if idx is None:
                facts[f"'{aspect}' in {label}"] = (
                    "zoom skipped — answered from the full comparison")
                continue
        matched[ref] = side[idx]
        facts[f"'{aspect}' in {label}"] = side[idx]["name"]

    if len(matched) == 2:
        pair = _fragments(run_kql, [matched[ref_a]["node_id"],
                                    matched[ref_b]["node_id"]])
        frag_a = pair.get(matched[ref_a]["node_id"], "")
        frag_b = pair.get(matched[ref_b]["node_id"], "")
        if not frag_a.strip() or not frag_b.strip():
            facts[f"'{aspect}' logic identical"] = (
                "cannot verify — SQL not recorded for one or both steps")
        elif _content_key(frag_a) == _content_key(frag_b):
            facts[f"'{aspect}' logic identical"] = "yes"
        else:
            facts[f"'{aspect}' logic identical"] = "no"
            facts[f"'{aspect}' diff"] = _diff(_cap(frag_a), _cap(frag_b))
    return (f"semantic_search({aspect!r}) scoped to both subjects -> "
            f"{len(per_side[ref_a])}+{len(per_side[ref_b])} step matches")
