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

from aivia.graph import kg3_artifacts
from aivia.graph.read_api import ReadApi

SCRIBE_AUTHOR = "agent:scribe"
DESCRIBED_LABELS = ("file", "PBI Report")


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
    """The node's OWN anatomy, for the Scribe to distill — the
    structural voicing (files) or the shell description + displays
    (PBI). Evidence, never copy-source: the contract bans landing
    it verbatim as speech."""
    from aivia.flows import speech as speech_mod
    node = next((n for n in read.nodes(None)
                 if n.identity == identity), None)
    if node is None:
        return ""
    if node.label == "PBI Report":
        return " ".join([
            node.properties.get("name") or "",
            node.properties.get("description") or "",
            "displays: " + ", ".join(
                node.properties.get("displays") or [])]).strip()
    name = node.properties.get("name") or identity
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
         created_at: str) -> int:
    """Drafts become kg3 description artifacts: machine author,
    status 'drafted', basis mandatory (the witness chain)."""
    n = 0
    for identity, text in sorted(drafts.items()):
        kg3_artifacts.append_description(
            store, f"description::{identity}", [identity], text,
            status="drafted", author=SCRIBE_AUTHOR, basis=basis,
            created_at=created_at)
        n += 1
    return n
