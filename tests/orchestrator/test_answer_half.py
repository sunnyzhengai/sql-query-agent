"""Tests for assemble, narrate, events, and the CLI loop (offline)."""

import json

import pytest

from src.orchestrator.assemble import (
    METRIC_FACTS_QUERY,
    NODE_FACTS_QUERY,
    AssemblyError,
    assemble,
)
from src.orchestrator.cli import chat_loop, render_candidates
from src.orchestrator.core import Candidate, resolve
from src.orchestrator.events import JsonlEventSink, PickEvent
from src.orchestrator.narrate import narrate
from src.schemas import USAGE_EVENTS

METRIC_ROW = {
    "metric_id": "reporting.USP_ED_Sepsis", "metric_name": "USP_ED_Sepsis",
    "business_name": "ED Sepsis Screening", "description": "Measures X.",
    "steward": None, "developer": None,
    "report_name": "ED Dashboard", "report_url": "https://r/1",
    "transform_count": 43, "source_tables": "A, B",
    "calculation_logic": "-- Base_Pop SELECT ...",
}
NODE_ROW = {
    "node_id": "transform:reporting.USP_ED_Sepsis:Base_Pop",
    "name": "Base_Pop", "description": "Distinct encounters.",
    "properties": json.dumps(
        {"metric_id": "reporting.USP_ED_Sepsis", "sql_fragment": "SELECT 1"}
    ),
}


def fake_kql(query, params):
    if query == METRIC_FACTS_QUERY:
        return [METRIC_ROW] if params["p_ref"] == METRIC_ROW["metric_id"] else []
    if query == NODE_FACTS_QUERY:
        return [NODE_ROW] if params["p_node_id"] == NODE_ROW["node_id"] else []
    raise AssertionError(f"unexpected query: {query}")


def cand(kind, node_id, ref):
    return Candidate(node_id=node_id, kind=kind, ref=ref, name="n",
                     business_name="", display_text="d", closeness=0.5,
                     total_matches=1)


class TestAssemble:
    def test_metric_fixed_lookup(self):
        fs = assemble(cand("metric", "canonical:reporting.USP_ED_Sepsis",
                           "reporting.USP_ED_Sepsis"), fake_kql)
        assert fs.facts["business_name"] == "ED Sepsis Screening"
        assert fs.basis == "output_metric_logic[metric_id='reporting.USP_ED_Sepsis'] -> 1 row"

    def test_step_joins_parent_metric(self):
        fs = assemble(cand("step", NODE_ROW["node_id"],
                           "reporting.USP_ED_Sepsis"), fake_kql)
        assert fs.facts["step_name"] == "Base_Pop"
        assert fs.facts["sql_fragment"] == "SELECT 1"
        assert fs.facts["parent_business_name"] == "ED Sepsis Screening"
        assert "graph_nodes" in fs.basis and "output_metric_logic" in fs.basis

    def test_missing_facts_raise_honestly(self):
        with pytest.raises(AssemblyError):
            assemble(cand("metric", "canonical:ghost", "ghost"), fake_kql)

    def test_unknown_kind_raises(self):
        with pytest.raises(AssemblyError):
            assemble(cand("term", "term:x", "x"), fake_kql)


class TestNarrate:
    def test_prose_plus_code_stamped_basis(self):
        fs = assemble(cand("metric", "canonical:reporting.USP_ED_Sepsis",
                           "reporting.USP_ED_Sepsis"), fake_kql)
        seen = {}
        def chat(system, user):
            seen.update(system=system, user=user)
            return "It measures X."
        out = narrate(fs, chat)
        assert out.startswith("It measures X.")
        assert out.endswith(f"Basis: {fs.basis}")       # stamped by code
        assert "ED Sepsis Screening" in seen["user"]     # facts in prompt
        assert "steward" not in seen["user"]             # nulls omitted
        assert "Never fabricate a link" in seen["system"]


class TestEvents:
    def test_jsonl_sink_appends_and_maps_to_contract(self, tmp_path):
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        ev = PickEvent(
            event_at="2026-08-09T00:00:00Z", user_id="u1", question="q?",
            token="q", candidates_shown=("a", "b"),
            picked_node_id="a", picked_ref="m.X", total_matches=2,
        )
        sink.record(ev)
        sink.record(ev)
        lines = (tmp_path / "e.jsonl").read_text().splitlines()
        assert len(lines) == 2
        row = ev.to_usage_event_row()
        assert set(row) == {c[0] for c in USAGE_EVENTS["columns"]}
        assert row["outcome"] == "answered" and row["metric_id"] == "m.X"

    def test_decline_maps_to_refused(self):
        ev = PickEvent(event_at="t", user_id="u", question="q", token="q",
                       candidates_shown=("a",), picked_node_id=None,
                       picked_ref=None, total_matches=1)
        assert ev.to_usage_event_row()["outcome"] == "refused"


