"""PHASE I — the
enrichment pipeline: SCAN (mechanical: the estate's distinct name
tokens) -> SCRIBE (the curation seat proposes expansions — a model,
injected; proposals only) -> BLESS (a human approves; acronym nodes
are born). The live run is gated on Sunny's blessing; everything
here is deterministic machinery around the injected seat.
"""
from typing import Callable, Dict, List

from aivia.graph import kg3_artifacts
from aivia.lenses.ask_index import _tokens


def scan_name_tokens(read) -> List[str]:
    """Every distinct token the estate's names are made of — no
    judgment, no acronym-detection heuristics."""
    toks = set()
    for n in read.nodes(None):
        nm = n.properties.get("name") or n.identity.rsplit("|", 1)[-1]
        toks |= _tokens(str(nm))
    return sorted(toks)


def propose(tokens: List[str],
            scribe: Callable[[List[str]], Dict[str, List[str]]]
            ) -> Dict[str, List[str]]:
    """The Scribe reads the token list and proposes expansions for
    the shorthand it recognizes. PROPOSALS ONLY — nothing lands
    until a human blesses."""
    raw = scribe(tokens) or {}
    return {t.lower(): [e.strip() for e in exps if (e or "").strip()]
            for t, exps in raw.items()
            if t.lower() in {x.lower() for x in tokens}
            and exps}


def bless(store, proposals: Dict[str, List[str]],
          approved_by: str, approved_at: str) -> int:
    """The human act: approved proposals become acronym nodes."""
    n = 0
    for name, exps in sorted(proposals.items()):
        kg3_artifacts.append_acronym(store, name, exps,
                                     approved_by=approved_by,
                                     approved_at=approved_at)
        n += 1
    return n
