"""KG layer 4 — the concept layer. The lens computes; a human touch
mints. Sparse by design.

CHECK-KG4-1: every concept's minting act traces to a HUMAN ruling or
acceptance — no machine mint path exists. Ids are content-keyed at
minting; basis holds the family snapshot (member tree versions + lens
version). Membership is NEVER stored — the relatedness lens recomputes
(CHECK-KG4-3: no member edges exist); basis-vs-now divergence is the
deferred concept-drift lens's whole job. Append-only (CHECK-KG4-2):
no edit or delete path exists in this module.
"""
import hashlib
import json
from typing import Any, Dict

from aisql.graph.kg3_artifacts import is_machine
from aisql.graph.store import NodeVersion, Store


class RefusalKG4(Exception):
    def __init__(self, rule: str, message: str):
        self.rule = rule
        super().__init__(f"{rule}: {message}")


def mint(store: Store, family_snapshot: Dict[str, Any], minting_act: str,
         created_at: str) -> NodeVersion:
    acts, _ = store.read(minting_act, mode="all")
    if not acts:
        raise RefusalKG4("CHECK-KG4-1", f"minting act '{minting_act}' does "
                         "not exist — a concept traces to a recorded act")
    act = acts[-1]
    if is_machine(act.properties.get("author", "agent:unknown")):
        raise RefusalKG4("CHECK-KG4-1", "the minting act is machine-"
                         "authored — a human touch mints, no machine "
                         "mint path exists")
    key = hashlib.sha1(json.dumps(family_snapshot,
                                  sort_keys=True).encode()).hexdigest()[:12]
    concept_id = f"concept:{key}"
    if any(n.identity == concept_id for n in store.current_nodes("concept")):
        raise RefusalKG4("CHECK-KG4-2", f"{concept_id} already minted — "
                         "append-only, and the id is content-keyed")
    return store.append_node("concept", concept_id,
                             # literal: shape
                             {"basis": dict(family_snapshot),
                              "minting_act": minting_act,
                              "created_at": created_at},
                             created_at, f"kg4@{created_at}")