class TestCliLoop:
    def scripted(self, inputs):
        it = iter(inputs)
        return lambda prompt="": next(it)

    def collect(self):
        out = []
        return out, lambda *a: out.append(" ".join(str(x) for x in a))

    def run_kql_for_loop(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            return [{
                "node_id": "canonical:reporting.USP_ED_Sepsis",
                "kind": "metric", "ref": "reporting.USP_ED_Sepsis",
                "name": "USP_ED_Sepsis", "business_name": "ED Sepsis Screening",
                "display_text": "ED Sepsis Screening (metric)",
                "closeness": 0.44, "total_matches": 1,
            }]
        return fake_kql(query, params)

    def test_full_loop_question_pick_answer_event(self, tmp_path):
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out, say = self.collect()
        chat = lambda s, u: ("ED sepsis screening" if "search phrase" in s
                             else "The metric measures X.")
        chat_loop(chat, self.run_kql_for_loop, sink,
                  ask=self.scripted(["how is ed screening done?", "1", "q"]),
                  say=say)
        text = "\n".join(out)
        assert "1. ED Sepsis Screening" in text        # candidate shown
        assert "The metric measures X." in text        # narrated answer
        assert "Basis:" in text                        # stamped provenance
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        assert events[0]["picked_ref"] == "reporting.USP_ED_Sepsis"

    def test_refusal_and_decline_both_record(self, tmp_path):
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out, say = self.collect()
        def run_kql(query, params):
            from src.orchestrator.core import RESOLVE_QUERY
            assert query == RESOLVE_QUERY
            return []
        chat_loop(lambda s, u: "unicorn velocity", run_kql, sink,
                  ask=self.scripted(["unicorns?", "q"]), say=say)
        text = "\n".join(out)
        assert "Nothing in the certified knowledge base" in text
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        assert events[0]["picked_node_id"] is None

    def test_single_candidate_still_requires_pick(self, tmp_path):
        # no bypass: 1 candidate is presented exactly like 10
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out, say = self.collect()
        chat = lambda s, u: ("token" if "search phrase" in s else "Prose.")
        chat_loop(chat, self.run_kql_for_loop, sink,
                  ask=self.scripted(["q?", "1", "q"]), say=say)
        assert "Pick a number" in "\n".join(out)


class TestRendering:
    def test_weak_matches_labeled_closeness_visible(self):
        rows = [{
            "node_id": "a", "kind": "step", "ref": "r", "name": "N",
            "business_name": "", "display_text": "d",
            "closeness": 0.36, "total_matches": 12,
        }]
        result = resolve("t", lambda q, p: rows)
        text = render_candidates(result)
        assert "closeness 0.36" in text and "(weak match)" in text
        assert "Found 12 related item(s); showing 1" in text


class TestCompareFlow:
    """'Compare X and Y': two tokens -> two pick rounds -> one comparison."""

    def run_kql(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            token = params["token"]
            row = {
                "node_id": f"canonical:m.{token}", "kind": "metric",
                "ref": "reporting.USP_ED_Sepsis",
                "name": f"USP_{token}", "business_name": token.title(),
                "display_text": f"{token} (metric)",
                "closeness": 0.5, "total_matches": 1,
            }
            return [row]
        return fake_kql(query, params)

    def test_two_tokens_two_picks_one_comparison(self, tmp_path):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        def chat(system, user):
            if "search phrase" in system:
                return "alpha\nbeta"           # entry edge splits into 2
            return "Alpha does X; Beta does Y."  # exit edge compares
        it = iter(["compare alpha and beta", "1", "1", "q"])
        chat_loop(chat, self.run_kql, sink, ask=lambda p="": next(it), say=say)
        text = "\n".join(out)
        assert "For 'alpha':" in text and "For 'beta':" in text
        assert "Alpha does X; Beta does Y." in text
        assert text.count("output_metric_logic[metric_id=") >= 1  # stamped basis
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        assert len(events) == 2                  # one pick event per concept
