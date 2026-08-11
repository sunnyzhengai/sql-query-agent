"""The variants verb (set-subject): do all same-named definitions agree?

Born live 2026-08-10: six procs each define a step named
Base_Pop_Severe_ED_Scores and Sunny asked "are they all using the same
definition?" — the question a governance product exists to answer, and
one a pick menu structurally cannot: the subject is the FAMILY (every
step sharing the name), not one node, so there is no pick. Gather the
family with one fixed query, hash each fragment, partition by content.

Every pairwise phrasing ("is proc A's X the same as proc B's?") is a
slice of the same partition — the general answer dominates the specific
ones, so we always compute the whole and let the narrate edge answer
the question actually asked.

Deterministic end to end: fixed KQL, code-computed hashes and diffs,
code-stamped basis (ADR 0032). Flywheel note: drift findings deserve
their own event type (a governance signal, not a definition pick) —
future work, not wedged into PickEvent.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Callable

from src.orchestrator.assemble import NODE_FACTS_QUERY, FactSet

# Fixed family lookup: every step sharing the (case-folded) name.
FAMILY_QUERY = (
    "declare query_parameters(p_name:string);\n"
    "semantic_catalog | where ['kind'] == 'step' and tolower(name) == "
    "tolower(p_name)\n"
    "| project node_id, ['ref'], name\n"
    "| order by node_id asc"
)

_MAX_FRAGMENT_CHARS = 4000
_MAX_DIFF_LINES = 60


def _normalized(fragment: str) -> str:
    """Equality view of a fragment: whitespace runs collapsed, casefolded.
    T-SQL's default collation is case-insensitive (ADR 0016 spirit), so
    spacing and case are forgiven; any literal or structural difference
    still counts as a distinct definition.
    """
    return re.sub(r"\s+", " ", fragment or "").strip().casefold()


def _content_key(fragment: str) -> str:
    return hashlib.sha256(_normalized(fragment).encode()).hexdigest()[:16]


def _cap(text: str) -> str:
    if len(text) <= _MAX_FRAGMENT_CHARS:
        return text
    return text[:_MAX_FRAGMENT_CHARS] + "\n... (truncated)"


def _diff(a: str, b: str) -> str:
    lines = list(difflib.unified_diff(
        a.splitlines(), b.splitlines(),
        fromfile="definition_1", tofile="definition_2", lineterm="", n=1,
    ))
    if len(lines) > _MAX_DIFF_LINES:
        lines = lines[:_MAX_DIFF_LINES] + [
            f"... ({len(lines) - _MAX_DIFF_LINES} more diff lines)"
        ]
    return "\n".join(lines)


@dataclass(frozen=True)
class VariantGroup:
    content_key: str
    refs: "tuple[str, ...]"     # parent metric_ids sharing this definition
    fragment: str               # representative original text


@dataclass(frozen=True)
class VariantReport:
    name: str
    groups: "tuple[VariantGroup, ...]"   # largest first, then first ref
    basis: str

    @property
    def consistent(self) -> bool:
        return len(self.groups) == 1


def compare_variants(
    name: str, run_kql: "Callable[[str, dict], list[dict]]"
) -> "VariantReport | None":
    """The whole computation: family -> fragments -> partition by content.
    Returns None when no step carries the name (caller degrades to
    search — a misfired classification must never break the flow).
    """
    family_name = name.strip().lstrip("#").strip("[]")
    members = run_kql(FAMILY_QUERY, {"p_name": family_name})
    if not members:
        return None

    grouped: "dict[str, dict]" = {}
    for m in sorted(members, key=lambda r: r["node_id"]):
        rows = run_kql(NODE_FACTS_QUERY, {"p_node_id": m["node_id"]})
        props = (rows[0].get("properties") or "{}") if rows else "{}"
        if isinstance(props, str):
            props = json.loads(props)
        fragment = props.get("sql_fragment") or ""
        key = _content_key(fragment) if fragment.strip() else "unrecorded"
        grouped.setdefault(key, {"refs": [], "fragment": fragment})
        grouped[key]["refs"].append(m["ref"])

    groups = tuple(sorted(
        (VariantGroup(content_key=k, refs=tuple(sorted(v["refs"])),
                      fragment=v["fragment"])
         for k, v in grouped.items()),
        key=lambda g: (-len(g.refs), g.refs[0]),
    ))
    basis = (
        f"semantic_catalog[step name={family_name!r}] -> {len(members)} "
        f"definitions; graph_nodes[{len(members)} fragments] -> "
        f"{len(groups)} distinct (whitespace/case folded)"
    )
    return VariantReport(name=family_name, groups=groups, basis=basis)


def variant_facts(report: VariantReport) -> FactSet:
    """Project the partition into narratable facts. The narrate edge sees
    which procs share which definition and (when they differ) the diff —
    it answers the user's specific question from these facts alone."""
    all_refs = sorted(r for g in report.groups for r in g.refs)
    facts: dict = {
        "step_name": report.name,
        "defined_in": f"{len(all_refs)} procedure(s): " + ", ".join(all_refs),
        "distinct_definitions": len(report.groups),
        "all_agree": "yes" if report.consistent else "no",
    }
    if report.consistent and len(all_refs) == 1:
        facts["all_agree"] = ("only one procedure defines this step — "
                              "nothing to compare against")
    if report.consistent:
        facts["sql_fragment"] = _cap(report.groups[0].fragment)
    else:
        for i, g in enumerate(report.groups, 1):
            facts[f"definition_{i}_used_by"] = ", ".join(g.refs)
            facts[f"definition_{i}_sql"] = (
                _cap(g.fragment) if g.fragment.strip()
                else "(no SQL recorded)"
            )
        facts["diff_definition_1_vs_2"] = _diff(
            report.groups[0].fragment, report.groups[1].fragment
        )
        if len(report.groups) > 2:
            facts["note"] = (f"{len(report.groups)} distinct definitions "
                             "exist; the diff shown compares the two most "
                             "widely used")
    return FactSet(
        kind="variants", ref=report.name, facts=facts, basis=report.basis,
        sources=("semantic_catalog", "graph_nodes"),
    )


def variants_answer(
    name: str, run_kql: "Callable[[str, dict], list[dict]]"
) -> "FactSet | None":
    report = compare_variants(name, run_kql)
    return None if report is None else variant_facts(report)
