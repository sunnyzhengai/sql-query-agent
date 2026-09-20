"""Outward stage 2: APPROVE — the human surface's write path.

One stage rule (APPR-1): this surface WRITES DISPOSITIONS ONLY — it
renders lenses, never touches artifacts, trees, or the technical
layer. Everything shown is a lens reading; everything written goes
through kg3's disposition door, which itself refuses agent authors
(LC3-C3) — human sovereignty enforced twice, structurally.
"""
from typing import Any, Dict, Optional

from aisql.graph import kg3_artifacts
from aisql.lenses import derivation


def queue(read) -> Dict[str, Any]:
    """The review queue IS a lens rendering: pending artifacts with
    their current version and derived states. Read side only."""
    standing = derivation.lens_standing(read, None)["yield"]
    current = derivation.lens_current(read, None)["yield"]
    ownership = derivation.lens_ownership(read, None)["yield"]
    # literal: shape
    return {"pending": {aid: {"current": current[aid],
                              "ownership": ownership[aid]}
                        for aid, s in standing.items() if s == "pending"},
            "completeness": "total over artifacts",
            "stamp": read.stamp()}


def rule(store, about: str, ruling: str, author: str, occurred_at: str,
         reason: Optional[str] = None):
    """The ONE write this surface owns."""
    return kg3_artifacts.append_disposition(
        store, about=about, ruling=ruling, author=author,
        occurred_at=occurred_at, reason=reason)
