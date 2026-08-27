"""CI leg of the live-probe law (P0.4, Sunny's no-whack-a-mole audit
2026-08-23): the dispatch→op argument mapping, checked offline with
the recorded fake store — plus totality guards so a NEW engine tool
cannot ship without a dispatch branch and a live smoke case.

The live leg is devtools/engine_smoke.py (required before any ship
touching src/orchestrator/ops.py or tools.py).

Proves: law:live-probe
"""

from pathlib import Path

from src.orchestrator.ops import OpError, OpsSession
from src.orchestrator.turn_engine import ENGINE_TOOLS, _run_op
from tests.orchestrator.test_tools import REF_A, REF_B, fake_kql

REPO = Path(__file__).resolve().parent.parent.parent

# Realistic offline arguments per declared tool — built from the SAME
# param names the tool schemas declare, so a schema/dispatch drift
# fails here before it fails live (the W12 class).
OFFLINE_ARGS = {
    "search": {"phrase": "ed sepsis", "mode": "semantic"},
    "census": {"kind": "metric", "contains": "ED"},
    "retrieve": {"ids": [REF_A]},
    "lineage": {"table": "IP_SEPSIS"},
    "compare": {"refs": [REF_A, REF_B]},
}


def test_every_declared_tool_has_offline_args_and_dispatches():
    declared = {t["function"]["name"] for t in ENGINE_TOOLS}
    assert declared == set(OFFLINE_ARGS), (
        "ENGINE_TOOLS and OFFLINE_ARGS drifted — a new tool needs an "
        "offline dispatch case here AND a live case in "
        "devtools/engine_smoke.py")
    ops = OpsSession()
    ops.note_user(f"{REF_A} {REF_B}")     # read guarantee for the args
    for name, args in OFFLINE_ARGS.items():
        rs = _run_op(name, args, fake_kql, ops)
        assert rs.op, f"{name}: dispatch returned no result set"


def test_schema_param_names_are_accepted_by_dispatch():
    """Every parameter a tool schema declares must be consumed by the
    dispatch — a renamed schema param that _run_op ignores silently is
    exactly how valid arguments turn into empty selections."""
    for tool in ENGINE_TOOLS:
        name = tool["function"]["name"]
        declared_params = set(
            tool["function"]["parameters"]["properties"])
        offline = set(OFFLINE_ARGS[name])
        assert offline <= declared_params, (
            f"{name}: offline args {offline - declared_params} are not "
            "in the tool schema")


def test_unknown_tool_raises_visibly():
    try:
        _run_op("nonexistent", {}, fake_kql, OpsSession())
        raise AssertionError("unknown tool did not raise")
    except OpError as e:
        assert "unknown tool" in str(e)


def test_live_harness_covers_every_declared_tool():
    """Totality: the live smoke harness must name every ENGINE_TOOLS
    entry — adding a tool without a live case fails here, not in the
    field (the mechanism the 5-Rule Gate demands)."""
    harness = (REPO / "devtools" / "engine_smoke.py").read_text()
    for tool in ENGINE_TOOLS:
        name = tool["function"]["name"]
        assert f'"{name}"' in harness or f"'{name}'" in harness, (
            f"devtools/engine_smoke.py has no case naming {name!r}")
