"""ADR 0059 — the graph topology axioms, mechanized.

G1 accounted connectivity: undirected components are ENUMERATED every
build; exactly one PRINCIPAL component carries the derived layers
(org, canonical, governance — where disconnection signals a defect);
foundation-only components are LEGITIMATE STATES under the FOUNDATION
EXCEPTION (Sunny, 2026-08-26: the dictionary is a source of truth —
its islands are enumerated for visibility, never findings). Degree-0
nodes are forbidden outright, with one enumerated exclusion: the
`govmeta:sweep` build receipt (metadata by construction, typed here,
never silent).

G2 edge soundness: every edge referential (both endpoints exist) and
provenanced (EDGE_PROVENANCE totality — parsed/declared/derived/
asserted, exactly one class per type).

Union-find, pure, over row dicts — the same analysis runs as the CI
leg (recorded corpus), inside 300's postconditions (build time), and
in the live audit (store rows).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models import EDGE_PROVENANCE, EdgeType

# G1's enumerated degree-0 exclusions — typed, visible, never silent
DEGREE_ZERO_EXCLUSIONS = {"govmeta:sweep": "build_receipt"}

# layers where disconnection from the principal component is a DEFECT
DERIVED_LAYERS = frozenset(
    {"canonical", "transformation", "report", "measure", "decision",
     "governance"})


@dataclass
class Topology:
    node_count: int = 0
    edge_count: int = 0
    components: int = 0
    principal_size: int = 0
    # G1 violations (empty = axiom holds)
    dangling_edges: "list[tuple]" = field(default_factory=list)
    degree_zero: "list[str]" = field(default_factory=list)
    stray_derived_components: "list[list[str]]" = field(
        default_factory=list)
    unmapped_edge_types: "list[str]" = field(default_factory=list)
    # the foundation exception: legitimate, enumerated, never findings
    foundation_islands: "list[list[str]]" = field(default_factory=list)
    # typed isolation (live find 2026-08-26, first tenant run of this
    # leg: the admin-telemetry semantic model formed its own
    # report/measure-only component — its anchor tables are not
    # dictionary-tracked, so nothing joins it to the principal). A
    # consumption-only component is a LEGITIMATE state with a typed
    # reason, enumerated for visibility — Q1's own form ("every
    # component is principal OR carries a typed isolation reason").
    consumption_unanchored: "list[list[str]]" = field(
        default_factory=list)
    excluded_degree_zero: "dict[str, str]" = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not (self.dangling_edges or self.degree_zero
                    or self.stray_derived_components
                    or self.unmapped_edge_types)

    def summary(self) -> str:
        return (f"{self.node_count} nodes / {self.edge_count} edges; "
                f"components={self.components} "
                f"(principal={self.principal_size}, foundation "
                f"islands={len(self.foundation_islands)}, "
                f"consumption-unanchored="
                f"{len(self.consumption_unanchored)}); "
                f"dangling={len(self.dangling_edges)}, "
                f"degree-0={len(self.degree_zero)}, stray derived "
                f"components={len(self.stray_derived_components)}, "
                f"unmapped edge types={len(self.unmapped_edge_types)}")


def analyze(nodes_rows: "list[dict]",
            edges_rows: "list[dict]") -> Topology:
    t = Topology(node_count=len(nodes_rows),
                 edge_count=len(edges_rows))
    layer_of = {str(n["node_id"]): str(n.get("layer") or "")
                for n in nodes_rows}
    ids = set(layer_of)

    # G2-referential + provenance totality
    known_types = {e.value for e in EdgeType}
    mapped_types = {e.value for e in EDGE_PROVENANCE}
    seen_unmapped: "set[str]" = set()
    parent: "dict[str, str]" = {i: i for i in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    touched: "set[str]" = set()
    for e in edges_rows:
        s, d = str(e["source_id"]), str(e["target_id"])
        et = str(e.get("edge_type") or "")
        if s not in ids or d not in ids:
            t.dangling_edges.append((s, d, et))
            continue
        if et not in mapped_types:
            if et not in seen_unmapped:
                seen_unmapped.add(et)
                label = et if et in known_types else f"UNKNOWN:{et}"
                t.unmapped_edge_types.append(label)
        union(s, d)
        touched.add(s)
        touched.add(d)

    for nid in sorted(ids - touched):
        reason = DEGREE_ZERO_EXCLUSIONS.get(nid)
        if reason:
            t.excluded_degree_zero[nid] = reason
        else:
            t.degree_zero.append(nid)

    comps: "dict[str, list[str]]" = {}
    for nid in ids:
        if nid in DEGREE_ZERO_EXCLUSIONS and nid not in touched:
            continue
        comps.setdefault(find(nid), []).append(nid)
    t.components = len(comps)

    derived_comps = []
    for members in comps.values():
        derived_in = {layer_of[m] for m in members} & DERIVED_LAYERS
        if not derived_in:
            # all-foundation: legitimate under the exception —
            # enumerated for visibility, never a finding
            t.foundation_islands.append(sorted(members)[:10])
        elif derived_in <= {"report", "measure"}:
            # consumption-only: a semantic model whose anchor tables
            # are outside the dictionary — typed isolation, not a
            # finding (enumerated; joins the principal when its
            # tables are dictionary-tracked)
            t.consumption_unanchored.append(sorted(members)[:10])
        else:
            derived_comps.append(sorted(members))
    derived_comps.sort(key=len, reverse=True)
    if derived_comps:
        t.principal_size = len(derived_comps[0])
        # G1: exactly ONE principal derived component
        t.stray_derived_components = [c[:10] for c in derived_comps[1:]]
    return t
