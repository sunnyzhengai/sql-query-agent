"""The append-only substrate (Level 1's storage primitive).

One law: there is no update and no delete. Supersede = append new
version + retire prior (valid_to set, never removed); retire = mark.
Reads declare their completeness; current-vs-including-retired is an
explicit parameter, never a default surprise (LC-D1).

Callable ONLY by lifecycle modules + read_api — enforced structurally
by tests/aivia/test_planks.py, not by convention. In-memory in slice 1;
the platform adapter arrives behind this same interface.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

READ_MODES = ("current", "all")


@dataclass
class NodeVersion:
    label: str
    identity: str
    properties: Dict[str, Any]
    as_of: str
    extract_id: str
    valid_to: Optional[str] = None


@dataclass
class Edge:
    label: str
    from_id: str
    to_id: str
    properties: Dict[str, Any]
    as_of: str
    extract_id: str
    valid_to: Optional[str] = None


@dataclass
class Store:
    _nodes: List[NodeVersion] = field(default_factory=list)
    _edges: List[Edge] = field(default_factory=list)
    _seq: int = 0
    # PHASE E1 (Sunny's ruling: all user decisions persist): the
    # governance journal — writes whose extract_id belongs to the
    # kg3@ family (human acts, minted actors, blessed vocabulary)
    # append a line here; builders (sources) never journal.
    journal_path: Optional[Any] = None
    _replaying: bool = False

    def append_node(self, label: str, identity: str,
                    properties: Dict[str, Any], as_of: str,
                    extract_id: str) -> NodeVersion:
        for prior in self._nodes:
            if prior.identity == identity and prior.valid_to is None:
                prior.valid_to = as_of  # supersede: retire, never remove
        version = NodeVersion(label, identity, dict(properties),
                              as_of, extract_id)
        self._nodes.append(version)
        if (self.journal_path is not None and not self._replaying
                and extract_id.startswith("kg3@")):
            import json as _json
            with open(self.journal_path, "a") as fh:
                fh.write(_json.dumps(
                    {"label": label, "identity": identity,
                     "properties": properties, "as_of": as_of,
                     "extract_id": extract_id}) + "\n")
        self._seq += 1
        return version

    def retire_node(self, identity: str, valid_to: str) -> None:
        for version in self._nodes:
            if version.identity == identity and version.valid_to is None:
                version.valid_to = valid_to
                self._seq += 1

    def append_edge(self, label: str, from_id: str, to_id: str,
                    properties: Dict[str, Any], as_of: str,
                    extract_id: str) -> Edge:
        edge = Edge(label, from_id, to_id, dict(properties),
                    as_of, extract_id)
        self._edges.append(edge)
        self._seq += 1
        return edge

    def retire_edge(self, edge: Edge, valid_to: str) -> None:
        edge.valid_to = valid_to
        self._seq += 1

    def read(self, identity: str,
             mode: str = "current") -> Tuple[List[NodeVersion], str]:
        if mode not in READ_MODES:
            raise ValueError(
                f"read mode must be one of {READ_MODES}, got '{mode}' — "
                "completeness is explicit, never a default surprise (LC-D1)")
        versions = [v for v in self._nodes if v.identity == identity]
        if mode == "current":
            return [v for v in versions if v.valid_to is None], "current"
        return versions, "including_retired"

    def current_nodes(self, label: Optional[str] = None) -> List[NodeVersion]:
        return [v for v in self._nodes if v.valid_to is None
                and (label is None or v.label == label)]

    def current_edges(self, label: Optional[str] = None) -> List[Edge]:
        return [e for e in self._edges if e.valid_to is None
                and (label is None or e.label == label)]

    def replay_journal(self) -> int:
        """Replay the governance journal into this store — the
        rebirth of every human decision. Idempotent by supersession
        (same identity re-appends supersede the prior)."""
        if self.journal_path is None:
            return 0
        import json as _json
        import pathlib as _pl
        path = _pl.Path(self.journal_path)
        if not path.is_file():
            return 0
        self._replaying = True
        n = 0
        try:
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                row = _json.loads(line)
                self.append_node(row["label"], row["identity"],
                                 row["properties"], row["as_of"],
                                 row["extract_id"])
                n += 1
        finally:
            self._replaying = False
        return n

    def state_stamp(self) -> Tuple[int, int, int]:
        return (self._seq, len(self._nodes), len(self._edges))
