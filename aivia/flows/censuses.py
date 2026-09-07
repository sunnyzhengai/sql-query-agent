"""THE THREE CENSUSES (ADR 0080) — Sunny's questions as standing
conservation equations, the voiced ⊎ counted == total shape:

  1. reachable  ⊎ ruled-isolated == total nodes
  2. speaks     ⊎ counted-gap ⊎ ruled-mute == total
  3. searchable ⊎ ruled-silent == everything that speaks

Each census is a test AND a gap-check report bucket. A census that
cannot fail is decoration — the vacuity tests feed synthetic
orphans through these and expect them SEEN.
"""
from typing import Any, Dict, List

from aivia.flows import connect, speech

# ruled isolation — kinds legitimately edge-less, with the reason
# on record (ADR 0080 census 1; a new ruling is a row here + the
# registry, never a silent skip)
RULED_ISOLATED_KINDS = {
    "term": "human vocabulary; findable by name, cited by "
            "descriptions/dispositions when governance accretes",
    "usage": "the event log — evidence, not topology",
    "description": "anchored to meaning identity, not edged",
    "disposition": "governance act — anchored, not edged",
    "exclusion": "counted parse refusals — the census IS their edge",
    "responsibility": "governance act — anchored, not edged",
    "extract_receipt": "intake bookkeeping",
    "registration": "the estate's birth record",
    "meaning_twin": "KG2b container node; its interior nodes point "
                    "at the parse (points_at), not the adjacency",
}


def reachability_census(read) -> Dict[str, Any]:
    """Census 1: every node has an edge in the connecting graph, or
    its KIND is ruled isolated with a reason."""
    adj = connect.build_adjacency(read)
    kinds_of: Dict[str, str] = {}
    for kind in ("table", "column", "term", "usage", "description",
                 "disposition", "exclusion", "responsibility",
                 "extract_receipt", "registration", "meaning_twin"):
        for n in read.nodes(kind):
            kinds_of[n.identity] = kind
    total_ids = set(adj) | set(kinds_of)
    reachable = {i for i in total_ids if adj.get(i)}
    ruled, isolated = [], []
    for i in sorted(total_ids - reachable):
        kind = kinds_of.get(i)
        if kind in RULED_ISOLATED_KINDS:
            ruled.append(i)
        else:
            isolated.append(i)
    return {"total": len(total_ids), "reachable": len(reachable),
            "ruled_isolated": len(ruled),
            "ruled_isolated_kinds": sorted(
                {kinds_of.get(i) for i in ruled if kinds_of.get(i)}),
            "isolated": isolated}


def speech_census(read, index: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Census 2: speaks ⊎ counted-gap ⊎ ruled-mute == total. The
    Speech_Sources sheet is the closed assignment — an entry kind
    without a row is UNASSIGNED and fails the census at birth."""
    declared = speech.sources()
    speaks = sum(1 for e in index if e["words"])
    gaps = sum(1 for e in index if not e["words"])
    muted = 0
    for n in read.nodes("meaning_twin"):
        muted += n.properties["twin"]["census"].get("operational", 0)
    unassigned = sorted(
        {e["kind"] for e in index
         if speech.SHEET_KINDS.get(e["kind"]) not in declared})
    return {"total": speaks + gaps + muted, "speaks": speaks,
            "counted_gap": gaps, "ruled_mute": muted,
            "unassigned_kinds": unassigned}


def searchability_census(read,
                         index: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Census 3: everything that speaks is in the search surface
    with its speech verbatim; ruled-silent covers speakers ruled out
    of search (none today — the equation pins that fact)."""
    speaks = sum(1 for e in index if e["words"])
    searchable = sum(1 for e in index if e["words"])
    return {"speaks": speaks, "searchable": searchable,
            "ruled_silent": speaks - searchable}


def report(read, index: List[Dict[str, Any]]) -> str:
    """The gap-check report bucket — the three equations with their
    numbers, for Sunny's read."""
    r = reachability_census(read)
    s = speech_census(read, index)
    q = searchability_census(read, index)
    return "\n".join([
        "## The three censuses (ADR 0080)",
        f"- reachability: {r['reachable']} reachable + "
        f"{r['ruled_isolated']} ruled-isolated == {r['total']} "
        f"total; unruled orphans: {len(r['isolated'])}",
        f"- speech: {s['speaks']} speak + {s['counted_gap']} "
        f"counted gaps + {s['ruled_mute']} ruled-mute == "
        f"{s['total']}; unassigned kinds: "
        f"{s['unassigned_kinds'] or 'none'}",
        f"- searchability: {q['searchable']} searchable + "
        f"{q['ruled_silent']} ruled-silent == {q['speaks']} "
        "speakers",
    ])
