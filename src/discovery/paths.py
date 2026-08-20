"""Path enumeration over the technical join map — spec:E1.

    G_tech finite ∧ static ⟹ Paths_k(A) is finite and mechanically
    enumerable, for any anchor set A.

Paths between anchored tables are FACTS waiting to be enumerated — a
search problem, never a synthesis problem (ADR 0046, Sunny's position:
"when you know nodes, you know the path"). Direction is preserved in
the hop record because direction is meaning (Encounter→Referral ≠
Referral→Encounter); the walk itself may cross an edge either way —
both orientations are real, both are candidates, the human picks.

Replay-deterministic by construction (spec:E2): sorted adjacency,
sorted output, no clocks, no randomness.
"""

from __future__ import annotations

from src.parser.identity import fold_identifier

# a hop: (from_table, from_column, to_table, to_column)
Hop = tuple
Path = tuple


def _adjacency(joinable: "list[tuple]") -> "dict[str, list[Hop]]":
    adj: "dict[str, list[Hop]]" = {}
    for src_t, src_c, dst_t, dst_c in joinable:
        a = (fold_identifier(src_t), fold_identifier(src_c),
             fold_identifier(dst_t), fold_identifier(dst_c))
        b = (a[2], a[3], a[0], a[1])  # the mirror orientation
        adj.setdefault(a[0], []).append(a)
        adj.setdefault(b[0], []).append(b)
    for hops in adj.values():
        hops.sort()
    return adj


def enumerate_paths(anchors: "set[str]", joinable: "list[tuple]",
                    max_hops: int = 4) -> "list[Path]":
    """All simple paths (≤ max_hops) connecting each pair of anchors.

    Returns a sorted list of paths; each path is a tuple of hops. The
    caller (the 0046 engine) ranks by corpus evidence — enumeration
    PRESENTS, it never prunes beyond the stated hop cap.
    """
    adj = _adjacency(joinable)
    anchor_list = sorted(fold_identifier(a) for a in anchors)
    results: "set[Path]" = set()

    def walk(current: str, target: str, visited: "tuple[str, ...]",
             path: "tuple[Hop, ...]") -> None:
        if len(path) > max_hops:
            return
        if current == target and path:
            results.add(path)
            return
        for hop in adj.get(current, []):
            nxt = hop[2]
            if nxt in visited:
                continue
            walk(nxt, target, visited + (nxt,), path + (hop,))

    for i, a in enumerate(anchor_list):
        for b in anchor_list[i + 1:]:
            walk(a, b, (a,), ())
    return sorted(results)
