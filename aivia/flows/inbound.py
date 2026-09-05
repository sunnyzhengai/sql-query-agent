"""The extract door — inbound stage for registered dictionary extracts.

Thin by design: validation and lifecycle live in kg1_intake (the
layer's one writer); this flow sequences validate-then-apply and
returns the intake report. The estate door (SQL files -> kg2_mapper)
arrives with slice 2.
"""
from typing import Any, Dict, Set

from aivia.graph import kg1_intake


def receive_extract(store, reg: Dict[str, Any],
                    snap: "kg1_intake.ExtractSnapshot",
                    known_packs: Set[str]) -> "kg1_intake.IntakeReport":
    kg1_intake.validate_extract(reg, snap, known_packs)
    return kg1_intake.apply_extract(store, reg, snap)
