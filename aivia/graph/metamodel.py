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
