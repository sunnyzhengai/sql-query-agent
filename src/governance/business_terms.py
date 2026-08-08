"""Business-term candidate mining (ADR 0031).

Deterministic, no LLM: the transformation layer is where developers
named business concepts (ADR 0019). A step name recurring across
metrics is a candidate concept; fragment hashes split it into shared
definitions vs sibling variants:

    same folded name + same fragment hash  -> ONE candidate linking all
    same folded name + different hashes    -> one candidate PER variant,
                                              grouped under a concept_key

Mined candidates enter as status=emergent, source=mined — steward
review names the variants ("X (scheduling)" vs "X (diabetes cohort)")
and accepts/rejects. Weight comes later, from endorsements + usage,
never from mining.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from src.models import NodeLayer

# Step names that are plumbing, not concepts
_NOISE_NAMES = {"final_select", "final", "finaldata", "main", "base",
                "temp", "tmp", "cte", "data", "result", "results", "output"}
_MIN_NAME_LEN = 4
_MIN_METRICS = 2  # a concept must recur across at least this many metrics


def _fold(name: str) -> str:
    return (name or "").strip().upper()


def _fragment_hash(fragment: str) -> str:
    normalized = " ".join((fragment or "").upper().split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


@dataclass
class TermCandidate:
    concept_key: str            # folded shared name
    name: str                   # display name (variant suffix left to humans)
    definition: str             # seeded from a step's generated description
    fragment_hash: str
    links: "list[dict]" = field(default_factory=list)  # gov_term_links rows
    metric_ids: "list[str]" = field(default_factory=list)

    @property
    def term_id(self) -> str:
        return hashlib.sha256(
            f"{self.concept_key}|{self.fragment_hash}".encode()
        ).hexdigest()[:16]


def mine_term_candidates(nodes_rows: "list[dict]") -> "list[TermCandidate]":
    """Cluster transformation steps into term candidates.

    Returns candidates sorted by reach (metrics touched, desc) — the
    steward reviews from the top. Sibling variants (same concept_key,
    different fragment_hash) sort adjacently.
    """
    steps: "dict[str, list[tuple[str, dict]]]" = {}  # folded name -> [(node_id, props)]
    descriptions: "dict[str, str]" = {}
    for row in nodes_rows:
        if row.get("layer") != NodeLayer.TRANSFORMATION.value:
            continue
        name = row.get("name") or ""
        folded = _fold(name)
        if len(folded) < _MIN_NAME_LEN or folded.lower().strip("_0123456789") in _NOISE_NAMES:
            continue
        props = row["properties"]
        if isinstance(props, str):
            props = json.loads(props)
        steps.setdefault(folded, []).append((row["node_id"], props))
        if row.get("description"):
            descriptions[row["node_id"]] = row["description"]

    candidates: "list[TermCandidate]" = []
    for folded, members in steps.items():
        metric_ids = {p.get("metric_id", "") for _, p in members}
        if len(metric_ids) < _MIN_METRICS:
            continue
        by_hash: "dict[str, list[tuple[str, dict]]]" = {}
        for node_id, props in members:
            by_hash.setdefault(
                _fragment_hash(props.get("sql_fragment", "")), []
            ).append((node_id, props))
        display = members[0][1].get("display_name") or members[0][0].split(":")[-1]
        for fhash, group in sorted(by_hash.items()):
            group_metrics = sorted({p.get("metric_id", "") for _, p in group})
            definition = next(
                (descriptions[nid] for nid, _ in group if nid in descriptions), ""
            )
            candidates.append(TermCandidate(
                concept_key=folded,
                name=display,
                definition=definition,
                fragment_hash=fhash,
                links=[{
                    "node_ref": nid, "node_kind": "step", "role": "defines",
                } for nid, _ in group],
                metric_ids=group_metrics,
            ))

    candidates.sort(key=lambda c: (-len(c.metric_ids), c.concept_key, c.fragment_hash))
    return candidates


def candidates_to_records(
    candidates: "list[TermCandidate]", mined_at: str = ""
) -> "tuple[list[dict], list[dict]]":
    """(gov_business_terms rows, gov_term_links rows) for steward review."""
    terms, links = [], []
    for c in candidates:
        terms.append({
            "term_id": c.term_id,
            "concept_key": c.concept_key,
            "name": c.name,
            "definition": c.definition,
            "status": "emergent",
            "steward": "",
            "source": "mined",
            "created_by": "miner",
            "created_at": mined_at,
            "updated_at": mined_at,
        })
        for link in c.links:
            links.append({
                "term_id": c.term_id,
                **link,
                "added_by": "miner",
                "added_at": mined_at,
            })
    return terms, links
