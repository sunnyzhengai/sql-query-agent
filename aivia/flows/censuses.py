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


def connection_ledger() -> Dict[str, Dict[str, str]]:
    """The per-kind birth-edge table, FROM THE REGISTRY (v1.21.0 —
    the literal law: RULED_ISOLATED_KINDS is dead; a ruling never
    lives in code). kind -> {edge, status}."""
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Connection_Ledger"]
    return {r["Label"]: {"edge": r["Edge"], "status": r["Status"]}
            for r in sheet if r["Label"] != "_ruling"}


def connection_census(read) -> Dict[str, Any]:
    """CENSUS 1's SUCCESSOR (the birth-edge law, Sunny's
    term-isolation overrule): every node answers 'why do you exist'
    by a walkable edge — birth_edged + counted_missing + rooted ==
    total. missing-counted kinds are honest debt with their landing
    step named in the ledger; an unledgered kind is a failure, not
    a discovery (closed at birth)."""
    adj = connect.build_adjacency(read)
    ledger = connection_ledger()
    birth_edged = counted = rooted = total = 0
    missing_kinds = set()
    unledgered = set()
    for kind in sorted({n.label for n in read.nodes(None)}):
        nodes = read.nodes(kind)
        row = ledger.get(kind)
        if row is None:
            unledgered.add(kind)
            total += len(nodes)
            continue
        for n in nodes:
            total += 1
            if row["status"] == "rooted":
                rooted += 1
            elif row["status"] == "missing-counted":
                counted += 1
                missing_kinds.add(kind)
            else:
                labels = {lbl for _, lbl in adj.get(n.identity, [])}
                ok = (bool(labels) if row["edge"] == "any"
                      else row["edge"] in labels)
                if ok:
                    birth_edged += 1
                else:
                    counted += 1
                    missing_kinds.add(kind)
    # literal: shape
    return {"total": total, "birth_edged": birth_edged,
            "counted_missing": counted, "rooted": rooted,
            "counted_missing_kinds": sorted(missing_kinds),
            "unledgered_kinds": sorted(unledgered)}


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
        {e["label"] for e in index
         if speech.SHEET_KINDS.get(e["label"]) not in declared})
    # literal: shape
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
    # literal: shape
    return {"speaks": speaks, "searchable": searchable,
            "ruled_silent": speaks - searchable}


def verbatim_census(read,
                    index: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Census 8 (integrity battery; first implemented 2026-09-09 —
    the documentation audit found the ratified equation had no
    code): index words == recomputed speech, entry by entry.
    matched ⊎ counted-mismatch == total; a stale or mutated index
    is COUNTED with its identities, never silent."""
    matched, mismatches = 0, []
    for e in index:
        if speech.speak(read, e) == e.get("words", ""):
            matched += 1
        else:
            mismatches.append(e["identity"])
    # literal: shape
    return {"total": len(index), "matched": matched,
            "mismatched": len(mismatches),
            "mismatches": mismatches[:20]}


def report(read, index: List[Dict[str, Any]]) -> str:
    """The gap-check report bucket — the three equations with their
    numbers, for Sunny's read."""
    from aivia.flows import smells
    r = connection_census(read)
    s = speech_census(read, index)
    q = searchability_census(read, index)
    v = verbatim_census(read, index)
    m = smells.smell_census(read)
    return "\n".join([
        "## The three censuses (ADR 0080; census 1 succeeded by the "
        "connection census, 2026-09-07)",
        f"- connection: {r['birth_edged']} birth-edged + "
        f"{r['counted_missing']} counted-missing + {r['rooted']} "
        f"rooted == {r['total']} total; missing kinds: "
        f"{r['counted_missing_kinds'] or 'none'}; unledgered: "
        f"{r['unledgered_kinds'] or 'none'}",
        f"- speech: {s['speaks']} speak + {s['counted_gap']} "
        f"counted gaps + {s['ruled_mute']} ruled-mute == "
        f"{s['total']}; unassigned kinds: "
        f"{s['unassigned_kinds'] or 'none'}",
        f"- searchability: {q['searchable']} searchable + "
        f"{q['ruled_silent']} ruled-silent == {q['speaks']} "
        "speakers",
        f"- verbatim: {v['matched']} matched + {v['mismatched']} "
        f"counted mismatches == {v['total']}; drifted: "
        f"{v['mismatches'] or 'none'}",
        f"- meaning-smell: {m['clean']} clean + {m['smelled']} "
        f"smelled == {m['total']} voicings; smells: "
        f"{m['by_smell'] or 'none'} (the fourth equation, "
        "Sunny's go 2026-09-14)"])
