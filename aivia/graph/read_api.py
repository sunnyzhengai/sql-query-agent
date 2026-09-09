"""The Level-2-facing READ surface — the ONLY module lenses may import
(the import-law plank enforces this structurally).

Every answer carries its completeness (B3): reads are current-graph
views unless the caller explicitly asks for retired versions. The
stamp anchors consistent reads (SO3) — a lens result cites the graph
state it was computed against.
"""
from typing import Any, Dict, List, Optional, Tuple

from aivia.graph.store import Edge, NodeVersion, Store


class ReadApi:
    def __init__(self, store: Store):
        self._store = store

    def nodes(self, label: Optional[str] = None) -> List[NodeVersion]:
        return self._store.current_nodes(label)

    def edges(self, kind: Optional[str] = None) -> List[Edge]:
        return self._store.current_edges(kind)

    def read(self, identity: str,
             mode: str = "current") -> Tuple[List[NodeVersion], str]:
        return self._store.read(identity, mode)

    def trees(self) -> Dict[str, Dict[str, Any]]:
        """Current KG2 trees, keyed by file identity."""
        return {n.identity: n.properties["tree"]
                for n in self._store.current_nodes("file")}

    def stamp(self):
        return self._store.state_stamp()
