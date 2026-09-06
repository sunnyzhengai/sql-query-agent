"""The registry loader — the only door between design data and code.

Loads the ratified registries from AIVIA_Design/registries/ and refuses
anything unratified: a draft registry cannot feed a build. Code and
tests consume these loaded registries, never the design doc's prose
(Design-to-Code protocol step 2; binding mechanism a).

The validate side (metamodel conformance over graph nodes/edges,
CHECK-TL-4 / CHECK-KG2-7 / CHECK-KG3-7 / CHECK-KG4-3) arrives with
slice 1 — this module ships load-only in slice 0.
"""
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List

REGISTRY_DIR = (pathlib.Path(__file__).resolve().parents[2]
                / "AIVIA_Design" / "registries")
REGISTRY_NAMES = ("kg1_technical", "kg2_kind_library", "kg2_logic",
                  "kg3_artifacts", "kg4_concepts", "lenses", "flows")


class UnknownRegistryError(KeyError):
    """Named registry is not one of the seven."""


class UnratifiedRegistryError(RuntimeError):
    """Registry exists but its stamp says ratified is not true."""


@dataclass(frozen=True)
class Registry:
    name: str
    version: str
    doc_section: str
    ratified: bool
    sheets: Dict[str, List[Dict[str, Any]]] = field(repr=False)


def load(name: str) -> Registry:
    if name not in REGISTRY_NAMES:
        raise UnknownRegistryError(
            f"unknown registry '{name}' — the seven are {REGISTRY_NAMES}")
    raw = json.loads((REGISTRY_DIR / f"{name}.json").read_text())
    stamp = raw["stamp"]
    if stamp.get("ratified") is not True:
        raise UnratifiedRegistryError(
            f"registry '{name}' (v{stamp.get('version')}) is not ratified — "
            "a draft registry cannot feed a build")
    return Registry(name=name, version=stamp["version"],
                    doc_section=stamp["doc_section"],
                    ratified=True, sheets=raw["sheets"])


def load_all() -> Dict[str, Registry]:
    return {name: load(name) for name in REGISTRY_NAMES}


# ---- validate side (slice 1): CHECK-TL-4 conformance ----
# Properties satisfied structurally rather than as stored fields:
# as_of rides every NodeVersion/Edge (the store's shape); source is the
# identity's FIRST component (A2 — never stored as a second field).
_STRUCTURAL = {"as_of", "source"}
_CONTAINS_DOMAIN = {("db", "schema"), ("schema", "table"),
                    ("table", "column")}


def _required_by_kind(reg: Registry) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for row in reg.sheets["Node_Types"]:
        kind = row["Node kind"]
        out.setdefault(kind, [])  # every declared kind, even all-optional
        if row.get("Required", "").startswith("yes") \
                and row["Property"] not in _STRUCTURAL:
            out[kind].append(row["Property"])
    return out


def validate_technical_layer(store) -> List[str]:
    """Every current KG1 node/edge validates against the ratified
    kg1_technical registry — kinds, required properties, edge
    endpoint domains. Returns named problems ([] = conformant)."""
    reg = load("kg1_technical")
    required = _required_by_kind(reg)
    problems = []
    kind_of: Dict[str, str] = {}
    for node in store.current_nodes():
        kind_of[node.identity] = node.kind
        if node.kind == "responsibility":
            continue  # layer 3; validated by its own registry (slice 4)
        if node.kind not in required:
            problems.append(f"unknown node kind '{node.kind}' "
                            f"({node.identity})")
            continue
        for prop in required[node.kind]:
            if node.properties.get(prop) in (None, "", []):
                problems.append(
                    f"{node.identity}: required property '{prop}' absent")
    for edge in store.current_edges("contains"):
        pair = (kind_of.get(edge.from_id), kind_of.get(edge.to_id))
        if pair not in _CONTAINS_DOMAIN:
            problems.append(f"contains {edge.from_id} -> {edge.to_id}: "
                            f"endpoint kinds {pair} outside domain")
    for edge in store.current_edges("joins_to"):
        pair = (kind_of.get(edge.from_id), kind_of.get(edge.to_id))
        if pair != ("table", "table"):
            problems.append(f"joins_to {edge.from_id} -> {edge.to_id}: "
                            f"endpoint kinds {pair}, must be table->table")
        on = edge.properties.get("on")
        if not on or any(len(pair) != 2 for pair in on):
            problems.append(f"joins_to {edge.from_id} -> {edge.to_id}: "
                            "'on' must be ordered [src, dest] pairs")
        if edge.properties.get("cardinality") != "many_to_one":
            problems.append(f"joins_to {edge.from_id} -> {edge.to_id}: "
                            "cardinality outside closed vocab")
    return problems


def validate_artifact_layer(store) -> List[str]:
    """CHECK-KG3-7: layer-3 spine + closed vocabularies. The registry's
    Classes sheet is the authority; summaries (ownership, standing,
    current) must NOT exist as stored fields (CHECK-KG3-1)."""
    from aivia.graph import kg3_artifacts as kg3
    problems = []
    for node in store.current_nodes():
        p = node.properties
        if node.kind in kg3.STATE_CLASSES:
            if not p.get("artifact_id"):
                problems.append(f"{node.identity}: no artifact_id")
            if not p.get("about"):
                problems.append(f"{node.identity}: spine incomplete (about)")
            author = str(p.get("author", ""))
            if not author:
                problems.append(f"{node.identity}: spine incomplete (author)")
            if author.startswith("agent:") and not p.get("basis"):
                problems.append(f"{node.identity}: machine version, no basis")
            for banned in ("ownership", "standing", "current", "version"):
                if banned in p:
                    problems.append(f"{node.identity}: stored summary "
                                    f"'{banned}' — the ledger law bans it")
            if node.kind == "description" and author.startswith("agent:") \
                    and p.get("status") not in kg3.DESCRIPTION_STATUS:
                problems.append(f"{node.identity}: status outside vocab")
        elif node.kind == "disposition":
            if p.get("ruling") not in kg3.RULINGS:
                problems.append(f"{node.identity}: ruling outside vocab")
            if str(p.get("author", "")).startswith("agent:"):
                problems.append(f"{node.identity}: agent disposition exists")
    return problems
