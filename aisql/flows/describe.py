"""E1 — THE SCRIBE'S DESCRIPTION PIPELINE (the speech contract,
Design_Graph_Engine.md; route ruled 2026-09-09: Scribe-drafted
aboutness). SCAN what lacks its own description → the Scribe
DISTILLS one aboutness sentence from the node's structural evidence
(a model, injected — proposals only) → LAND as kg3 description
artifacts, machine-authored, status 'drafted', basis-stamped. The
live run commits its drafts as estate data (descriptions.json) so
every boot — test or prod — speaks the same aboutness; blessing is
a later human act.
"""
from typing import Callable, Dict, List

from aisql.graph import kg3_artifacts
from aisql.graph.read_api import ReadApi

SCRIBE_AUTHOR = "agent:scribe"
# Sunny's ruling (2026-09-09): reports DERIVE their description from
# their procs through the executes edge — "the report users SHOULD
# see the logic"; the Scribe drafts for the logic only
DESCRIBED_LABELS = ("file",)


def _described(read: ReadApi) -> set:
    out = set()
    for n in read.nodes("description"):
        out |= set(n.properties.get("about") or [])
    return out


def scan_undescribed(read: ReadApi) -> List[str]:
    """Every file / PBI report with no description artifact of its
    own — the aboutness debt, mechanically."""
    have = _described(read)
    out = []
    for label in DESCRIBED_LABELS:
        for n in read.nodes(label):
            if n.identity not in have:
                out.append(n.identity)
    return sorted(out)


def evidence(read: ReadApi, identity: str) -> str:
    """The node's OWN anatomy, for the Scribe to distill.
    Evidence, never copy-source: the contract bans landing it
    verbatim as speech. M6 (the two-field design, Sunny's chain
    "we summarize this technical definition using LLM"): when the
    node carries the R13 catch-all, THAT is the one evidence —
    already true, already population-focused; the old anatomy/
    shell evidence (catalog recitation) retires behind it."""
    from aisql.flows import speech as speech_mod
    node = next((n for n in read.nodes(None)
                 if n.identity == identity), None)
    if node is None:
        return ""
    name = node.properties.get("name") or identity
    td = node.properties.get("technical_definition")
    if td:
        return f"{name}. {td}"
    return f"{name}. {speech_mod._file_voicing(read, identity)}"


def draft(read: ReadApi,
          targets: List[str],
          scribe: Callable[[Dict[str, str]], Dict[str, str]]
          ) -> Dict[str, str]:
    """The Scribe reads {identity: evidence} and returns
    {identity: aboutness sentence}. PROPOSALS ONLY — empty or
    unknown identities are dropped, never invented."""
    ev = {t: evidence(read, t) for t in targets}
    raw = scribe(ev) or {}
    return {i: (txt or "").strip() for i, txt in raw.items()
            if i in ev and (txt or "").strip()}


def land(store, drafts: Dict[str, str], basis: Dict[str, str],
         created_at: str, status: str = "drafted") -> int:
    """Drafts become kg3 description artifacts: machine author,
    basis mandatory (the witness chain). Status defaults
    'drafted'; 'approved' rides ONLY when the estate file records
    Sunny's approval act (M6 — the blessed_subjects precedent:
    his act as estate data, every boot speaks it)."""
    n = 0
    for identity, text in sorted(drafts.items()):
        kg3_artifacts.append_description(
            store, f"description::{identity}", [identity], text,
            status=status, author=SCRIBE_AUTHOR, basis=basis,
            created_at=created_at)
        n += 1
    return n
