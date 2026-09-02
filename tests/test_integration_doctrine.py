"""Connector doctrine closure checks (ADR 0069, ratchet turn 3).

SOURCE_CONNECTORS.md retired into the integration registry: the
configurations became rows, the change/identity doctrine became data.
These checks keep the absorbed content honest.

Proves: spec:E3, spec:L3
"""

from __future__ import annotations

from src.integration_registry import (
    CHANGE_TRIGGERS,
    IDENTITY_LADDER,
    INTEGRATION_REGISTRY,
    NATIVE_STABLE_IDS,
)


def test_ladder_steps_are_typed_per_the_decision_typing_rule():
    """spec:E3 — computable steps belong to code, judgment steps to
    the steward. A ladder step outside the closed set is an untyped
    decision, the exact thing 0035's taxonomy forbids."""
    bad = [(name, kind) for name, kind, _ in IDENTITY_LADDER
           if kind not in ("computable", "judgment")]
    assert not bad, f"untyped ladder step(s): {bad}"
    kinds = [k for _, k, _ in IDENTITY_LADDER]
    assert "judgment" in kinds, (
        "the ladder lost its steward step — fuzzy rename mapping must "
        "never auto-merge (Sunny's 2026-08-11 ruling)")


def test_every_non_shipped_ingest_row_states_its_roadmap_note():
    """A planned/watchlist source with no note is a silent roadmap
    entry — the spec:C1 exclusion-row discipline applied to
    connectors: deliberate absence carries its reason."""
    silent = [r["from_tool"] for r in INTEGRATION_REGISTRY
              if r["direction"] == "ingest" and r["status"] != "shipped"
              and not r.get("notes", "").strip()]
    assert not silent, f"unexplained roadmap row(s): {silent}"


def test_no_mechanism_names_a_banned_parser():
    """ADR 0001 is total: sqlglot/sqlparse may not appear as a
    PLANNED mechanism (historical notes naming the ban are fine)."""
    bad = [r["from_tool"] for r in INTEGRATION_REGISTRY
           if "sqlglot" in r["mechanism"]
           and "banned" not in r["mechanism"]]
    assert not bad, (
        f"row(s) still plan a banned parser: {bad} — each dialect "
        f"gets its own native parser (spec:G2)")


def test_doctrine_blocks_are_complete():
    assert len(CHANGE_TRIGGERS) == 3, "the three triggers are ruled"
    assert len(NATIVE_STABLE_IDS) >= 5
    for src_, flag, use in NATIVE_STABLE_IDS:
        assert use.strip(), f"{src_}: no use note"
        assert flag in (True, False, None)
