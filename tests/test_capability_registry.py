"""Mechanism uniqueness (spec:G1–G3) — Uses ∖ S = ∅ over src/.

Every (module, powerful-primitive) pair actually present in the code
must be sanctioned by exactly the CAPABILITY_REGISTRY. A new module
importing requests, or anything importing a banned parser, fails here
with the registry named — the pressure moment becomes a registry review
instead of a silent second implementation."""

import ast
from pathlib import Path

from src.capability_registry import CAPABILITY_REGISTRY, POWER_PRIMS

REPO = Path(__file__).parent.parent


def _uses():
    out = []
    for py in sorted((REPO / "src").rglob("*.py")):
        if "__pycache__" in str(py):
            continue
        roots = set()
        for node in ast.walk(ast.parse(py.read_text())):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 \
                    and node.module:
                roots.add(node.module.split(".")[0])
        for prim in roots & set(POWER_PRIMS):
            out.append((str(py.relative_to(REPO)), prim))
    return out


def _sanctioned(module: str, prim: str) -> bool:
    for cap in CAPABILITY_REGISTRY.values():
        if prim in cap["prims"] and module.startswith(cap["owner"]):
            return True
    return False


def test_g2_sanctioned_powers_only():
    """spec:G2 — Uses ∖ S = ∅."""
    offenders = [(m, p) for m, p in _uses() if not _sanctioned(m, p)]
    assert not offenders, (
        f"unsanctioned powerful imports {offenders} — either the module "
        f"moves under an owning capability, or a new CAPABILITY_REGISTRY "
        f"row is added (the row IS the review; spec:G2)"
    )


def test_g1_one_owner_per_capability():
    """spec:G1 — own is a function: every row names exactly one owner
    prefix that exists on disk."""
    for name, cap in CAPABILITY_REGISTRY.items():
        owner = cap["owner"]
        assert isinstance(owner, str) and owner.startswith("src/"), name
        assert (REPO / owner).exists(), f"{name}: owner {owner} missing"
        assert cap["prims"], f"{name}: a capability with no primitives"
        assert cap.get("why", "").strip(), f"{name}: undocumented capability"


def test_g3_banned_parsers_have_no_owner():
    """spec:G3 corollary + ADR 0001 total law: sqlglot/sqlparse are
    powerful primitives that NO capability may sanction."""
    for cap_name, cap in CAPABILITY_REGISTRY.items():
        for banned in ("sqlglot", "sqlparse"):
            assert banned not in cap["prims"], (
                f"{cap_name} sanctions {banned} — banned under ADR 0001; "
                f"no registry row may ever grant it"
            )


def test_owners_actually_use_their_powers():
    """The reverse direction: a capability whose owner never imports its
    primitive is stale registry data."""
    uses = set(_uses())
    for name, cap in CAPABILITY_REGISTRY.items():
        for prim in cap["prims"]:
            if prim == "clr":
                continue  # loaded dynamically inside functions by design
            assert any(m.startswith(cap["owner"]) and p == prim
                       for m, p in uses), (
                f"{name}: owner {cap['owner']} never imports {prim} — "
                f"stale row, remove or fix"
            )
