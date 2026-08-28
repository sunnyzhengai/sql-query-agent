"""The boundary echo contract's teeth (ordered 2026-08-27).

Totality: every declared boundary module carries at least one row;
every row's op resolves to a real function. Fidelity: a row claiming
a witness names implementation text the source must contain (the
reachability pattern applied to side effects). Exemptions state a
real reason.

Proves: contract:boundary-echo
"""

import importlib
import inspect

from devtools.boundary_ops import BOUNDARY_MODULES, BOUNDARY_OPS


def test_every_boundary_module_is_covered():
    covered = {r["module"] for r in BOUNDARY_OPS}
    assert set(BOUNDARY_MODULES) <= covered, (
        "boundary module without a single op row: "
        f"{set(BOUNDARY_MODULES) - covered}")


def test_every_row_module_is_declared():
    for r in BOUNDARY_OPS:
        assert r["module"] in BOUNDARY_MODULES, r["module"]


def test_every_op_resolves_to_a_real_function():
    for r in BOUNDARY_OPS:
        mod = importlib.import_module(r["module"])
        assert callable(getattr(mod, r["op"], None)), (
            f"{r['module']}.{r['op']} does not resolve — the "
            "registry claims an op that does not exist")


def test_witness_markers_exist_in_source():
    for r in BOUNDARY_OPS:
        marker = r["witness_marker"]
        if marker is None:
            assert "EXEMPT-WITH-REASON" in r["postcondition"] and \
                len(r["postcondition"]) >= 60, (
                f"{r['op']}: an exemption is a decision on record — "
                "state why, fully")
            continue
        mod = importlib.import_module(r["module"])
        src = inspect.getsource(getattr(mod, r["op"]))
        assert marker in src, (
            f"{r['module']}.{r['op']}: witness marker {marker!r} "
            "not in source — the row claims a postcondition the "
            "code doesn't implement")


def test_kinds_are_the_ordered_taxonomy():
    allowed = {"create", "publish", "override", "rename", "load",
               "delete"}
    for r in BOUNDARY_OPS:
        assert r["kind"] in allowed, r


def test_postconditions_are_stated_not_stubbed():
    for r in BOUNDARY_OPS:
        assert len(r["postcondition"]) >= 30, r["op"]
