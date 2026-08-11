"""Tests for decision telemetry (Sunny, 2026-08-11): every turn records
WHO made its load-bearing decisions, so no-solution feedback patterns
attribute to the deterministic layer or the LLM."""

from src.orchestrator.events import decision_shape


def call(tool, result=None, args=None):
    return {"tool": tool, "args": args or {}, "result": result or {"ok": 1}}


class TestDecisionShape:
    def test_verified_by_tool(self):
        d = decision_shape(
            [call("find_by_name"), call("check_same_logic")],
            "No — the logic is not the same; 2 distinct definitions.")
        assert d["verified_by_tool"] is True
        assert d["unverified_sameness_language"] is False

    def test_llm_assembled_comparison_is_flagged(self):
        # two fact reads, no verify call, sameness language in the
        # answer: the LLM decided in its head — the highest-risk shape
        d = decision_shape(
            [call("get_facts"), call("get_facts")],
            "They share the same source tables and look identical.")
        assert d["llm_assembled"] is True
        assert d["unverified_sameness_language"] is True
        assert d["verified_by_tool"] is False

    def test_small_fact_assembly_without_sameness_claims(self):
        d = decision_shape(
            [call("get_facts"), call("get_facts")],
            "Metric A is stewarded by Pat; Metric B lists no steward.")
        assert d["llm_assembled"] is True
        assert d["unverified_sameness_language"] is False

    def test_refusals_and_smalltalk(self):
        d = decision_shape([], "I cannot provide patient counts.")
        assert d["no_tools"] is True and d["search_only"] is False
        d2 = decision_shape([call("search_catalog")],
                            "Several metrics relate to sepsis: ...")
        assert d2["search_only"] is True

    def test_tool_errors_counted(self):
        d = decision_shape(
            [call("get_facts", result={"error": "not surfaced"}),
             call("search_catalog"), call("get_facts")],
            "Here are the facts.")
        assert d["tool_errors"] == 1
