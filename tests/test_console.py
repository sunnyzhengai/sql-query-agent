"""CONSOLE-1 (0063 §3 — the Resolution Console / the Inbox):
buttons are the 0056 verbs; every verb has a landing row and every
landing has a grade — mechanized totality, the trace-registry
pattern applied to product actions.

Proves: law:walk-finds
"""

import json

import pytest

from src.console import (
    LANDING_MAP,
    ConsoleRefusal,
    action_event,
    check_action,
    effective_dispositions,
    inbox_state,
)
from tests.orchestrator.test_tools import fake_kql


class TestLandingTotality:
    """0063's two invariants, mechanical."""

    def test_every_verb_has_a_landing_and_a_grade(self):
        assert set(LANDING_MAP) == {
            "certify", "certify_official", "differentiate_all",
            "certify_definition", "deny", "delegate", "compare",
            "approve_technical", "fork"}
        for verb, row in LANDING_MAP.items():
            assert row["lands"].strip(), verb
            assert row["grade"].strip(), verb
            assert row["persona"] in ("steward", "developer", "any")

    def test_unknown_verb_refuses_with_the_law(self):
        with pytest.raises(ConsoleRefusal) as e:
            check_action("summarize", "steward")
        assert e.value.reason_class == "unknown_verb"
        assert "no action without a landing" in str(e.value)

    def test_every_action_event_is_graded(self):
        for verb, row in LANDING_MAP.items():
            persona = ("developer"
                       if row["persona"] == "developer"
                       else "steward")
            ev = action_event(verb, "cluster:x", persona, "u",
                              "because", "t0",
                              member_ids=["m1"])
            assert ev["decision"]["grade"] == row["grade"]
            assert ev["decision"]["lands"] == row["lands"]
            assert ev["question"].startswith("[CONSOLE:")


class TestPersonaAndReason:
    def test_steward_cannot_approve_technical(self):
        with pytest.raises(ConsoleRefusal) as e:
            check_action("approve_technical", "steward")
        assert e.value.reason_class == "persona"

    def test_developer_cannot_certify(self):
        with pytest.raises(ConsoleRefusal):
            check_action("certify", "developer")

    def test_deny_requires_its_reason(self):
        with pytest.raises(ConsoleRefusal) as e:
            check_action("deny", "steward", reason="  ")
        assert e.value.reason_class == "reason_required"
        check_action("deny", "steward", reason="wrong grain")

    def test_compare_is_any_persona(self):
        check_action("compare", "steward")
        check_action("compare", "developer")


class TestInboxFolding:
    def _events(self, tmp_path, events):
        p = tmp_path / "e.jsonl"
        p.write_text("\n".join(json.dumps(e) for e in events))
        return p

    def test_latest_decision_wins(self, tmp_path):
        p = self._events(tmp_path, [
            action_event("deny", "cluster:a", "steward", "u",
                         "wrong", "t0"),
            action_event("certify", "cluster:a", "steward", "u",
                         "", "t1"),
        ])
        d = effective_dispositions(p)
        assert d["cluster:a"]["state"] == "certified"
        assert d["cluster:a"]["grade"] == "steward-certified"

    def test_compare_lands_nowhere(self, tmp_path):
        p = self._events(tmp_path, [
            action_event("compare", "cluster:a", "steward", "u",
                         "", "t0")])
        assert effective_dispositions(p) == {}

    def test_inbox_serves_flags_with_console_state(self, tmp_path):
        p = self._events(tmp_path, [
            action_event("certify",
                         "cluster:misnomer:step:aaa111bbb222",
                         "steward", "u", "", "t0")])
        state = inbox_state(fake_kql, p, "steward")
        by_id = {f["id"]: f for f in state["flags"]}
        done = by_id["cluster:misnomer:step:aaa111bbb222"]
        assert done["console_state"]["state"] == "certified"
        # untouched flags sort FIRST (open work on top)
        assert state["flags"][0]["console_state"] is None
        assert "landing_map" in state


class TestConsole3CertifyOutcomes:
    """CONSOLE-3: certify has a TARGET and an OUTCOME — the three
    steward acts, each its own graded event with picked members in
    the decision; picker verbs refuse without their member."""

    def test_picker_verbs_require_a_member(self):
        for verb in ("certify_official", "certify_definition"):
            with pytest.raises(ConsoleRefusal) as e:
                check_action(verb, "steward")
            assert e.value.reason_class == "member_required"
            check_action(verb, "steward", member_ids=["m1"])

    def test_differentiate_all_needs_no_member(self):
        check_action("differentiate_all", "steward")

    def test_official_event_carries_the_picked_target(self):
        ev = action_event("certify_official", "cluster:f",
                          "steward", "u", "", "t0",
                          member_ids=["metric:reporting.USP_A"])
        assert ev["decision"]["targets"] == [
            "metric:reporting.USP_A"]
        assert "metric:reporting.USP_A" in ev["ids_read"]
        assert "canonical bearer" in ev["decision"]["lands"]

    def test_outcomes_fold_as_dispositions(self, tmp_path):
        p = tmp_path / "e.jsonl"
        p.write_text(json.dumps(action_event(
            "differentiate_all", "cluster:f", "steward", "u",
            "", "t0")))
        d = effective_dispositions(p)
        assert d["cluster:f"]["state"] == "differentiated"

    def test_member_never_becomes_the_fold_key(self, tmp_path):
        p = tmp_path / "e.jsonl"
        p.write_text(json.dumps(action_event(
            "certify_official", "cluster:f", "steward", "u",
            "", "t0", member_ids=["m1"])))
        d = effective_dispositions(p)
        assert "cluster:f" in d and "m1" not in d
