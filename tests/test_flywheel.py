"""FLYWHEEL-1 (0056 mechanism v1, Sunny-authorized 2026-08-29):
captured decision events → per-item usage weights; cards disclose
with provenance; the Ground-Truth Shelf serves my definitions /
reports / questions with replay.

Proves: contract:suite-legibility
"""

import json

from src.flywheel import my_shelf, provenance_line, usage_weights


def _write_events(tmp_path, events):
    p = tmp_path / "events.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events))
    return p


def _ev(question, ids, user="u1", answered=True):
    return {"question": question, "ids_read": ids, "user_id": user,
            "answered": answered}


class TestUsageWeights:
    def test_four_decision_classes_count(self, tmp_path):
        p = _write_events(tmp_path, [
            _ev("[PLANNER] are they the same?", ["m1", "m2"]),
            _ev("[PLANNER] again", ["m1"]),
            _ev("[RUN] transform:m1:S", ["transform:m1:S"]),
            _ev("[PRUNE] are they the same?", ["m3"]),
            _ev("[ESCALATE] weird one", ["m4"]),
            _ev("plain engine turn", ["m1"]),
        ])
        w = usage_weights(p)
        assert w["m1"] == {"confirmed": 2, "run": 0, "pruned": 0,
                           "escalated": 0, "read": 1}
        assert w["transform:m1:S"]["run"] == 1
        assert w["m3"]["pruned"] == 1
        assert w["m4"]["escalated"] == 1

    def test_unanswered_non_decision_turns_count_nothing(self, tmp_path):
        p = _write_events(tmp_path, [
            _ev("engine turn that failed", ["m1"], answered=False)])
        assert usage_weights(p) == {}

    def test_missing_store_is_empty_never_a_crash(self, tmp_path):
        assert usage_weights(tmp_path / "nope.jsonl") == {}


class TestProvenanceLine:
    def test_discloses_counts_and_the_no_official_truth(self):
        line = provenance_line({"confirmed": 3, "run": 1,
                                "pruned": 0, "escalated": 0,
                                "read": 5})
        assert line == ("confirmed 3× · run 1× — no official "
                        "designated")

    def test_zero_usage_stays_silent(self):
        assert provenance_line(None) == ""
        assert provenance_line({"confirmed": 0, "run": 0,
                                "pruned": 0, "escalated": 0,
                                "read": 0}) == ""


class TestGroundTruthShelf:
    def test_shelf_sections_and_replay_questions(self, tmp_path):
        p = _write_events(tmp_path, [
            _ev("[PLANNER] are the codesets the same?",
                ["m1", "report:dash1"]),
            _ev("[RUN] transform:m1:S", ["transform:m1:S"]),
            _ev("what tables does m1 use", ["m1"]),
        ])
        shelf = my_shelf(p, "u1")
        def_ids = [d["id"] for d in shelf["definitions"]]
        assert "m1" in def_ids and "report:dash1" not in def_ids
        assert [r["id"] for r in shelf["reports"]] == ["report:dash1"]
        assert "are the codesets the same?" in shelf["questions"]
        assert "what tables does m1 use" in shelf["questions"]
        # the marker prefix never leaks into a replay question
        assert not any(q.startswith("[") for q in shelf["questions"])

    def test_single_user_isolation(self, tmp_path):
        p = _write_events(tmp_path, [
            _ev("[PLANNER] q", ["m1"], user="alice"),
            _ev("[PLANNER] q2", ["m2"], user="bob")])
        shelf = my_shelf(p, "alice")
        assert [d["id"] for d in shelf["definitions"]] == ["m1"]
        assert shelf["questions"] == ["q"]
